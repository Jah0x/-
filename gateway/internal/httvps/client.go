package httvps

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

type ValidateSessionRequest struct {
	SessionToken string `json:"session_token"`
}

type OutlineDescriptor struct {
	NodeID      int    `json:"node_id"`
	Host        string `json:"host"`
	Port        int    `json:"port"`
	Method      string `json:"method"`
	Password    string `json:"password"`
	Region      string `json:"region"`
	Pool        string `json:"pool"`
	AccessKeyID string `json:"access_key_id"`
	AccessURL   string `json:"access_url"`
}

type ValidateSessionResponse struct {
	SessionID  string            `json:"session_id"`
	DeviceID   string            `json:"device_id"`
	MaxStreams int               `json:"max_streams"`
	Outline    OutlineDescriptor `json:"outline"`
}

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
	Secret     string
}

func NewClient(baseURL string, timeout time.Duration, secret string) *Client {
	return &Client{BaseURL: baseURL, HTTPClient: &http.Client{Timeout: timeout}, Secret: secret}
}

func (c *Client) ValidateSession(ctx context.Context, token string) (ValidateSessionResponse, error) {
	var result ValidateSessionResponse
	payload, err := json.Marshal(ValidateSessionRequest{SessionToken: token})
	if err != nil {
		return result, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, fmt.Sprintf("%s/internal/httvps/validate-session", c.BaseURL), bytes.NewReader(payload))
	if err != nil {
		return result, err
	}
	req.Header.Set("Content-Type", "application/json")
	if c.Secret != "" {
		req.Header.Set("X-Internal-Secret", c.Secret)
	}
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return result, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, err
	}
	if resp.StatusCode != http.StatusOK {
		return result, errors.New(resp.Status)
	}
	if err := json.Unmarshal(data, &result); err != nil {
		return result, err
	}
	return result, nil
}
