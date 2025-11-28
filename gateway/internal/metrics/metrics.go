package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type Metrics struct {
	registry          *prometheus.Registry
	ActiveSessions    prometheus.Gauge
	ActiveStreams     prometheus.Gauge
	HandshakeTotal    *prometheus.CounterVec
	HandshakeDuration prometheus.Histogram
	ConnectionsTotal  *prometheus.CounterVec
	SessionDuration   prometheus.Histogram
	StreamOpenTotal   *prometheus.CounterVec
	StreamCloseTotal  prometheus.Counter
	StreamErrors      *prometheus.CounterVec
	UpstreamErrors    *prometheus.CounterVec
	BackendErrors     *prometheus.CounterVec
	BytesIn           prometheus.Counter
	BytesOut          prometheus.Counter
	MetricsEnabled    bool
	MetricsPath       string
}

func New(enabled bool, path string) *Metrics {
	m := &Metrics{registry: prometheus.NewRegistry(), MetricsEnabled: enabled, MetricsPath: path}
	m.ActiveSessions = prometheus.NewGauge(prometheus.GaugeOpts{Name: "httvps_gateway_active_sessions"})
	m.ActiveStreams = prometheus.NewGauge(prometheus.GaugeOpts{Name: "httvps_gateway_active_streams"})
	m.HandshakeTotal = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_handshakes_total"}, []string{"result"})
	m.HandshakeDuration = prometheus.NewHistogram(prometheus.HistogramOpts{Name: "httvps_gateway_handshake_duration_seconds", Buckets: prometheus.DefBuckets})
	m.ConnectionsTotal = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_connections_total"}, []string{"result"})
	m.SessionDuration = prometheus.NewHistogram(prometheus.HistogramOpts{Name: "httvps_gateway_session_duration_seconds", Buckets: prometheus.DefBuckets})
	m.StreamOpenTotal = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_stream_open_total"}, []string{"result"})
	m.StreamCloseTotal = prometheus.NewCounter(prometheus.CounterOpts{Name: "httvps_gateway_stream_close_total"})
	m.StreamErrors = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_stream_errors_total"}, []string{"reason"})
	m.UpstreamErrors = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_upstream_errors_total"}, []string{"operation"})
	m.BackendErrors = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_backend_errors_total"}, []string{"code"})
	m.BytesIn = prometheus.NewCounter(prometheus.CounterOpts{Name: "httvps_gateway_bytes_in_total"})
	m.BytesOut = prometheus.NewCounter(prometheus.CounterOpts{Name: "httvps_gateway_bytes_out_total"})
	if enabled {
		m.registry.MustRegister(m.ActiveSessions, m.ActiveStreams, m.HandshakeTotal, m.HandshakeDuration, m.ConnectionsTotal, m.SessionDuration, m.StreamOpenTotal, m.StreamCloseTotal, m.StreamErrors, m.UpstreamErrors, m.BackendErrors, m.BytesIn, m.BytesOut)
	}
	return m
}

func (m *Metrics) Handler() http.Handler {
	return promhttp.HandlerFor(m.registry, promhttp.HandlerOpts{})
}
