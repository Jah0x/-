package protocol

type FrameType string

const (
	FrameHello       FrameType = "hello"
	FrameAuthResult  FrameType = "auth_result"
	FrameStreamOpen  FrameType = "stream_open"
	FrameStreamData  FrameType = "stream_data"
	FrameStreamClose FrameType = "stream_close"
	FramePing        FrameType = "ping"
	FramePong        FrameType = "pong"
	FrameError       FrameType = "error"
)

type Envelope struct {
	Type FrameType `json:"type"`
}

type HelloFrame struct {
	Type          FrameType `json:"type"`
	DeviceID      string    `json:"device_id"`
	Token         string    `json:"token"`
	ClientVersion string    `json:"client_version,omitempty"`
	Capabilities  []string  `json:"capabilities,omitempty"`
	Region        string    `json:"region,omitempty"`
}

type AuthResultFrame struct {
	Type               FrameType `json:"type"`
	Allowed            bool      `json:"allowed"`
	SessionID          string    `json:"session_id,omitempty"`
	SubscriptionStatus string    `json:"subscription_status,omitempty"`
	Reason             string    `json:"reason,omitempty"`
}

type StreamOpenFrame struct {
	Type     FrameType `json:"type"`
	StreamID string    `json:"stream_id"`
	Target   string    `json:"target,omitempty"`
}

type StreamDataFrame struct {
	Type     FrameType `json:"type"`
	StreamID string    `json:"stream_id"`
	Data     string    `json:"data"`
}

type StreamCloseFrame struct {
	Type     FrameType `json:"type"`
	StreamID string    `json:"stream_id"`
	Reason   string    `json:"reason,omitempty"`
}

type ErrorFrame struct {
	Type    FrameType `json:"type"`
	Code    string    `json:"code"`
	Message string    `json:"message,omitempty"`
}
