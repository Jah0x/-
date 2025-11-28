package upstream

import "context"

type OutlineNodeConfig struct {
	NodeID      int
	Host        string
	Port        int
	Method      string
	Password    string
	Region      string
	Pool        string
	AccessKeyID string
	AccessURL   string
}

type Upstream interface {
	BindSession(ctx context.Context, sessionID string, node OutlineNodeConfig) error
	UnbindSession(ctx context.Context, sessionID string) error
	OpenStream(ctx context.Context, sessionID string, streamID string) error
	Write(ctx context.Context, sessionID string, streamID string, data []byte) ([]byte, error)
	CloseStream(ctx context.Context, sessionID string, streamID string) error
}
