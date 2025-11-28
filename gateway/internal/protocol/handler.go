package protocol

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"time"

	"github.com/gorilla/websocket"
	"github.com/httvps/httvps/gateway/internal/auth"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/sessions"
	"github.com/httvps/httvps/gateway/internal/upstream"
	"golang.org/x/exp/slog"
)

type AuthClient interface {
	ValidateDevice(ctx context.Context, req auth.ValidateDeviceRequest) (auth.ValidateDeviceResult, error)
}

type Handler struct {
	AuthClient AuthClient
	Sessions   *sessions.Manager
	Upstream   upstream.Upstream
	Metrics    *metrics.Metrics
	Logger     *slog.Logger
}

func (h *Handler) Handle(ctx context.Context, conn *websocket.Conn) {
	var session *sessions.Session
	handshakeStart := time.Now()
	defer func() {
		if session != nil {
			for streamID := range session.Streams {
				h.Upstream.CloseStream(context.Background(), session.ID, streamID)
			}
			h.Sessions.CloseSession(session.ID)
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveSessions.Set(float64(h.Sessions.ActiveSessions()))
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
			}
		}
		conn.Close()
	}()
	helloData, err := h.readMessage(conn)
	if err != nil {
		return
	}
	var env Envelope
	if err := json.Unmarshal(helloData, &env); err != nil || env.Type != FrameHello {
		h.sendError(conn, "bad_hello", "invalid hello")
		return
	}
	var hello HelloFrame
	if err := json.Unmarshal(helloData, &hello); err != nil {
		h.sendError(conn, "bad_hello", "invalid hello")
		return
	}
	authResult, authErr := h.AuthClient.ValidateDevice(ctx, auth.ValidateDeviceRequest{DeviceID: hello.DeviceID, Token: hello.Token})
	duration := time.Since(handshakeStart).Seconds()
	if h.Metrics != nil && h.Metrics.MetricsEnabled {
		h.Metrics.HandshakeDuration.Observe(duration)
	}
	if authErr != nil {
		if h.Metrics != nil && h.Metrics.MetricsEnabled {
			h.Metrics.HandshakeTotal.WithLabelValues("error").Inc()
			h.Metrics.BackendErrors.WithLabelValues("auth_error").Inc()
		}
		h.sendAuthResult(conn, AuthResultFrame{Type: FrameAuthResult, Allowed: false, Reason: authErr.Error()})
		return
	}
	if !authResult.Allowed {
		if h.Metrics != nil && h.Metrics.MetricsEnabled {
			h.Metrics.HandshakeTotal.WithLabelValues("rejected").Inc()
		}
		h.sendAuthResult(conn, AuthResultFrame{Type: FrameAuthResult, Allowed: false, Reason: authResult.Reason, SubscriptionStatus: authResult.SubscriptionStatus})
		return
	}
	if h.Metrics != nil && h.Metrics.MetricsEnabled {
		h.Metrics.HandshakeTotal.WithLabelValues("accepted").Inc()
	}
	session, err = h.Sessions.CreateSession(hello.DeviceID)
	if err != nil {
		h.sendError(conn, "session_error", "failed to create session")
		return
	}
	if h.Metrics != nil && h.Metrics.MetricsEnabled {
		h.Metrics.ActiveSessions.Set(float64(h.Sessions.ActiveSessions()))
	}
	if h.Logger != nil {
		h.Logger.Info("session_started", slog.String("device_id", hello.DeviceID), slog.String("session_id", session.ID))
	}
	h.sendAuthResult(conn, AuthResultFrame{Type: FrameAuthResult, Allowed: true, SessionID: session.ID, SubscriptionStatus: authResult.SubscriptionStatus})
	for {
		data, err := h.readMessage(conn)
		if err != nil {
			return
		}
		var envelope Envelope
		if err := json.Unmarshal(data, &envelope); err != nil {
			h.sendError(conn, "bad_frame", "invalid frame")
			continue
		}
		switch envelope.Type {
		case FrameStreamOpen:
			var frame StreamOpenFrame
			if err := json.Unmarshal(data, &frame); err != nil || frame.StreamID == "" {
				h.sendError(conn, "bad_stream", "invalid stream_open")
				continue
			}
			if err := h.Sessions.OpenStream(session.ID, frame.StreamID); err != nil {
				h.sendError(conn, "stream_error", err.Error())
				continue
			}
			if err := h.Upstream.OpenStream(ctx, session.ID, frame.StreamID); err != nil {
				h.sendError(conn, "stream_error", err.Error())
				continue
			}
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
			}
		case FrameStreamData:
			var frame StreamDataFrame
			if err := json.Unmarshal(data, &frame); err != nil || frame.StreamID == "" {
				h.sendError(conn, "bad_stream", "invalid stream_data")
				continue
			}
			payload, err := base64.StdEncoding.DecodeString(frame.Data)
			if err != nil {
				h.sendError(conn, "bad_stream", "invalid data encoding")
				continue
			}
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.BytesIn.Add(float64(len(payload)))
			}
			response, err := h.Upstream.Write(ctx, session.ID, frame.StreamID, payload)
			if err != nil {
				h.sendError(conn, "stream_error", err.Error())
				continue
			}
			if len(response) > 0 {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.BytesOut.Add(float64(len(response)))
				}
				h.sendFrame(conn, StreamDataFrame{Type: FrameStreamData, StreamID: frame.StreamID, Data: base64.StdEncoding.EncodeToString(response)})
			}
		case FrameStreamClose:
			var frame StreamCloseFrame
			if err := json.Unmarshal(data, &frame); err != nil || frame.StreamID == "" {
				h.sendError(conn, "bad_stream", "invalid stream_close")
				continue
			}
			h.Upstream.CloseStream(ctx, session.ID, frame.StreamID)
			h.Sessions.CloseStream(session.ID, frame.StreamID)
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
			}
		case FramePing:
			h.sendFrame(conn, Envelope{Type: FramePong})
		default:
			h.sendError(conn, "unsupported", "unsupported frame type")
		}
	}
}

func (h *Handler) readMessage(conn *websocket.Conn) ([]byte, error) {
	_, data, err := conn.ReadMessage()
	if err != nil {
		return nil, err
	}
	return data, nil
}

func (h *Handler) sendFrame(conn *websocket.Conn, frame any) {
	conn.WriteJSON(frame)
}

func (h *Handler) sendError(conn *websocket.Conn, code string, message string) {
	h.sendFrame(conn, ErrorFrame{Type: FrameError, Code: code, Message: message})
}

func (h *Handler) sendAuthResult(conn *websocket.Conn, frame AuthResultFrame) {
	h.sendFrame(conn, frame)
}
