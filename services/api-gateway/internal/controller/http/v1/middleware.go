package v1

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"slices"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/metrics"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi/middleware"
	"github.com/sirupsen/logrus"
)

const (
	metricsRoutePath   = "/metrics"
	actuatorPrometheus = "/actuator/prometheus"
	defenderCheckURL   = "/defend/http"
)

func PrometheusMiddleware(m *metrics.Metrics) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
			next.ServeHTTP(ww, r)

			duration := time.Since(start).Seconds()
			m.HttpRequestDurationSeconds.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
			m.HttpRequestsTotal.WithLabelValues(r.Method, r.URL.Path, fmt.Sprintf("%d", ww.Status())).Inc()
		})
	}
}

func CORSMiddleware(allowedOrigins []string) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")
			if origin != "" && slices.Contains(allowedOrigins, origin) {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
			}

			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusNoContent)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

func loggingMiddleware(log utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == metricsRoutePath || r.URL.Path == actuatorPrometheus {
				next.ServeHTTP(w, r)
				return
			}

			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

			start := time.Now()
			next.ServeHTTP(ww, r)
			duration := time.Since(start)

			log.Info("request completed", map[string]any{
				"method":      r.Method,
				"path":        r.URL.Path,
				"status":      ww.Status(),
				"duration_ms": duration.Milliseconds(),
				"remote_ip":   r.RemoteAddr,
			})
		})
	}
}

func RecoveryMiddleware(logger utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if err := recover(); err != nil {
					logger.Error("recover from panic", logrus.Fields{
						"error": err,
					})
					writeError(w, http.StatusInternalServerError, "Internal Server Error")
				}
			}()
			next.ServeHTTP(w, r)
		})
	}
}

type defenderRequest struct {
	Prompt string `json:"prompt"`
}

type defederResponse struct {
	IsSafe bool `json:"is_safe"`
}

func DefenderCheckMiddleware(enabled bool, defenderUrl string, logger utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !enabled || r.ContentLength == 0 {
				next.ServeHTTP(w, r)
				return
			}

			bodyBytes, err := io.ReadAll(r.Body)
			if err != nil {
				logger.Error("failed to read request body", map[string]any{
					"error": err,
				})
				writeError(w, http.StatusInternalServerError, "cannot read request body")
				return
			}
			r.Body.Close()

			r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

			defReq := defenderRequest{
				Prompt: string(bodyBytes),
			}

			defenderPayload, err := json.Marshal(defReq)
			if err != nil {
				logger.Error("failed to marshal defender request payload", map[string]any{
					"error": err,
				})
				writeError(w, http.StatusInternalServerError, "cannot create security request")
				return
			}

			logger.Debug(string(defenderPayload))

			checkUrl := defenderUrl + defenderCheckURL

			resp, err := http.Post(checkUrl, "application/json", bytes.NewBuffer(defenderPayload))
			if err != nil {
				logger.Error("defender service call failed", map[string]any{
					"error": err,
				})
				writeError(w, http.StatusServiceUnavailable, "security service is unavailable")
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode != http.StatusOK {
				logger.Error("defender service returned non-200 status", map[string]any{
					"status": resp.StatusCode,
				})
				writeError(w, http.StatusForbidden, "request rejected by security service")
				return
			}

			var defResp defederResponse
			if err := json.NewDecoder(resp.Body).Decode(&defResp); err != nil {
				logger.Error("failed to decode defender response", map[string]any{
					"error": err,
				})
				writeError(w, http.StatusInternalServerError, "failed to parse security response")
				return
			}

			if !defResp.IsSafe {
				logger.Warn("request blocked by defender as unsafe", map[string]any{
					"ip_address": r.RemoteAddr,
				})
				writeError(w, http.StatusForbidden, "request content is considered unsafe")
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
