package protocol

import (
	"context"
	"encoding/base64"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/httvps/httvps/gateway/internal/auth"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/nodes"
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

type mockNodesClient struct {
	resp    nodes.AssignOutlineResponse
	err     error
	lastReq nodes.AssignOutlineRequest
}

func (m *mockNodesClient) AssignOutlineNode(ctx context.Context, req nodes.AssignOutlineRequest) (nodes.AssignOutlineResponse, error) {
	m.lastReq = req
	return m.resp, m.err
}

type mockUpstream struct {
	bindCalls []upstream.OutlineNodeConfig
}

func (m *mockUpstream) BindSession(ctx context.Context, sessionID string, node upstream.OutlineNodeConfig) error {
	m.bindCalls = append(m.bindCalls, node)
	return nil
}

func (m *mockUpstream) OpenStream(ctx context.Context, sessionID string, streamID string) error {
	return nil
}

func (m *mockUpstream) Write(ctx context.Context, sessionID string, streamID string, data []byte) ([]byte, error) {
	return nil, nil
}

func (m *mockUpstream) CloseStream(ctx context.Context, sessionID string, streamID string) error {
	return nil
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

func TestHandlerOutlineAssignSuccess(t *testing.T) {
	mockNodes := &mockNodesClient{resp: nodes.AssignOutlineResponse{NodeID: 10, Host: "host", Port: 1234, Method: "aes-256-gcm", Password: "pwd", Region: "us"}}
	mockUp := &mockUpstream{}
	handler := &Handler{AuthClient: &mockAuthClient{result: auth.ValidateDeviceResult{Allowed: true}}, NodesClient: mockNodes, Sessions: sessions.NewManager(4), Upstream: mockUp, Metrics: metrics.New(false, ""), Logger: newTestLogger(), UpstreamMode: "outline"}
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
	hello := HelloFrame{Type: FrameHello, DeviceID: "dev1", Token: "tok", Region: "us"}
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
	if len(mockUp.bindCalls) != 1 {
		t.Fatalf("expected bind call")
	}
	if mockUp.bindCalls[0].NodeID != 10 || mockUp.bindCalls[0].Region != "us" {
		t.Fatalf("unexpected bind config: %+v", mockUp.bindCalls[0])
	}
	if mockNodes.lastReq.RegionCode != "us" || mockNodes.lastReq.DeviceID != "dev1" {
		t.Fatalf("unexpected assign request: %+v", mockNodes.lastReq)
	}
}

func TestHandlerOutlineAssignFailure(t *testing.T) {
	handler := &Handler{AuthClient: &mockAuthClient{result: auth.ValidateDeviceResult{Allowed: true}}, NodesClient: &mockNodesClient{err: errors.New("no_nodes")}, Sessions: sessions.NewManager(4), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger(), UpstreamMode: "outline"}
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
	var errFrame ErrorFrame
	if err := conn.ReadJSON(&errFrame); err != nil {
		t.Fatalf("read error: %v", err)
	}
	if errFrame.Code != "outline_unavailable" {
		t.Fatalf("unexpected error frame: %+v", errFrame)
	}
	if handler.Sessions.ActiveSessions() != 0 {
		t.Fatalf("session should not be created")
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
