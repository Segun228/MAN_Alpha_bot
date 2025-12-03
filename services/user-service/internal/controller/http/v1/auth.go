package v1

import (
	"encoding/json"
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
)

type authRoutes struct {
	authService service.Auth
	logger      utils.Logger
}

func newAuthRoutes(r chi.Router, authService service.Auth, logger utils.Logger) {
	ar := &authRoutes{
		authService: authService,
		logger:      logger,
	}

	r.Route("/auth", func(r chi.Router) {
		r.Post("/login", ar.login)
		// r.Post("/register", ar.register)
	})
}

type loginRequest struct {
	Login    string `json:"login"`
	Password string `json:"password"`
}

type loginResponse struct {
	UserID int `json:"user_id"`
}

// @Summary Login a user
// @Description Аутентификация пользователя по логину и паролю
// @Tags Auth
// @Accept json
// @Produce json
// @Param loginRequest body loginRequest true "Login Request"
// @Success 200 {object} loginResponse
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

	userID, err := ar.authService.VerifyUserCredentials(r.Context(), req.Login, req.Password)
	if err != nil {
		switch err {
		case service.ErrInvalidCredentials:
			writeError(w, http.StatusUnauthorized, "invalid credentials")
			return
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "user not found")
			return
		default:
			ar.logger.Error("failed to verify user credentials", map[string]any{
				"error": err,
			})
			writeError(w, http.StatusInternalServerError, "internal server error")
			return
		}
	}

	writeJSON(w, http.StatusOK, loginResponse{
		UserID: userID,
	})
}
