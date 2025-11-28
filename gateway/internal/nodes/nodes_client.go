package nodes

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type AssignOutlineRequest struct {
	RegionCode string `json:"region_code,omitempty"`
	DeviceID   string `json:"device_id"`
}

type AssignOutlineResponse struct {
	NodeID   int    `json:"node_id"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Method   string `json:"method,omitempty"`
	Password string `json:"password,omitempty"`
	Region   string `json:"region,omitempty"`
}

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewClient(baseURL string, timeout time.Duration) *Client {
	return &Client{BaseURL: baseURL, HTTPClient: &http.Client{Timeout: timeout}}
}

func (c *Client) AssignOutlineNode(ctx context.Context, req AssignOutlineRequest) (AssignOutlineResponse, error) {
	var result AssignOutlineResponse
	body, err := json.Marshal(req)
	if err != nil {
		return result, err
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, fmt.Sprintf("%s/api/v1/nodes/assign-outline", c.BaseURL), bytes.NewReader(body))
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
	if len(data) > 0 {
		return result, fmt.Errorf("assign_outline_failed: %s", string(data))
	}
	return result, fmt.Errorf("assign_outline_failed: %s", resp.Status)
}
