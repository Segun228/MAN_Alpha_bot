package v1

import (
	"encoding/json"
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/go-chi/chi/v5"
)

type businessRoutes struct {
	businessService service.Business
}

func newBusinessRoutes(r chi.Router, businessService service.Business) {
	br := &businessRoutes{
		businessService: businessService,
	}

	r.Route("/businesses", func(r chi.Router) {
		r.Get("/", br.getAll)
		r.Get("/{businessID}", br.getByID)
		r.Get("/user/{userID}", br.getByUserID)
		r.Get("/{businessID}/owner", br.getOwner)
		r.Put("/{businessID}", br.put)
		r.Patch("/{businessID}", br.patch)
		r.Delete("/{businessID}", br.delete)
	})
}

// @Summary Get all businesses
// @Description Получить список всех бизнесов
// @Tags businesses
// @Accept json
// @Produce json
// @Success 200 {array} models.Business
// @Failure 500 {object} map[string]string
// @Router /businesses [get]
func (br *businessRoutes) getAll(w http.ResponseWriter, r *http.Request) {
	businesses, err := br.businessService.GetBusinesses(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get businesses")
		return
	}

	writeJSON(w, http.StatusOK, businesses)
}

// @Summary Get business by ID
// @Description Получить бизнес по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param businessID path int true "Business ID"
// @Success 200 {object} models.Business
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [get]

func (br *businessRoutes) getByID(w http.ResponseWriter, r *http.Request) {
	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	business, err := br.businessService.GetBusinessByID(r.Context(), businessID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get business by ID")
		return
	}

	writeJSON(w, http.StatusOK, business)
}

// @Summary Get businesses by user ID
// @Description Получить все бизнесы пользователя по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param userID path int true "User ID"
// @Success 200 {array} models.Business
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/user/{userID} [get]
func (br *businessRoutes) getByUserID(w http.ResponseWriter, r *http.Request) {
	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	businesses, err := br.businessService.GetBusinessesByUserID(r.Context(), userID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get businesses by user ID")
		return
	}

	writeJSON(w, http.StatusOK, businesses)
}

// @Summary Get owner of business
// @Description Получить владельца бизнеса по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param businessID path int true "Business ID"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID}/owner [get]
func (br *businessRoutes) getOwner(w http.ResponseWriter, r *http.Request) {
	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	owner, err := br.businessService.GetBusinessOwner(r.Context(), businessID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get business owner")
		return
	}

	writeJSON(w, http.StatusOK, owner)
}

type businessUpdateRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

// @Summary Update business (full)
// @Description Полное обновление бизнеса по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param businessID path int true "Business ID"
// @Param business body businessUpdateRequest true "Business info"
// @Success 200 {object} models.Business
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [put]
func (br *businessRoutes) put(w http.ResponseWriter, r *http.Request) {
	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	var req businessUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		ID:          businessID,
		Name:        req.Name,
		Description: req.Description,
	}

	updatedBusiness, err := br.businessService.PutBusiness(r.Context(), business)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to update business")
		return
	}

	writeJSON(w, http.StatusOK, updatedBusiness)
}

// @Summary Patch business
// @Description Частичное обновление бизнеса по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param businessID path int true "Business ID"
// @Param business body businessUpdateRequest true "Business info"
// @Success 200 {object} models.Business
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [patch]

func (br *businessRoutes) patch(w http.ResponseWriter, r *http.Request) {
	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	var req businessUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	business := models.Business{
		ID:          businessID,
		Name:        req.Name,
		Description: req.Description,
	}

	updatedBusiness, err := br.businessService.PatchBusiness(r.Context(), business)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to patch business")
		return
	}

	writeJSON(w, http.StatusOK, updatedBusiness)
}

// @Summary Delete business
// @Description Удалить бизнес по ID
// @Tags businesses
// @Accept json
// @Produce json
// @Param businessID path int true "Business ID"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [delete]
func (br *businessRoutes) delete(w http.ResponseWriter, r *http.Request) {
	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	err = br.businessService.DeleteBusiness(r.Context(), businessID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to delete business")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"message": "business deleted successfully"})
}
