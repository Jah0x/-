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
	m.BackendErrors = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "httvps_gateway_backend_errors_total"}, []string{"code"})
	m.BytesIn = prometheus.NewCounter(prometheus.CounterOpts{Name: "httvps_gateway_bytes_in_total"})
	m.BytesOut = prometheus.NewCounter(prometheus.CounterOpts{Name: "httvps_gateway_bytes_out_total"})
	if enabled {
		m.registry.MustRegister(m.ActiveSessions, m.ActiveStreams, m.HandshakeTotal, m.HandshakeDuration, m.BackendErrors, m.BytesIn, m.BytesOut)
	}
	return m
}

func (m *Metrics) Handler() http.Handler {
	return promhttp.HandlerFor(m.registry, promhttp.HandlerOpts{})
}
