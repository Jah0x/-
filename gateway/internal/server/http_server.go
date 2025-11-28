package server

import (
	"context"
	"crypto/tls"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
	"github.com/httvps/httvps/gateway/internal/config"
	"github.com/httvps/httvps/gateway/internal/metrics"
	"github.com/httvps/httvps/gateway/internal/protocol"
	"golang.org/x/exp/slog"
)

type HTTPServer struct {
	cfg      config.Config
	handler  *protocol.Handler
	metrics  *metrics.Metrics
	logger   *slog.Logger
	server   *http.Server
	upgrader websocket.Upgrader
}

func New(cfg config.Config, handler *protocol.Handler, metrics *metrics.Metrics, logger *slog.Logger) *HTTPServer {
	upgrader := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
	return &HTTPServer{cfg: cfg, handler: handler, metrics: metrics, logger: logger, upgrader: upgrader}
}

func (s *HTTPServer) Start(ctx context.Context) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", s.handleWebsocket)
	if s.metrics != nil && s.metrics.MetricsEnabled {
		mux.Handle(s.cfg.MetricsPath, s.metrics.Handler())
	}
	s.server = &http.Server{Addr: s.cfg.ListenAddr, Handler: mux, TLSConfig: &tls.Config{MinVersion: tls.VersionTLS12}}
	shutdownDone := make(chan struct{})
	go func() {
		<-ctx.Done()
		ctxShutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		s.server.Shutdown(ctxShutdown)
		close(shutdownDone)
	}()
	err := s.server.ListenAndServeTLS(s.cfg.TLSCertPath, s.cfg.TLSKeyPath)
	<-shutdownDone
	return err
}

func (s *HTTPServer) handleWebsocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	go s.handler.Handle(r.Context(), conn)
}
