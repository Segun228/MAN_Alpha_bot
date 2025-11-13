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

func (br *businessRoutes) getAll(w http.ResponseWriter, r *http.Request) {
	businesses, err := br.businessService.GetBusinesses(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get businesses")
		return
	}

	writeJSON(w, http.StatusOK, businesses)
}

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
