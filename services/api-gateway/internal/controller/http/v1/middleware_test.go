package v1

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-openapi/testify/v2/assert"
)

func TestAuthMiddleware(t *testing.T) {
	logger := utils.NewLogger("dev")
	tokenService := service.NewTokenService(15*time.Minute, 24*time.Hour, "test-secret-key")
	botKey := "test-bot-key"

	middleware := HybridAuthMiddleware(tokenService, logger, botKey)

	finalHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	testHandler := middleware(finalHandler)

	t.Run("Success - Valid JWT Key", func(t *testing.T) {
		tokens, _ := tokenService.GenerateTokens(123)
		req := httptest.NewRequest(http.MethodPost, "/api/protected", nil)
		req.Header.Set("Authorization", "Bearer "+tokens.AccessToken)
		rr := httptest.NewRecorder()

		testHandler.ServeHTTP(rr, req)
		assert.Equal(t, http.StatusOK, rr.Code)
	})

	t.Run("Success - Valid Bot Key", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/api/protected", nil)
		req.Header.Set("X-Bot-Key", botKey)
		rr := httptest.NewRecorder()

		testHandler.ServeHTTP(rr, req)
		assert.Equal(t, http.StatusOK, rr.Code)
	})

	t.Run("Failure - Invalid JWT Token", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodPost, "/api/protected", nil)
		req.Header.Set("Authorization", "Bearer invalid-token")
		rr := httptest.NewRecorder()

		testHandler.ServeHTTP(rr, req)
		assert.Equal(t, http.StatusUnauthorized, rr.Code)
	})
}
