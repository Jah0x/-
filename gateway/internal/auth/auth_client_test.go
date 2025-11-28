package auth

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestValidateDeviceSuccess(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"allowed":true,"user_id":1,"subscription_status":"active"}`))
	}))
	defer server.Close()
	client := NewClient(server.URL, 2*time.Second)
	result, err := client.ValidateDevice(context.Background(), ValidateDeviceRequest{DeviceID: "dev1", Token: "tok"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !result.Allowed || result.UserID != 1 || result.SubscriptionStatus != "active" {
		t.Fatalf("unexpected result: %+v", result)
	}
}

func TestValidateDeviceForbidden(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		w.Write([]byte(`{"allowed":false,"reason":"invalid_token"}`))
	}))
	defer server.Close()
	client := NewClient(server.URL, 2*time.Second)
	result, err := client.ValidateDevice(context.Background(), ValidateDeviceRequest{DeviceID: "dev1", Token: "bad"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.Allowed || result.Reason != "invalid_token" {
		t.Fatalf("unexpected result: %+v", result)
	}
}

func TestValidateDeviceServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()
	client := NewClient(server.URL, 2*time.Second)
	_, err := client.ValidateDevice(context.Background(), ValidateDeviceRequest{DeviceID: "dev1", Token: "bad"})
	if err == nil {
		t.Fatalf("expected error")
	}
}

func TestValidateDeviceTimeout(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()
	client := NewClient(server.URL, 50*time.Millisecond)
	_, err := client.ValidateDevice(context.Background(), ValidateDeviceRequest{DeviceID: "dev1", Token: "tok"})
	if err == nil {
		t.Fatalf("expected timeout error")
	}
}
