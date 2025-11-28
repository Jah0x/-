package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/httvps/httvps/gateway/internal/config"
	"github.com/httvps/httvps/gateway/internal/httvps"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/protocol"
	"github.com/httvps/httvps/gateway/internal/server"
	"github.com/httvps/httvps/gateway/internal/sessions"
	"github.com/httvps/httvps/gateway/internal/upstream"
	"github.com/nats-io/nats.go"
	"github.com/redis/go-redis/v9"
	"golang.org/x/exp/slog"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config error: %v", err)
	}
	ctx := context.Background()
	logger := newLogger(cfg.LogFormat, cfg.LogLevel)
	m := metrics.New(cfg.MetricsEnabled, cfg.MetricsPath)
	validator := httvps.NewClient(cfg.BackendBaseURL, cfg.BackendTimeout, cfg.BackendSecret)
	sessionManager := sessions.NewManager(cfg.MaxStreamsPerSession)
	var store upstream.SessionStore = upstream.NewMemoryStore()
	switch cfg.UpstreamStore {
	case "redis":
		if cfg.RedisAddr == "" {
			log.Fatalf("redis addr required for store")
		}
		client := redis.NewClient(&redis.Options{Addr: cfg.RedisAddr, Username: cfg.RedisUsername, Password: cfg.RedisPassword, DB: cfg.RedisDB})
		if err := client.Ping(ctx).Err(); err != nil {
			log.Fatalf("redis ping error: %v", err)
		}
		store = upstream.NewRedisStore(client, cfg.SessionStoreTTL)
	case "nats":
		if cfg.NATSURL == "" {
			log.Fatalf("nats url required for store")
		}
		conn, err := nats.Connect(cfg.NATSURL)
		if err != nil {
			log.Fatalf("nats connect error: %v", err)
		}
		kv, err := upstream.NewNATSStore(conn, cfg.NATSBucket, cfg.SessionStoreTTL)
		if err != nil {
			log.Fatalf("nats store error: %v", err)
		}
		store = kv
	}
	var up upstream.Upstream
	switch cfg.UpstreamMode {
	case "outline":
		up = upstream.NewOutlineUpstreamWithStore(cfg.BackendTimeout, store)
	default:
		up = upstream.NewFakeUpstream(true)
	}
	handler := &protocol.Handler{Validator: validator, Sessions: sessionManager, Upstream: up, Metrics: m, Logger: logger, Version: "1"}
	logger.Info("upstream_mode", slog.String("mode", cfg.UpstreamMode))
	srv := server.New(cfg, handler, m, logger)
	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer cancel()
	if err := srv.Start(ctx); err != nil {
		logger.Error("gateway_exit", slog.String("error", err.Error()))
	}
}

func newLogger(format string, level string) *slog.Logger {
	var slogLevel slog.Level
	switch level {
	case "debug":
		slogLevel = slog.LevelDebug
	case "warn":
		slogLevel = slog.LevelWarn
	case "error":
		slogLevel = slog.LevelError
	default:
		slogLevel = slog.LevelInfo
	}
	var handler slog.Handler
	if format == "text" {
		handler = slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slogLevel})
	} else {
		handler = slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slogLevel})
	}
	return slog.New(handler)
}
