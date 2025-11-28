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
	"github.com/httvps/httvps/gateway/internal/httvps"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/sessions"
	"github.com/httvps/httvps/gateway/internal/upstream"
	"golang.org/x/exp/slog"
)

type mockValidator struct {
	resp httvps.ValidateSessionResponse
	err  error
}

func (m *mockValidator) ValidateSession(ctx context.Context, token string) (httvps.ValidateSessionResponse, error) {
	return m.resp, m.err
}

func newTestLogger() *slog.Logger {
	return slog.New(slog.NewJSONHandler(io.Discard, nil))
}

func TestHandlerHelloSuccess(t *testing.T) {
	validator := &mockValidator{resp: httvps.ValidateSessionResponse{SessionID: "sess-1", DeviceID: "dev1", MaxStreams: 4, Outline: httvps.OutlineDescriptor{NodeID: 1}}}
	handler := &Handler{Validator: validator, Sessions: sessions.NewManager(4), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger(), Version: "1"}
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
	hello := HelloFrame{Type: FrameHello, SessionToken: "tok", Version: "1"}
	if err := conn.WriteJSON(hello); err != nil {
		t.Fatalf("write hello: %v", err)
	}
	var ready ReadyFrame
	if err := conn.ReadJSON(&ready); err != nil {
		t.Fatalf("read ready: %v", err)
	}
	if ready.SessionID != "sess-1" || ready.MaxStreams != 4 {
		t.Fatalf("unexpected ready frame: %+v", ready)
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

func TestHandlerAuthFailure(t *testing.T) {
	validator := &mockValidator{err: io.ErrUnexpectedEOF}
	handler := &Handler{Validator: validator, Sessions: sessions.NewManager(4), Upstream: upstream.NewFakeUpstream(true), Metrics: metrics.New(false, ""), Logger: newTestLogger(), Version: "1"}
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
	hello := HelloFrame{Type: FrameHello, SessionToken: "tok", Version: "1"}
	if err := conn.WriteJSON(hello); err != nil {
		t.Fatalf("write hello: %v", err)
	}
	var errFrame ErrorFrame
	if err := conn.ReadJSON(&errFrame); err != nil {
		t.Fatalf("read error: %v", err)
	}
	if errFrame.Code != "auth_failed" {
		t.Fatalf("unexpected code: %+v", errFrame)
	}
}
