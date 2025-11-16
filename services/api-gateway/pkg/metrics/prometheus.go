package metrics

import "github.com/prometheus/client_golang/prometheus"

type Metrics struct {
	HttpRequestsTotal          *prometheus.CounterVec
	HttpRequestDurationSeconds *prometheus.HistogramVec
}

func NewMetrics(reg prometheus.Registerer) *Metrics {
	return &Metrics{
		HttpRequestsTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of http requests",
			}, []string{"mathod", "path", "status"}),

		HttpRequestDurationSeconds: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_duration_seconds",
				Help:    "HTTP request duration in seconds",
				Buckets: prometheus.DefBuckets,
			}, []string{"method", "path"},
		),
	}
}
