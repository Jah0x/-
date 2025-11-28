package protocol

import (
	"context"
	"encoding/base64"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/httvps/httvps/gateway/internal/auth"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/sessions"
	"github.com/httvps/httvps/gateway/internal/upstream"
	"golang.org/x/exp/slog"
)

type mockAuthClient struct {
	result auth.ValidateDeviceResult
	err    error
}

func (m *mockAuthClient) ValidateDevice(ctx context.Context, req auth.ValidateDeviceRequest) (auth.ValidateDeviceResult, error) {
	return m.result, m.err
}

func newTestLogger() *slog.Logger {
	return slog.New(slog.NewJSONHandler(io.Discard, nil))
}

func TestHandlerHelloSuccess(t *testing.T) {
	handler := &Handler{AuthClient: &mockAuthClient{result: auth.ValidateDeviceResult{Allowed: true, SubscriptionStatus: "active"}}, Sessions: sessions.NewManager(4), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger()}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		upgrader := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			t.Fatalf("upgrade error: %v", err)
		}
		handler.Handle(context.Background(), conn)
	}))
	defer server.Close()
	url := "ws" + server.URL[len("http"):]
	conn, _, err := websocket.DefaultDialer.Dial(url+"/ws", nil)
	if err != nil {
		t.Fatalf("dial error: %v", err)
	}
	defer conn.Close()
	hello := HelloFrame{Type: FrameHello, DeviceID: "dev1", Token: "tok", ClientVersion: "1.0"}
	if err := conn.WriteJSON(hello); err != nil {
		t.Fatalf("write hello: %v", err)
	}
	var authResp AuthResultFrame
	if err := conn.ReadJSON(&authResp); err != nil {
		t.Fatalf("read auth: %v", err)
	}
	if !authResp.Allowed || authResp.SessionID == "" {
		t.Fatalf("unexpected auth response: %+v", authResp)
	}
	openFrame := StreamOpenFrame{Type: FrameStreamOpen, StreamID: "s1"}
	if err := conn.WriteJSON(openFrame); err != nil {
		t.Fatalf("write open: %v", err)
	}
	data := base64.StdEncoding.EncodeToString([]byte("hello"))
	dataFrame := StreamDataFrame{Type: FrameStreamData, StreamID: "s1", Data: data}
	if err := conn.WriteJSON(dataFrame); err != nil {
		t.Fatalf("write data: %v", err)
	}
	var echo StreamDataFrame
	if err := conn.ReadJSON(&echo); err != nil {
		t.Fatalf("read echo: %v", err)
	}
	if echo.Data != data {
		t.Fatalf("unexpected echo: %+v", echo)
	}
	conn.Close()
	time.Sleep(50 * time.Millisecond)
	if handler.Sessions.ActiveSessions() != 0 {
		t.Fatalf("session not cleaned")
	}
}

func TestHandlerAuthReject(t *testing.T) {
	handler := &Handler{AuthClient: &mockAuthClient{result: auth.ValidateDeviceResult{Allowed: false, Reason: "invalid"}}, Sessions: sessions.NewManager(4), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger()}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		upgrader := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			t.Fatalf("upgrade error: %v", err)
		}
		handler.Handle(context.Background(), conn)
	}))
	defer server.Close()
	url := "ws" + server.URL[len("http"):]
	conn, _, err := websocket.DefaultDialer.Dial(url+"/ws", nil)
	if err != nil {
		t.Fatalf("dial error: %v", err)
	}
	defer conn.Close()
	hello := HelloFrame{Type: FrameHello, DeviceID: "dev1", Token: "tok"}
	if err := conn.WriteJSON(hello); err != nil {
		t.Fatalf("write hello: %v", err)
	}
	var authResp AuthResultFrame
	if err := conn.ReadJSON(&authResp); err != nil {
		t.Fatalf("read auth: %v", err)
	}
	if authResp.Allowed {
		t.Fatalf("expected rejection")
	}
	if handler.Sessions.ActiveSessions() != 0 {
		t.Fatalf("session should not be created")
	}
}

func TestHandlerSessionClosedOnDisconnect(t *testing.T) {
	handler := &Handler{AuthClient: &mockAuthClient{result: auth.ValidateDeviceResult{Allowed: true}}, Sessions: sessions.NewManager(2), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger()}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		upgrader := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			t.Fatalf("upgrade error: %v", err)
		}
		handler.Handle(context.Background(), conn)
	}))
	defer server.Close()
	url := "ws" + server.URL[len("http"):]
	conn, _, err := websocket.DefaultDialer.Dial(url+"/ws", nil)
	if err != nil {
		t.Fatalf("dial error: %v", err)
	}
	hello := HelloFrame{Type: FrameHello, DeviceID: "dev1", Token: "tok"}
	if err := conn.WriteJSON(hello); err != nil {
		t.Fatalf("write hello: %v", err)
	}
	var authResp AuthResultFrame
	if err := conn.ReadJSON(&authResp); err != nil {
		t.Fatalf("read auth: %v", err)
	}
	if !authResp.Allowed {
		t.Fatalf("expected allowed")
	}
	conn.Close()
	time.Sleep(50 * time.Millisecond)
	if handler.Sessions.ActiveSessions() != 0 {
		t.Fatalf("session not cleaned after disconnect")
	}
}
