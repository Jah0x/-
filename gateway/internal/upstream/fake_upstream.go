package upstream

import (
	"context"
	"errors"
	"sync"
)

type Upstream interface {
	OpenStream(ctx context.Context, sessionID string, streamID string) error
	Write(ctx context.Context, sessionID string, streamID string, data []byte) ([]byte, error)
	CloseStream(ctx context.Context, sessionID string, streamID string) error
}

type FakeUpstream struct {
	mu       sync.Mutex
	streams  map[string]map[string]struct{}
	echoMode bool
}

func NewFakeUpstream(echo bool) *FakeUpstream {
	return &FakeUpstream{streams: make(map[string]map[string]struct{}), echoMode: echo}
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
