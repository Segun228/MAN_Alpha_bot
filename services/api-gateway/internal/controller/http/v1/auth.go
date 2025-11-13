package v1

import (
	"context"
	"net/http"
	"strings"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/golang-jwt/jwt"
)

type Auth struct {
	jwtSecretKey []byte
	botSecretKey []byte
}

type ctxKey string

const (
	UserIDKey   ctxKey = "user_id"
	AuthTypeKey ctxKey = "auth_type"

	BotRole string = "bot"
)

func NewAuth(jwtSecretKey, botSecretKey []byte) *Auth {
	return &Auth{
		jwtSecretKey: jwtSecretKey,
		botSecretKey: botSecretKey,
	}
}

func (a *Auth) Middleware(logger utils.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if there is a bot
			if string(a.botSecretKey) != "" {
				key := r.Header.Get("X-Bot-Key")
				if key != "" && key == string(a.botSecretKey) {
					userID := r.Header.Get("X-User-ID")
					if userID != "" {
						r.Header.Set("X-User-Role", "bot")
					}

					ctx := context.WithValue(r.Context(), AuthTypeKey, BotRole)

					r = r.WithContext(ctx)
					next.ServeHTTP(w, r)
				}
			}

			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				http.Error(w, "missing Authorization header", http.StatusUnauthorized)
				return
			}

			parts := strings.SplitN(authHeader, " ", 2)
			if len(parts) != 2 || parts[0] != "Bearer" {
				http.Error(w, "invalid Authorization header format", http.StatusUnauthorized)
				return
			}

			tokenStr := parts[1]
			token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
				if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
					return nil, http.ErrAbortHandler
				}
				return a.jwtSecretKey, nil
			})

			if err != nil || !token.Valid {
				http.Error(w, "invalid or expited token", http.StatusUnauthorized)
				return
			}

			claims, ok := token.Claims.(jwt.MapClaims)
			if !ok {
				http.Error(w, "invalid token claims", http.StatusUnauthorized)
				return
			}

			sub, _ := claims["sub"].(string)
			role, _ := claims["role"].(string)

			ctx := context.WithValue(r.Context(), UserIDKey, sub)
			r = r.WithContext(ctx)

			r.Header.Set("X-User-ID", sub)
			r.Header.Set("X-User-Role", role)

			next.ServeHTTP(w, r)
		})
	}
}

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
