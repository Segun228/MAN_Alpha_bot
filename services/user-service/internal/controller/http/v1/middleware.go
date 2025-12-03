package v1

import (
	"net/http"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5/middleware"
)

func loggingMiddleware(log utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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

func TrustedSerciceMiddleware(botKey string, logger utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if key := r.Header.Get("X-Bot-Key"); key != "" && key == botKey {
				next.ServeHTTP(w, r)
				return
			}

			if userID := r.Header.Get("X-User-ID"); userID != "" {
				next.ServeHTTP(w, r)
				return
			}

			logger.Error("forbidden: no trusted credential provided")
			writeError(w, http.StatusForbidden, "access forbidden")
		})
	}
}

func BotAuthMiddleware(botKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := r.Header.Get("X-Bot-Key")
			if key == "" || key != botKey {
				writeError(w, http.StatusUnauthorized, "invalid or missing bot key")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
