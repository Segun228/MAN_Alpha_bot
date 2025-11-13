package v1

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/go-chi/chi/v5"
)

type userRoutes struct {
	userService service.User
}

func newUserRoutes(r chi.Router, userService service.User) {
	ur := &userRoutes{
		userService: userService,
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
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}

func (ur *userRoutes) getAll(w http.ResponseWriter, r *http.Request) {
	users, err := ur.userService.GetUsers(r.Context())
	if err != nil {
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

func (ur *userRoutes) create(w http.ResponseWriter, r *http.Request) {
	var req createUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
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
		writeError(w, http.StatusInternalServerError, "failed to create user")
		return
	}

	writeJSON(w, http.StatusCreated, createdUser)
}

type addBusinessRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

func (ur *userRoutes) addBusinessByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req addBusinessRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		Name:        req.Name,
		Description: req.Description,
	}

	updatedUser, err := ur.userService.AddBusinessToUserByID(r.Context(), userID, business)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to add business to user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

func (ur *userRoutes) addBusinessByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req addBusinessRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		Name:        req.Name,
		Description: req.Description,
	}

	updatedUser, err := ur.userService.AddBusinessToUserByTgID(r.Context(), tgID, business)
	if err != nil {
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

func (ur *userRoutes) putByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
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
		writeError(w, http.StatusInternalServerError, "failed to update user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

func (ur *userRoutes) putByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
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
		writeError(w, http.StatusInternalServerError, "failed to update user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

func (ur *userRoutes) patchByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
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
		writeError(w, http.StatusInternalServerError, "failed to patch user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

func (ur *userRoutes) patchByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	var req updateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	userFromDB, err := ur.userService.GetUserByTgID(r.Context(), tgID)
	if err != nil {
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
		writeError(w, http.StatusInternalServerError, "failed to patch user")
		return
	}

	writeJSON(w, http.StatusOK, updatedUser)
}

func (ur *userRoutes) deleteByID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	err = ur.userService.DeleteUserByID(r.Context(), userID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to delete user")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (ur *userRoutes) deleteByTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgId")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid telegram ID")
		return
	}

	err = ur.userService.DeleteUserByTgID(r.Context(), tgID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to delete user")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
