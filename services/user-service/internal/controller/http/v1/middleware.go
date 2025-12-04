package v1

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/controller/http/v1/logkeys"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/broker"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/google/uuid"
)

func loggingMiddleware(log utils.Logger, logsBroker broker.MessageBroker, env string) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			metricsPtr := &logkeys.LogMetrics{
				Env: env,
			}
			newCtx := context.WithValue(r.Context(), logkeys.LogMetricsKey, metricsPtr)

			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

			bodyStr := readAndReplaceBody(r, log)

			start := time.Now()
			next.ServeHTTP(ww, r.WithContext(newCtx))
			duration := time.Since(start)

			log.Info("request completed", map[string]any{
				"method":      r.Method,
				"path":        r.URL.Path,
				"status":      ww.Status(),
				"duration_ms": duration.Milliseconds(),
				"remote_ip":   r.RemoteAddr,
			})

			logToSend := models.Log{
				Timestamp:     time.Now(),
				TraceID:       uuid.New().String(),
				RequestMethod: r.Method,
				RequestBody:   bodyStr,
				ResponseCode:  ww.Status(),
				Source:        "user-service",

				UserID:          metricsPtr.UserID,
				TelegramID:      metricsPtr.TelegramID,
				IsAuthenticated: metricsPtr.IsAuthenticated,
				Platform:        metricsPtr.Platform,
				Action:          metricsPtr.Action,
				Level:           metricsPtr.Level,
				EventType:       metricsPtr.Action,
				Env:             metricsPtr.Env,
				Message:         metricsPtr.Message,
			}

			if metricsPtr.Action != "" {
				logs := []models.Log{logToSend}
				logsBroker.SendLogs(newCtx, logs)
			}
		})
	}
}

func TrustedSerciceMiddleware(botKey string, logger utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
			metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

			if key := r.Header.Get("X-Bot-Key"); key != "" && key == botKey {
				if ok {
					metricsPtr.IsAuthenticated = true
					metricsPtr.Platform = "bot"
				}
				next.ServeHTTP(w, r)
				return
			}

			if userID := r.Header.Get("X-User-ID"); userID != "" {
				if ok {
					metricsPtr.IsAuthenticated = true
					metricsPtr.Platform = "web"
				}
				next.ServeHTTP(w, r)
				return
			}

			logger.Error("forbidden: no trusted credential provided")
			if ok {
				metricsPtr.IsAuthenticated = false
				metricsPtr.Message = "forbidden: no trusted credential provided"
			}
			writeError(w, http.StatusForbidden, "access forbidden")
		})
	}
}

func BotAuthMiddleware(botKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
			metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

			defer func() {
				if ok {
					metricsPtr.IsAuthenticated = false
				}
			}()

			key := r.Header.Get("X-Bot-Key")
			if key == "" || key != botKey {
				writeError(w, http.StatusUnauthorized, "invalid or missing bot key")
				return
			}

			if ok {
				metricsPtr.IsAuthenticated = true
				metricsPtr.Platform = "bot"
			}
			next.ServeHTTP(w, r)
		})
	}
}

func readAndReplaceBody(r *http.Request, logger utils.Logger) string {
	if r.ContentLength == 0 {
		return ""
	}

	bodyBytes, err := io.ReadAll(r.Body)
	if err != nil {
		logger.Error("failed to read request body for logging", map[string]any{
			"error": err,
		})
		r.Body.Close()

		r.Body = http.NoBody
		return "[Error reading body]"
	}

	r.Body.Close()

	r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	return string(bodyBytes)
}
