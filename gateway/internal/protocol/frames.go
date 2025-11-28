package protocol

type FrameType string

const (
	FrameHello       FrameType = "hello"
	FrameReady       FrameType = "ready"
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
	Type         FrameType `json:"type"`
	SessionToken string    `json:"session_token"`
	Version      string    `json:"version"`
	Client       string    `json:"client,omitempty"`
}

type ReadyFrame struct {
	Type       FrameType `json:"type"`
	SessionID  string    `json:"session_id"`
	MaxStreams int       `json:"max_streams"`
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
