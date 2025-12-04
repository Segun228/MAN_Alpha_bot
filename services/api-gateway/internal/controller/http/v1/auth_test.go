package v1

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
	"github.com/go-openapi/testify/v2/assert"
	"github.com/go-openapi/testify/v2/require"
)

func TestAuthRoutes_Login(t *testing.T) {
	mockUserService := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		require.Equal(t, "/auth/login", r.URL.Path)

		var req loginRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)

		if req.Login == "test" && req.Password == "password" {
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(userServiceLoginResponse{UserID: 123})
		} else {
			w.WriteHeader(http.StatusUnauthorized)
			json.NewEncoder(w).Encode(map[string]string{"error": "invalid credentials"})
		}
	}))
	defer mockUserService.Close()

	logger := utils.NewLogger("dev")
	tokenService := service.NewTokenService(15*time.Minute, 24*time.Hour, "test-secret-key")

	router := chi.NewRouter()
	newAuthRoutes(router, tokenService, logger, mockUserService.URL)

	t.Run("Success - Correct Credentials", func(t *testing.T) {
		reqBody, _ := json.Marshal(map[string]string{"login": "test", "password": "password"})
		req := httptest.NewRequest(http.MethodPost, "/login", bytes.NewBuffer(reqBody))
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		assert.Equal(t, http.StatusOK, rr.Code)
		var tokens service.Tokens
		err := json.NewDecoder(rr.Body).Decode(&tokens)
		require.NoError(t, err)
		assert.NotEmpty(t, tokens.AccessToken)
		assert.NotEmpty(t, tokens.RefreshToken)
	})

	t.Run("Failure - Incorrect Credentials", func(t *testing.T) {
		reqBody, _ := json.Marshal(map[string]string{"login": "test", "password": "wrong"})
		req := httptest.NewRequest(http.MethodPost, "/login", bytes.NewBuffer(reqBody))
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		assert.Equal(t, http.StatusUnauthorized, rr.Code)
	})
}
