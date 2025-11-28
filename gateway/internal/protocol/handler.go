package protocol

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"time"

	"github.com/gorilla/websocket"
	"github.com/httvps/httvps/gateway/internal/httvps"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/sessions"
	"github.com/httvps/httvps/gateway/internal/upstream"
	"golang.org/x/exp/slog"
)

type SessionValidator interface {
	ValidateSession(ctx context.Context, token string) (httvps.ValidateSessionResponse, error)
}

type Handler struct {
	Validator SessionValidator
	Sessions  *sessions.Manager
	Upstream  upstream.Upstream
	Metrics   *metrics.Metrics
	Logger    *slog.Logger
	Version   string
}

func (h *Handler) Handle(ctx context.Context, conn *websocket.Conn) {
	var session *sessions.Session
	handshakeStart := time.Now()
	sessionStart := time.Time{}
	handshakeResult := "transport_error"
	defer func() {
		if session != nil {
			for streamID := range session.Streams {
				h.Upstream.CloseStream(context.Background(), session.ID, streamID)
			}
			h.Sessions.CloseSession(session.ID)
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveSessions.Set(float64(h.Sessions.ActiveSessions()))
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
				if !sessionStart.IsZero() {
					h.Metrics.SessionDuration.Observe(time.Since(sessionStart).Seconds())
				}
			}
		}
		if h.Metrics != nil && h.Metrics.MetricsEnabled {
			h.Metrics.HandshakeDuration.Observe(time.Since(handshakeStart).Seconds())
			h.Metrics.HandshakeTotal.WithLabelValues(handshakeResult).Inc()
			h.Metrics.ConnectionsTotal.WithLabelValues(handshakeResult).Inc()
		}
		conn.Close()
	}()
	helloData, err := h.readMessage(conn)
	if err != nil {
		return
	}
	var env Envelope
	if err := json.Unmarshal(helloData, &env); err != nil || env.Type != FrameHello {
		handshakeResult = "bad_hello"
		h.sendError(conn, "bad_hello", "invalid hello")
		return
	}
	var hello HelloFrame
	if err := json.Unmarshal(helloData, &hello); err != nil {
		handshakeResult = "bad_hello"
		h.sendError(conn, "bad_hello", "invalid hello")
		return
	}
	if hello.Version == "" {
		handshakeResult = "bad_hello"
		h.sendError(conn, "bad_hello", "missing version")
		return
	}
	if h.Version != "" && hello.Version != h.Version {
		handshakeResult = "bad_version"
		h.sendError(conn, "bad_version", "unsupported version")
		return
	}
	validation, authErr := h.Validator.ValidateSession(ctx, hello.SessionToken)
	if authErr != nil {
		if h.Metrics != nil && h.Metrics.MetricsEnabled {
			h.Metrics.BackendErrors.WithLabelValues("auth_error").Inc()
		}
		handshakeResult = "auth_error"
		h.sendError(conn, "auth_failed", authErr.Error())
		return
	}
	session, err = h.Sessions.CreateSessionWithID(validation.SessionID, validation.DeviceID, validation.MaxStreams)
	if err != nil {
		handshakeResult = "session_error"
		h.sendError(conn, "session_error", "failed to create session")
		return
	}
	sessionStart = time.Now()
	defer h.Upstream.UnbindSession(ctx, session.ID)
	nodeConfig := upstream.OutlineNodeConfig{NodeID: validation.Outline.NodeID, Host: validation.Outline.Host, Port: validation.Outline.Port, Method: validation.Outline.Method, Password: validation.Outline.Password, Region: validation.Outline.Region, Pool: validation.Outline.Pool, AccessKeyID: validation.Outline.AccessKeyID, AccessURL: validation.Outline.AccessURL}
	if err := h.Upstream.BindSession(ctx, session.ID, nodeConfig); err != nil {
		handshakeResult = "upstream_error"
		if h.Metrics != nil && h.Metrics.MetricsEnabled {
			h.Metrics.UpstreamErrors.WithLabelValues("bind").Inc()
		}
		h.sendError(conn, "session_error", "failed to bind upstream")
		return
	}
	if h.Metrics != nil && h.Metrics.MetricsEnabled {
		h.Metrics.ActiveSessions.Set(float64(h.Sessions.ActiveSessions()))
	}
	handshakeResult = "accepted"
	if h.Logger != nil {
		h.Logger.Info("session_started", slog.String("device_id", session.DeviceID), slog.String("session_id", session.ID), slog.String("region", nodeConfig.Region), slog.Int("node_id", nodeConfig.NodeID))
	}
	h.sendFrame(conn, ReadyFrame{Type: FrameReady, SessionID: session.ID, MaxStreams: session.MaxStreams})
	for {
		data, err := h.readMessage(conn)
		if err != nil {
			return
		}
		var envelope Envelope
		if err := json.Unmarshal(data, &envelope); err != nil {
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.StreamErrors.WithLabelValues("bad_envelope").Inc()
				h.Metrics.ConnectionsTotal.WithLabelValues("protocol_error").Inc()
			}
			h.sendError(conn, "bad_frame", "invalid frame")
			continue
		}
		switch envelope.Type {
		case FrameStreamOpen:
			var frame StreamOpenFrame
			if err := json.Unmarshal(data, &frame); err != nil || frame.StreamID == "" {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.StreamErrors.WithLabelValues("bad_stream_open").Inc()
				}
				h.sendError(conn, "bad_stream", "invalid stream_open")
				continue
			}
			if err := h.Sessions.OpenStream(session.ID, frame.StreamID); err != nil {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.StreamOpenTotal.WithLabelValues("limit_exceeded").Inc()
				}
				h.sendError(conn, "stream_error", err.Error())
				continue
			}
			if err := h.Upstream.OpenStream(ctx, session.ID, frame.StreamID); err != nil {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.UpstreamErrors.WithLabelValues("open_stream").Inc()
					h.Metrics.StreamOpenTotal.WithLabelValues("upstream_error").Inc()
				}
				h.sendError(conn, "stream_error", err.Error())
				continue
			}
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
				h.Metrics.StreamOpenTotal.WithLabelValues("opened").Inc()
			}
		case FrameStreamData:
			var frame StreamDataFrame
			if err := json.Unmarshal(data, &frame); err != nil || frame.StreamID == "" {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.StreamErrors.WithLabelValues("bad_stream_data").Inc()
				}
				h.sendError(conn, "bad_stream", "invalid stream_data")
				continue
			}
			payload, err := base64.StdEncoding.DecodeString(frame.Data)
			if err != nil {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.StreamErrors.WithLabelValues("decode_error").Inc()
				}
				h.sendError(conn, "bad_stream", "invalid data encoding")
				continue
			}
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.BytesIn.Add(float64(len(payload)))
			}
			response, err := h.Upstream.Write(ctx, session.ID, frame.StreamID, payload)
			if err != nil {
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.UpstreamErrors.WithLabelValues("write").Inc()
					h.Metrics.StreamErrors.WithLabelValues("upstream_write").Inc()
				}
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
				if h.Metrics != nil && h.Metrics.MetricsEnabled {
					h.Metrics.StreamErrors.WithLabelValues("bad_stream_close").Inc()
				}
				h.sendError(conn, "bad_stream", "invalid stream_close")
				continue
			}
			h.Upstream.CloseStream(ctx, session.ID, frame.StreamID)
			h.Sessions.CloseStream(session.ID, frame.StreamID)
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.ActiveStreams.Set(float64(h.Sessions.ActiveStreams()))
				h.Metrics.StreamCloseTotal.Inc()
			}
		case FramePing:
			h.sendFrame(conn, Envelope{Type: FramePong})
		default:
			if h.Metrics != nil && h.Metrics.MetricsEnabled {
				h.Metrics.StreamErrors.WithLabelValues("unsupported_frame").Inc()
			}
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
