package upstream

import (
	"context"
	"errors"
	"io"
	"net"
	"strconv"
	"sync"
	"time"

	"github.com/shadowsocks/go-shadowsocks2/core"
)

type outlineDialer interface {
	Dial(ctx context.Context, address string, method string, password string) (net.Conn, error)
}

type shadowsocksDialer struct {
	dialer net.Dialer
}

func (s *shadowsocksDialer) Dial(ctx context.Context, address string, method string, password string) (net.Conn, error) {
	conn, err := s.dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, err
	}
	if method == "" {
		return conn, nil
	}
	cipher, err := core.PickCipher(method, nil, password)
	if err != nil {
		conn.Close()
		return nil, err
	}
	streamCipher, ok := cipher.(core.StreamConnCipher)
	if !ok {
		conn.Close()
		return nil, errors.New("cipher_not_supported")
	}
	return streamCipher.StreamConn(conn), nil
}

type OutlineUpstream struct {
	mu        sync.Mutex
	sessions  map[string]OutlineNodeConfig
	streams   map[string]map[string]net.Conn
	dialer    outlineDialer
	ioTimeout time.Duration
}

func NewOutlineUpstream(timeout time.Duration) *OutlineUpstream {
	if timeout <= 0 {
		timeout = 5 * time.Second
	}
	return newOutlineUpstreamWithDialer(timeout, &shadowsocksDialer{})
}

func newOutlineUpstreamWithDialer(timeout time.Duration, dialer outlineDialer) *OutlineUpstream {
	return &OutlineUpstream{sessions: make(map[string]OutlineNodeConfig), streams: make(map[string]map[string]net.Conn), dialer: dialer, ioTimeout: timeout}
}

func (o *OutlineUpstream) BindSession(ctx context.Context, sessionID string, node OutlineNodeConfig) error {
	o.mu.Lock()
	defer o.mu.Unlock()
	o.sessions[sessionID] = node
	if _, ok := o.streams[sessionID]; !ok {
		o.streams[sessionID] = make(map[string]net.Conn)
	}
	return nil
}

func (o *OutlineUpstream) OpenStream(ctx context.Context, sessionID string, streamID string) error {
	node, ok := o.sessionNode(sessionID)
	if !ok {
		return errors.New("session_not_bound")
	}
	address := net.JoinHostPort(node.Host, strconv.Itoa(node.Port))
	conn, err := o.dialer.Dial(ctx, address, node.Method, node.Password)
	if err != nil {
		return err
	}
	o.mu.Lock()
	if _, ok := o.streams[sessionID]; !ok {
		o.streams[sessionID] = make(map[string]net.Conn)
	}
	if _, exists := o.streams[sessionID][streamID]; exists {
		o.mu.Unlock()
		conn.Close()
		return errors.New("stream_exists")
	}
	o.streams[sessionID][streamID] = conn
	o.mu.Unlock()
	return nil
}

func (o *OutlineUpstream) Write(ctx context.Context, sessionID string, streamID string, data []byte) ([]byte, error) {
	conn, err := o.getStream(sessionID, streamID)
	if err != nil {
		return nil, err
	}
	if o.ioTimeout > 0 {
		_ = conn.SetDeadline(time.Now().Add(o.ioTimeout))
	}
	if _, err := conn.Write(data); err != nil {
		return nil, err
	}
	buf := make([]byte, 65536)
	n, err := conn.Read(buf)
	if err != nil {
		if netErr, ok := err.(net.Error); ok && netErr.Timeout() && n == 0 {
			return nil, nil
		}
		if errors.Is(err, io.EOF) && n == 0 {
			return nil, err
		}
		if n > 0 {
			return buf[:n], nil
		}
		return nil, err
	}
	if o.ioTimeout > 0 {
		_ = conn.SetDeadline(time.Time{})
	}
	return buf[:n], nil
}

func (o *OutlineUpstream) CloseStream(ctx context.Context, sessionID string, streamID string) error {
	o.mu.Lock()
	defer o.mu.Unlock()
	if _, ok := o.streams[sessionID]; !ok {
		return nil
	}
	if conn, exists := o.streams[sessionID][streamID]; exists {
		conn.Close()
		delete(o.streams[sessionID], streamID)
	}
	if len(o.streams[sessionID]) == 0 {
		delete(o.streams, sessionID)
	}
	return nil
}

func (o *OutlineUpstream) sessionNode(sessionID string) (OutlineNodeConfig, bool) {
	o.mu.Lock()
	defer o.mu.Unlock()
	node, ok := o.sessions[sessionID]
	return node, ok
}

func (o *OutlineUpstream) getStream(sessionID string, streamID string) (net.Conn, error) {
	o.mu.Lock()
	defer o.mu.Unlock()
	streams, ok := o.streams[sessionID]
	if !ok {
		return nil, errors.New("session_not_found")
	}
	conn, ok := streams[streamID]
	if !ok {
		return nil, errors.New("stream_not_found")
	}
	return conn, nil
}
