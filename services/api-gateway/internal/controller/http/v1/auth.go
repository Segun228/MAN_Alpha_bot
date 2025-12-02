package v1

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
)

type contextKey string

const userIDKey contextKey = "user_id"

type authRoutes struct {
	authService    service.Token
	logger         utils.Logger
	userServiceURL string
}

func newAuthRoutes(r chi.Router, authService service.Token, logger utils.Logger, userServiceURL string) {
	ar := &authRoutes{
		authService:    authService,
		logger:         logger,
		userServiceURL: userServiceURL,
	}

	r.Route("/auth", func(r chi.Router) {
		r.Post("/login", ar.login)
		r.Post("/refresh", ar.refresh)
	})
}

type loginRequest struct {
	Login    string `json:"login"`
	Password string `json:"password"`
}

type userServiceLoginResponse struct {
	UserID int `json:"user_id"`
}

// @Summary Login a user
// @Description Авторизовать пользователя и получить JWT токены
// @Tags Auth
// @Accept json
// @Produce json
// @Param loginRequest body loginRequest true "Login Request"
// @Success 200 {object} service.Tokens
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/login [post]
func (ar *authRoutes) login(w http.ResponseWriter, r *http.Request) {
	var req loginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ar.logger.Error("failed to decode login request", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	userSvcURL := ar.userServiceURL + "/auth/login"
	reqBody, err := json.Marshal(req)
	if err != nil {
		ar.logger.Error("failed to marshal login request", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	resp, err := http.Post(userSvcURL, "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		ar.logger.Error("failed to call user service login", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		ar.logger.Error("user service login returned non-200 status", map[string]any{
			"status_code": resp.StatusCode,
		})
		writeError(w, resp.StatusCode, "failed to login")
		return
	}

	var userResp userServiceLoginResponse
	if err := json.NewDecoder(resp.Body).Decode(&userResp); err != nil {
		ar.logger.Error("failed to decode user service login response", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	tokens, err := ar.authService.GenerateTokens(userResp.UserID)
	if err != nil {
		ar.logger.Error("failed to generate tokens", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, tokens)
}

type refreshRequest struct {
	RefreshToken string `json:"refresh_token"`
}

// @Summary Refresh tokens
// @Description Обновить JWT токены с помощью refresh токена
// @Tags Auth
// @Accept json
// @Produce json
// @Param refreshRequest body refreshRequest true "Refresh Request"
// @Success 200 {object} service.Tokens
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/refresh [post]
func (ar *authRoutes) refresh(w http.ResponseWriter, r *http.Request) {
	var req refreshRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ar.logger.Error("failed to decode refresh request", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	userID, err := ar.authService.ParseToken(req.RefreshToken)
	if err != nil {
		ar.logger.Error("failed to parse refresh token", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusUnauthorized, "invalid refresh token")
		return
	}

	tokens, err := ar.authService.GenerateTokens(userID)
	if err != nil {
		ar.logger.Error("failed to generate tokens", map[string]any{
			"error": err,
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, tokens)
}

func AuthMiddleware(tokenService service.Token, logger utils.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				writeError(w, http.StatusUnauthorized, "missing authorization header")
				return
			}

			headerParts := strings.Split(authHeader, " ")
			if len(headerParts) != 2 || headerParts[0] != "Bearer" {
				writeError(w, http.StatusUnauthorized, "invalid authorization header format")
				return
			}

			accessToken := headerParts[1]
			userID, err := tokenService.ParseToken(accessToken)
			if err != nil {
				logger.Error("failed to parse access token", map[string]any{
					"error": err,
				})
			}

			ctx := context.WithValue(r.Context(), userIDKey, userID)
			next.ServeHTTP(w, r.WithContext(ctx))
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

func HybridAuthMiddleware(tokenService service.Token, logger utils.Logger, botKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			botKeyHeader := r.Header.Get("X-Bot-Key")

			if authHeader != "" {
				headerParts := strings.Split(authHeader, " ")
				if len(headerParts) == 2 && headerParts[0] == "Bearer" {
					accessToken := headerParts[1]
					userID, err := tokenService.ParseToken(accessToken)
					if err == nil {
						ctx := context.WithValue(r.Context(), userIDKey, userID)
						next.ServeHTTP(w, r.WithContext(ctx))
						return
					}

					logger.Error("failed to parse access token", map[string]any{
						"error": err,
					})
					writeError(w, http.StatusUnauthorized, "invalid access token")
					return
				}
			}

			if botKeyHeader != "" || botKeyHeader == botKey {
				next.ServeHTTP(w, r)
				return
			}

			logger.Error("unauthorized access: no valid credentials provided", nil)
			writeError(w, http.StatusUnauthorized, "no valid credentials provided")
		})
	}
}
