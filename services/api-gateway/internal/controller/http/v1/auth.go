package v1

import (
	"net/http"
)

func BotAuthMiddleware(botKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := r.Header.Get("X-Bot-Key")
			if key == "" || key != botKey {
				http.Error(w, "invalid or missing bot key", http.StatusUnauthorized)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
