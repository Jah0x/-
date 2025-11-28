package auth

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

type ValidateDeviceRequest struct {
	DeviceID string `json:"device_id"`
	Token    string `json:"token"`
}

type ValidateDeviceResult struct {
	Allowed            bool   `json:"allowed"`
	UserID             int    `json:"user_id"`
	SubscriptionStatus string `json:"subscription_status"`
	Reason             string `json:"reason"`
}

type wrappedError struct {
	Detail ValidateDeviceResult `json:"detail"`
}

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewClient(baseURL string, timeout time.Duration) *Client {
	return &Client{BaseURL: baseURL, HTTPClient: &http.Client{Timeout: timeout}}
}

func (c *Client) ValidateDevice(ctx context.Context, req ValidateDeviceRequest) (ValidateDeviceResult, error) {
	var result ValidateDeviceResult
	body, err := json.Marshal(req)
	if err != nil {
		return result, err
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, fmt.Sprintf("%s/api/v1/auth/validate-device", c.BaseURL), bytes.NewReader(body))
	if err != nil {
		return result, err
	}
	request.Header.Set("Content-Type", "application/json")
	resp, err := c.HTTPClient.Do(request)
	if err != nil {
		return result, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, err
	}
	if resp.StatusCode == http.StatusOK {
		if err := json.Unmarshal(data, &result); err != nil {
			return result, err
		}
		return result, nil
	}
	if resp.StatusCode == http.StatusForbidden {
		if err := json.Unmarshal(data, &result); err == nil && (!result.Allowed || result.Reason != "") {
			result.Allowed = false
			return result, nil
		}
		var wrapped wrappedError
		if err := json.Unmarshal(data, &wrapped); err == nil && (!wrapped.Detail.Allowed || wrapped.Detail.Reason != "") {
			return wrapped.Detail, nil
		}
		return ValidateDeviceResult{Allowed: false, Reason: string(data)}, nil
	}
	return result, errors.New(resp.Status)
}
