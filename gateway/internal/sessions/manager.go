package sessions

import (
	"errors"
	"sync"
	"time"

	"github.com/google/uuid"
)

type Stream struct {
	ID        string
	CreatedAt time.Time
}

type Session struct {
	ID         string
	DeviceID   string
	StartedAt  time.Time
	Streams    map[string]Stream
	MaxStreams int
}

type Manager struct {
	mu                   sync.RWMutex
	sessions             map[string]*Session
	maxStreamsPerSession int
}

func NewManager(maxStreams int) *Manager {
	return &Manager{sessions: make(map[string]*Session), maxStreamsPerSession: maxStreams}
}

func (m *Manager) CreateSessionWithID(id string, deviceID string, maxStreams int) (*Session, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	sessionID := id
	if sessionID == "" {
		sessionID = uuid.NewString()
	}
	if _, exists := m.sessions[sessionID]; exists {
		return nil, errors.New("session_exists")
	}
	session := &Session{ID: sessionID, DeviceID: deviceID, StartedAt: time.Now().UTC(), Streams: make(map[string]Stream), MaxStreams: maxStreams}
	m.sessions[sessionID] = session
	return session, nil
}

func (m *Manager) CloseSession(sessionID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.sessions, sessionID)
}

func (m *Manager) GetSession(sessionID string) (*Session, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	session, ok := m.sessions[sessionID]
	return session, ok
}

func (m *Manager) OpenStream(sessionID string, streamID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	session, ok := m.sessions[sessionID]
	if !ok {
		return errors.New("session_not_found")
	}
	if _, exists := session.Streams[streamID]; exists {
		return errors.New("stream_exists")
	}
	limit := m.maxStreamsPerSession
	if session.MaxStreams > 0 {
		limit = session.MaxStreams
	}
	if limit > 0 && len(session.Streams) >= limit {
		return errors.New("stream_limit")
	}
	session.Streams[streamID] = Stream{ID: streamID, CreatedAt: time.Now().UTC()}
	return nil
}

func (m *Manager) CloseStream(sessionID string, streamID string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	session, ok := m.sessions[sessionID]
	if !ok {
		return
	}
	delete(session.Streams, streamID)
}

func (m *Manager) ActiveSessions() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.sessions)
}

func (m *Manager) ActiveStreams() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	total := 0
	for _, session := range m.sessions {
		total += len(session.Streams)
	}
	return total
}
