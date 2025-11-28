package upstream

import (
	"context"
	"sync"
)

type SessionStore interface {
	Save(ctx context.Context, sessionID string, node OutlineNodeConfig) error
	Load(ctx context.Context, sessionID string) (OutlineNodeConfig, bool, error)
	Delete(ctx context.Context, sessionID string) error
}

type MemoryStore struct {
	mu    sync.Mutex
	store map[string]OutlineNodeConfig
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{store: make(map[string]OutlineNodeConfig)}
}

func (m *MemoryStore) Save(ctx context.Context, sessionID string, node OutlineNodeConfig) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.store[sessionID] = node
	return nil
}

func (m *MemoryStore) Load(ctx context.Context, sessionID string) (OutlineNodeConfig, bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	node, ok := m.store[sessionID]
	return node, ok, nil
}

func (m *MemoryStore) Delete(ctx context.Context, sessionID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.store, sessionID)
	return nil
}
