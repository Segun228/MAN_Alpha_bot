package logkeys

type contextKey string

const LogMetricsKey contextKey = "log_metrics_data"

type LogMetrics struct {
	UserID          int
	TelegramID      string
	IsAuthenticated bool
	Platform        string
	Action          string
	Level           string
	Env             string
	Message         string
}
