package upstream

import (
	"context"
	"net"
	"sync"
	"testing"
	"time"
)

type pipeDialer struct {
	mu    sync.Mutex
	conns []net.Conn
}

func (p *pipeDialer) Dial(ctx context.Context, address string, method string, password string) (net.Conn, error) {
	client, server := net.Pipe()
	p.mu.Lock()
	p.conns = append(p.conns, server)
	p.mu.Unlock()
	return client, nil
}

func (p *pipeDialer) take() net.Conn {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.conns) == 0 {
		return nil
	}
	conn := p.conns[0]
	p.conns = p.conns[1:]
	return conn
}

func TestOutlineUpstreamBindAndWrite(t *testing.T) {
	dialer := &pipeDialer{}
	up := newOutlineUpstreamWithDialer(time.Second, dialer)
	if err := up.BindSession(context.Background(), "s1", OutlineNodeConfig{Host: "localhost", Port: 1}); err != nil {
		t.Fatalf("bind error: %v", err)
	}
	if err := up.OpenStream(context.Background(), "s1", "st1"); err != nil {
		t.Fatalf("open stream error: %v", err)
	}
	serverConn := dialer.take()
	if serverConn == nil {
		t.Fatalf("server connection missing")
	}
	go func() {
		buf := make([]byte, 4)
		serverConn.Read(buf)
		serverConn.Write([]byte("pong"))
	}()
	resp, err := up.Write(context.Background(), "s1", "st1", []byte("ping"))
	if err != nil {
		t.Fatalf("write error: %v", err)
	}
	if string(resp) != "pong" {
		t.Fatalf("unexpected response: %s", string(resp))
	}
	if err := up.CloseStream(context.Background(), "s1", "st1"); err != nil {
		t.Fatalf("close error: %v", err)
	}
}

func TestOutlineUpstreamMissingSession(t *testing.T) {
	up := NewOutlineUpstream(time.Second)
	if err := up.OpenStream(context.Background(), "missing", "st1"); err == nil {
		t.Fatalf("expected error for missing session")
	}
}

func TestOutlineUpstreamLoadsFromStore(t *testing.T) {
	dialer := &pipeDialer{}
	store := NewMemoryStore()
	cached := OutlineNodeConfig{Host: "localhost", Port: 1, Pool: "edge"}
	if err := store.Save(context.Background(), "s1", cached); err != nil {
		t.Fatalf("store error: %v", err)
	}
	up := newOutlineUpstreamWithDialerAndStore(time.Second, dialer, store)
	if err := up.OpenStream(context.Background(), "s1", "st1"); err != nil {
		t.Fatalf("open stream error: %v", err)
	}
	serverConn := dialer.take()
	if serverConn == nil {
		t.Fatalf("server connection missing")
	}
	go func() {
		buf := make([]byte, 4)
		serverConn.Read(buf)
		serverConn.Write([]byte("pong"))
	}()
	resp, err := up.Write(context.Background(), "s1", "st1", []byte("ping"))
	if err != nil {
		t.Fatalf("write error: %v", err)
	}
	if string(resp) != "pong" {
		t.Fatalf("unexpected response: %s", string(resp))
	}
	if err := up.UnbindSession(context.Background(), "s1"); err != nil {
		t.Fatalf("unbind error: %v", err)
	}
}
