package v1

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
)

type userRoutes struct {
	userService service.User
	logger      utils.Logger
}

func newUserRoutes(r chi.Router, userService service.User, logger utils.Logger) {
	ur := &userRoutes{
		userService: userService,
		logger:      logger,
	}
	r.Route("/users", func(r chi.Router) {
		r.Get("/", ur.getAll)
		r.Get("/{userID}", ur.getByID)
		r.Get("/tg/{tgID}", ur.getByTgID)
		r.Post("/", ur.create)
		r.Post("/{userID}/businesses", ur.addBusinessByID)
		r.Post("/tg/{tgId}/businesses", ur.addBusinessByTgID)
		r.Put("/{userID}", ur.putByID)
		r.Put("/tg/{tgId}", ur.putByTgID)
		r.Patch("/{userID}", ur.patchByID)
		r.Patch("/tg/{tgId}", ur.patchByTgID)
		r.Delete("/{userID}", ur.deleteByID)
		r.Delete("/tg/{tgId}", ur.deleteByTgID)
	})
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")

	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")

	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}

// @Summary Get all users
// @Description Получить список всех пользователей
// @Tags users
// @Accept json
// @Produce json
// @Success 200 {array} models.User
// @Failure 500 {object} map[string]string
// @Router /users [get]
func (ur *userRoutes) getAll(w http.ResponseWriter, r *http.Request) {
	users, err := ur.userService.GetUsers(r.Context())
	if err != nil {
		ur.logger.Error("error getting user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to get users")
		return
	}

	writeJSON(w, http.StatusOK, users)
}

func parseIDParam(idParam string) (int, error) {
	var id int
	_, err := fmt.Sscanf(idParam, "%d", &id)
	if err != nil {
		return 0, err
	}
	return id, nil
}

func parseTgIDParam(tgIDParam string) (int64, error) {
	var tgID int64
	_, err := fmt.Sscanf(tgIDParam, "%d", &tgID)
	if err != nil {
		return 0, err
	}
	return tgID, nil
}

// @Summary Get user by ID
// @Description Получить пользователя по ID
// @Tags users
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/{userID} [get]
func (ur *userRoutes) getByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	user, err := ur.userService.GetUserByID(r.Context(), userID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get user by ID")
		return
	}

	writeJSON(w, http.StatusOK, user)
}

// @Summary Get user by Telegram ID
// @Description Получить пользователя по Telegram ID
// @Tags users
// @Accept json
// @Produce json
// @Param tgID path int true "Telegram ID"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/tg/{tgID} [get]
func (ur *userRoutes) getByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgID")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	user, err := ur.userService.GetUserByTgID(r.Context(), tgID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get user by Telegram ID")
		return
	}

	writeJSON(w, http.StatusOK, user)
}

type createUserRequest struct {
	TelegramID int64  `json:"telegram_id"`
	Login      string `json:"login"`
	Password   string `json:"password"`
	Email      string `json:"email"`
}

// @Summary Create new user
// @Description Создать нового пользователя
// @Tags users
// @Accept json
// @Produce json
// @Param user body createUserRequest true "User info"
// @Success 201 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users [post]
func (ur *userRoutes) create(w http.ResponseWriter, r *http.Request) {
	var req createUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	user := models.User{
		TelegramID: req.TelegramID,
		Login:      req.Login,
		Password:   req.Password,
		Email:      req.Email,
	}

	createdUser, err := ur.userService.CreateUser(r.Context(), user)
	if err != nil {
		ur.logger.Error("error getting user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to create user")
		return
	}

	writeJSON(w, http.StatusCreated, createdUser)
}

type addBusinessRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

// @Summary Add business to user by ID
// @Description Добавить бизнес пользователю по ID
// @Tags users
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Param business body addBusinessRequest true "Business info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/{userID}/businesses [post]
func (ur *userRoutes) addBusinessByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		ur.logger.Error("invalid user id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req addBusinessRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		Name:        req.Name,
		Description: req.Description,
	}

	updatedUser, err := ur.userService.AddBusinessToUserByID(r.Context(), userID, business)
	if err != nil {
		ur.logger.Error("error updating user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to add business to user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

// @Summary Add business to user by Telegram ID
// @Description Добавить бизнес пользователю по Telegram ID
// @Tags users
// @Accept json
// @Produce json
// @Param tgId path int true "Telegram ID"
// @Param business body addBusinessRequest true "Business info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/tg/{tgId}/businesses [post]
func (ur *userRoutes) addBusinessByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		ur.logger.Error("error parsing user_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req addBusinessRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		Name:        req.Name,
		Description: req.Description,
	}

	updatedUser, err := ur.userService.AddBusinessToUserByTgID(r.Context(), tgID, business)
	if err != nil {
		ur.logger.Error("error adding business to user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to add business to user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

type updateUserRequest struct {
	Login    string `json:"login,omitempty"`
	Password string `json:"password,omitempty"`
	Email    string `json:"email,omitempty"`
	Churned  *bool  `json:"churned,omitempty"`
	IsAdmin  *bool  `json:"is_admin,omitempty"`
}

// @Summary Update user by ID (full)
// @Description Полное обновление пользователя по ID
// @Tags users
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Param user body updateUserRequest true "User info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/{userID} [put]
func (ur *userRoutes) putByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		ur.logger.Error("error parsing user_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	user := models.User{
		ID:       userID,
		Login:    req.Login,
		Password: req.Password,
		Email:    req.Email,
	}

	updatedUser, err := ur.userService.PutUserByID(r.Context(), user)
	if err != nil {
		ur.logger.Error("error updating whole user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to update user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

// @Summary Update user by Telegram ID (full)
// @Description Полное обновление пользователя по Telegram ID
// @Tags users
// @Accept json
// @Produce json
// @Param tgId path int true "Telegram ID"
// @Param user body updateUserRequest true "User info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/tg/{tgId} [put]
func (ur *userRoutes) putByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		ur.logger.Error("error parsing tg_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	user := models.User{
		Login:    req.Login,
		Password: req.Password,
		Email:    req.Email,
	}

	updatedUser, err := ur.userService.PutUserByTgID(r.Context(), tgID, user)
	if err != nil {
		ur.logger.Error("error updating whole user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to update user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

// @Summary Patch user by ID
// @Description Частичное обновление пользователя по ID
// @Tags users
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Param user body updateUserRequest true "User info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/{userID} [patch]
func (ur *userRoutes) patchByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		ur.logger.Error("error parsing user_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	user := models.User{
		ID:       userID,
		Login:    req.Login,
		Password: req.Password,
		Email:    req.Email,
	}

	updatedUser, err := ur.userService.PatchUser(r.Context(), user)
	if err != nil {
		ur.logger.Error("error patching user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to patch user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

// @Summary Patch user by Telegram ID
// @Description Частичное обновление пользователя по Telegram ID
// @Tags users
// @Accept json
// @Produce json
// @Param tgId path int true "Telegram ID"
// @Param user body updateUserRequest true "User info"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/tg/{tgId} [patch]
func (ur *userRoutes) patchByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		ur.logger.Error("error parsing tg_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		ur.logger.Error("error decoding request_body", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	userFromDB, err := ur.userService.GetUserByTgID(r.Context(), tgID)
	if err != nil {
		ur.logger.Error("error getting user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to get user by Telegram ID")
		return
	}

	user := models.User{
		ID:       userFromDB.ID,
		Login:    req.Login,
		Password: req.Password,
		Email:    req.Email,
	}

	updatedUser, err := ur.userService.PatchUser(r.Context(), user)
	if err != nil {
		ur.logger.Error("error patching user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to patch user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

// @Summary Delete user by ID
// @Description Удалить пользователя по ID
// @Tags users
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Success 204 {object} nil
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/{userID} [delete]
func (ur *userRoutes) deleteByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		ur.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	err = ur.userService.DeleteUserByID(r.Context(), userID)
	if err != nil {
		ur.logger.Error("error deleting user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to delete user")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// @Summary Delete user by Telegram ID
// @Description Удалить пользователя по Telegram ID
// @Tags users
// @Accept json
// @Produce json
// @Param tgId path int true "Telegram ID"
// @Success 204 {object} nil
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /users/tg/{tgId} [delete]
func (ur *userRoutes) deleteByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		ur.logger.Error("error parsing tg_id", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	err = ur.userService.DeleteUserByTgID(r.Context(), tgID)
	if err != nil {
		ur.logger.Error("error deleting user", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to delete user")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
