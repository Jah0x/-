package main

import (
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

type sessionRequest struct {
	DeviceID string `json:"device_id"`
	Token    string `json:"token"`
	Region   string `json:"region,omitempty"`
}

type sessionResponse struct {
	SessionToken string    `json:"session_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	GatewayURL   string    `json:"gateway_url"`
	MaxStreams   int       `json:"max_streams"`
}

type envelope struct {
	Type string `json:"type"`
}

type helloFrame struct {
	Type         string `json:"type"`
	SessionToken string `json:"session_token"`
	Version      string `json:"version"`
	Client       string `json:"client,omitempty"`
}

type readyFrame struct {
	Type       string `json:"type"`
	SessionID  string `json:"session_id"`
	MaxStreams int    `json:"max_streams"`
}

type errorFrame struct {
	Type    string `json:"type"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

type streamOpenFrame struct {
	Type     string `json:"type"`
	StreamID string `json:"stream_id"`
	Target   string `json:"target,omitempty"`
}

type streamDataFrame struct {
	Type     string `json:"type"`
	StreamID string `json:"stream_id"`
	Data     string `json:"data"`
}

type streamCloseFrame struct {
	Type     string `json:"type"`
	StreamID string `json:"stream_id"`
	Reason   string `json:"reason,omitempty"`
}

func main() {
	backendURL := flag.String("backend", "http://localhost:8000", "Backend base URL")
	gatewayOverride := flag.String("gateway", "", "Override gateway URL")
	deviceID := flag.String("device", "", "Device identifier")
	token := flag.String("token", "", "Device token")
	region := flag.String("region", "", "Region code")
	target := flag.String("target", "example.com:80", "Target host:port")
	insecure := flag.Bool("insecure", true, "Skip TLS verification")
	version := flag.String("version", "1", "Protocol version")
	flag.Parse()
	if *deviceID == "" || *token == "" {
		fmt.Println("device and token are required")
		os.Exit(1)
	}
	descriptor, err := requestSession(*backendURL, *deviceID, *token, *region)
	if err != nil {
		fmt.Printf("session request failed: %v\n", err)
		os.Exit(1)
	}
	gatewayURL := descriptor.GatewayURL
	if *gatewayOverride != "" {
		gatewayURL = *gatewayOverride
	}
	conn, err := dialGateway(gatewayURL, *version, descriptor.SessionToken, *insecure)
	if err != nil {
		fmt.Printf("gateway dial failed: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()
	if err := performStream(conn, *target); err != nil {
		fmt.Printf("stream error: %v\n", err)
		os.Exit(1)
	}
}

func requestSession(baseURL string, deviceID string, token string, region string) (sessionResponse, error) {
	var result sessionResponse
	body, err := json.Marshal(sessionRequest{DeviceID: deviceID, Token: token, Region: region})
	if err != nil {
		return result, err
	}
	endpoint, err := url.JoinPath(baseURL, "/api/v1/httvps/session")
	if err != nil {
		return result, err
	}
	resp, err := http.Post(endpoint, "application/json", strings.NewReader(string(body)))
	if err != nil {
		return result, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, err
	}
	if resp.StatusCode != http.StatusOK {
		return result, fmt.Errorf("backend responded with %s: %s", resp.Status, string(data))
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return result, err
	}
	return result, nil
}

func dialGateway(gatewayURL string, version string, sessionToken string, insecure bool) (*websocket.Conn, error) {
	dialer := websocket.Dialer{TLSClientConfig: &tls.Config{InsecureSkipVerify: insecure}}
	conn, _, err := dialer.Dial(gatewayURL, nil)
	if err != nil {
		return nil, err
	}
	hello := helloFrame{Type: "hello", SessionToken: sessionToken, Version: version, Client: "httvps-cli"}
	if err := conn.WriteJSON(hello); err != nil {
		return nil, err
	}
	_, data, err := conn.ReadMessage()
	if err != nil {
		return nil, err
	}
	var env envelope
	if err := json.Unmarshal(data, &env); err != nil {
		return nil, err
	}
	if env.Type == "error" {
		var frame errorFrame
		_ = json.Unmarshal(data, &frame)
		return nil, fmt.Errorf("handshake failed: %s", frame.Code)
	}
	if env.Type != "ready" {
		return nil, fmt.Errorf("unexpected handshake response: %s", env.Type)
	}
	return conn, nil
}

func performStream(conn *websocket.Conn, target string) error {
	streamID := "cli-1"
	open := streamOpenFrame{Type: "stream_open", StreamID: streamID, Target: target}
	if err := conn.WriteJSON(open); err != nil {
		return err
	}
	payload, err := buildPayload(target)
	if err != nil {
		return err
	}
	dataFrame := streamDataFrame{Type: "stream_data", StreamID: streamID, Data: base64.StdEncoding.EncodeToString(payload)}
	if err := conn.WriteJSON(dataFrame); err != nil {
		return err
	}
	for {
		_, raw, err := conn.ReadMessage()
		if err != nil {
			return err
		}
		var env envelope
		if err := json.Unmarshal(raw, &env); err != nil {
			return err
		}
		switch env.Type {
		case "stream_data":
			var data streamDataFrame
			if err := json.Unmarshal(raw, &data); err != nil {
				return err
			}
			decoded, err := base64.StdEncoding.DecodeString(data.Data)
			if err != nil {
				return err
			}
			os.Stdout.Write(decoded)
			closeFrame := streamCloseFrame{Type: "stream_close", StreamID: streamID, Reason: "done"}
			_ = conn.WriteJSON(closeFrame)
			return nil
		case "error":
			var errFrame errorFrame
			if err := json.Unmarshal(raw, &errFrame); err != nil {
				return err
			}
			return fmt.Errorf("stream error: %s", errFrame.Code)
		}
	}
}

func buildPayload(target string) ([]byte, error) {
	parts := strings.Split(target, ":")
	if len(parts) != 2 {
		return nil, fmt.Errorf("target must be host:port")
	}
	host := parts[0]
	portValue, err := strconv.Atoi(parts[1])
	if err != nil {
		return nil, err
	}
	header := []byte{0x03, byte(len(host))}
	header = append(header, []byte(host)...)
	header = append(header, byte(portValue>>8), byte(portValue))
	request := fmt.Sprintf("GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n", host)
	return append(header, []byte(request)...), nil
}
