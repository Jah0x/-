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
	"golang.org/x/exp/slog"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config error: %v", err)
	}
	logger := newLogger(cfg.LogFormat, cfg.LogLevel)
	m := metrics.New(cfg.MetricsEnabled, cfg.MetricsPath)
	validator := httvps.NewClient(cfg.BackendBaseURL, cfg.BackendTimeout, cfg.BackendSecret)
	sessionManager := sessions.NewManager(cfg.MaxStreamsPerSession)
	var up upstream.Upstream
	switch cfg.UpstreamMode {
	case "outline":
		up = upstream.NewOutlineUpstream(cfg.BackendTimeout)
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
