package upstream

import (
	"context"
	"errors"
	"sync"
)

type FakeUpstream struct {
	mu       sync.Mutex
	streams  map[string]map[string]struct{}
	sessions map[string]OutlineNodeConfig
	echoMode bool
}

func NewFakeUpstream(echo bool) *FakeUpstream {
	return &FakeUpstream{streams: make(map[string]map[string]struct{}), sessions: make(map[string]OutlineNodeConfig), echoMode: echo}
}

func (f *FakeUpstream) BindSession(ctx context.Context, sessionID string, node OutlineNodeConfig) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.sessions[sessionID] = node
	if _, ok := f.streams[sessionID]; !ok {
		f.streams[sessionID] = make(map[string]struct{})
	}
	return nil
}

func (f *FakeUpstream) OpenStream(ctx context.Context, sessionID string, streamID string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if _, ok := f.streams[sessionID]; !ok {
		f.streams[sessionID] = make(map[string]struct{})
	}
	if _, exists := f.streams[sessionID][streamID]; exists {
		return errors.New("stream_exists")
	}
	f.streams[sessionID][streamID] = struct{}{}
	return nil
}

func (f *FakeUpstream) Write(ctx context.Context, sessionID string, streamID string, data []byte) ([]byte, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if _, ok := f.streams[sessionID]; !ok {
		return nil, errors.New("session_not_found")
	}
	if _, exists := f.streams[sessionID][streamID]; !exists {
		return nil, errors.New("stream_not_found")
	}
	if f.echoMode {
		return data, nil
	}
	return nil, nil
}

func (f *FakeUpstream) CloseStream(ctx context.Context, sessionID string, streamID string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	if _, ok := f.streams[sessionID]; !ok {
		return nil
	}
	delete(f.streams[sessionID], streamID)
	if len(f.streams[sessionID]) == 0 {
		delete(f.streams, sessionID)
	}
	return nil
}
