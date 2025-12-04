package v1

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/controller/http/v1/logkeys"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
)

type businessRoutes struct {
	businessService service.Business
	userService     service.User
	logger          utils.Logger
}

func newBusinessRoutes(r chi.Router, businessService service.Business, userService service.User, logger utils.Logger) {
	br := &businessRoutes{
		businessService: businessService,
		userService:     userService,
		logger:          logger,
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
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_get_all"
		metricsPtr.Level = "INFO"
	}

	businesses, err := br.businessService.GetBusinesses(r.Context())
	if err != nil {
		br.logger.Error("error getting businesses", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get businesses"
		}

		writeError(w, http.StatusInternalServerError, "failed to get businesses")
		return
	}

	if ok {
		metricsPtr.Message = "success"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [get]

func (br *businessRoutes) getByID(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_get_by_id"
		metricsPtr.Level = "INFO"
	}

	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		br.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get business by ID"
		}

		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	business, err := br.businessService.GetBusinessByID(r.Context(), businessID)
	if err != nil {
		if ok {
			metricsPtr.Level = "ERROR"
		}

		switch err {
		case repoerrors.ErrNotFound:
			if ok {
				metricsPtr.Message = "business not found"
			}

			writeError(w, http.StatusNotFound, "business not found")
			return
		default:
			br.logger.Error("error getting business by id", map[string]any{
				"error": err.Error(),
			})

			if ok {
				metricsPtr.Message = "failed to get business by ID"
			}

			writeError(w, http.StatusInternalServerError, "failed to get business by ID")
			return
		}
	}

	tgId, err := br.userService.GetTgIDByUserID(r.Context(), business.UserID)
	if err != nil {
		br.logger.Error("error getting tg_id", map[string]any{
			"error": err.Error(),
		})
		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get tg_id"
		}
	}

	if ok {
		metricsPtr.UserID = business.UserID
		metricsPtr.TelegramID = strconv.Itoa(int(tgId))
		metricsPtr.Message = "business found"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/user/{userID} [get]
func (br *businessRoutes) getByUserID(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_get_by_user_id"
		metricsPtr.Level = "INFO"
	}

	userIDParam := chi.URLParam(r, "userID")
	userID, err := parseIDParam(userIDParam)
	if err != nil {
		br.logger.Error("error parsing user_id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to parse user ID"
		}

		writeError(w, http.StatusBadRequest, "invalid user ID")
		return
	}

	businesses, err := br.businessService.GetBusinessesByUserID(r.Context(), userID)
	if err != nil {
		if ok {
			metricsPtr.Level = "ERROR"
		}

		switch err {
		case repoerrors.ErrOwnerNotFound:
			if ok {
				metricsPtr.Message = "owner not found"
			}

			writeError(w, http.StatusNotFound, "owner not found")
			return
		default:
			br.logger.Error("error getting businesses by user_id", map[string]any{
				"error": err.Error(),
			})
			if ok {
				metricsPtr.Message = "failed to get businesses by user ID"
			}
			writeError(w, http.StatusInternalServerError, "failed to get businesses by user ID")
			return
		}
	}

	tgId, err := br.userService.GetTgIDByUserID(r.Context(), userID)
	if err != nil {
		br.logger.Error("error getting tg_id", map[string]any{
			"error": err.Error(),
		})
		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get tg_id"
		}
	}

	if ok {
		metricsPtr.UserID = userID
		metricsPtr.TelegramID = strconv.Itoa(int(tgId))
		metricsPtr.Message = "businesses found"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID}/owner [get]
func (br *businessRoutes) getOwner(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_get_owner"
		metricsPtr.Level = "INFO"
	}

	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		br.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to parse business ID"
		}

		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	owner, err := br.businessService.GetBusinessOwner(r.Context(), businessID)
	if err != nil {
		if ok {
			metricsPtr.Level = "ERROR"
		}

		switch err {
		case repoerrors.ErrNotFound:
			if ok {
				metricsPtr.Message = "business not found"
			}
			writeError(w, http.StatusNotFound, "business not found")
			return
		default:
			br.logger.Error("error getting business owner", map[string]any{
				"error": err.Error(),
			})
			if ok {
				metricsPtr.Message = "failed to get business owner"
			}
			writeError(w, http.StatusInternalServerError, "failed to get business owner")
			return
		}
	}

	tgId, err := br.userService.GetTgIDByUserID(r.Context(), owner.ID)
	if err != nil {
		br.logger.Error("error getting tg_id", map[string]any{
			"error": err.Error(),
		})
		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get tg_id"
		}
	}

	if ok {
		metricsPtr.UserID = owner.ID
		metricsPtr.TelegramID = strconv.Itoa(int(tgId))
		metricsPtr.Message = "business owner found"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [put]
func (br *businessRoutes) put(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_put"
		metricsPtr.Level = "INFO"
	}

	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		br.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to parse business ID"
		}

		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	var req businessUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		br.logger.Error("error updating business", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to update business"
		}

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
		if ok {
			metricsPtr.Level = "ERROR"
		}
		switch err {
		case repoerrors.ErrNotFound:
			if ok {
				metricsPtr.Message = "business not found"
			}
			writeError(w, http.StatusNotFound, "business not found")
			return
		default:
			br.logger.Error("error updating business", map[string]any{
				"error": err.Error(),
			})

			if ok {
				metricsPtr.Message = "failed to update business"
			}

			writeError(w, http.StatusInternalServerError, "failed to update business")
			return
		}
	}

	tgId, err := br.userService.GetTgIDByUserID(r.Context(), updatedBusiness.UserID)
	if err != nil {
		br.logger.Error("error getting tg_id", map[string]any{
			"error": err.Error(),
		})
		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get tg_id"
		}
	}

	if ok {
		metricsPtr.UserID = updatedBusiness.UserID
		metricsPtr.TelegramID = strconv.Itoa(int(tgId))
		metricsPtr.Message = "business updated"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [patch]

func (br *businessRoutes) patch(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_patch"
		metricsPtr.Level = "INFO"
	}

	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		br.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to parse business ID"
		}

		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	var req businessUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		br.logger.Error("error decoding request body", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to decode request body"
		}

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
		if ok {
			metricsPtr.Level = "ERROR"
		}

		switch err {
		case repoerrors.ErrNotFound:
			if ok {
				metricsPtr.Message = "business not found"
			}
			writeError(w, http.StatusNotFound, "business not found")
			return
		default:
			br.logger.Error("error patching business", map[string]any{
				"error": err.Error(),
			})

			if ok {
				metricsPtr.Message = "failed to patch business"
			}

			writeError(w, http.StatusInternalServerError, "failed to patch business")
			return
		}
	}

	tgId, err := br.userService.GetTgIDByUserID(r.Context(), updatedBusiness.UserID)
	if err != nil {
		br.logger.Error("error getting tg_id", map[string]any{
			"error": err.Error(),
		})
		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to get tg_id"
		}
	}

	if ok {
		metricsPtr.UserID = updatedBusiness.UserID
		metricsPtr.TelegramID = strconv.Itoa(int(tgId))
		metricsPtr.Message = "business patched"
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
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /businesses/{businessID} [delete]
func (br *businessRoutes) delete(w http.ResponseWriter, r *http.Request) {
	metricsPtrVal := r.Context().Value(logkeys.LogMetricsKey)
	metricsPtr, ok := metricsPtrVal.(*logkeys.LogMetrics)

	if ok {
		metricsPtr.Action = "businesses_delete"
		metricsPtr.Level = "INFO"
	}

	businessIDParam := chi.URLParam(r, "businessID")
	businessID, err := parseIDParam(businessIDParam)
	if err != nil {
		br.logger.Error("error parsing id", map[string]any{
			"error": err.Error(),
		})

		if ok {
			metricsPtr.Level = "ERROR"
			metricsPtr.Message = "failed to parse business ID"
		}

		writeError(w, http.StatusBadRequest, "invalid business ID")
		return
	}

	err = br.businessService.DeleteBusiness(r.Context(), businessID)
	if err != nil {
		if ok {
			metricsPtr.Level = "ERROR"
		}
		switch err {
		case repoerrors.ErrNotFound:
			if ok {
				metricsPtr.Message = "business not found"
			}

			writeError(w, http.StatusNotFound, "business not found")
			return
		default:
			br.logger.Error("error deleting businesses", map[string]any{
				"error": err.Error(),
			})

			if ok {
				metricsPtr.Message = "failed to delete business"
			}

			writeError(w, http.StatusInternalServerError, "failed to delete business")
			return
		}
	}

	if ok {
		metricsPtr.Message = "business deleted"
	}

	writeJSON(w, http.StatusOK, map[string]string{"message": "business deleted successfully"})
}
