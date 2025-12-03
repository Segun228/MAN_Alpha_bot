package v1

import (
	"encoding/json"
	"net/http"

	_ "github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
)

type reportRoutes struct {
	reportService service.Reports
	logger        utils.Logger
}

func newReportRoutes(r chi.Router, reportService service.Reports, logger utils.Logger) {
	rr := &reportRoutes{
		reportService: reportService,
		logger:        logger,
	}

	r.Route("/reports", func(r chi.Router) {
		r.Get("/", rr.getAll)
		r.Get("/{reportID}", rr.getByID)
		r.Get("/tg/{tgID}", rr.getByUserTgID)
		r.Post("/", rr.create)
		r.Post("/tg/{tgID}", rr.createWithTg)
		r.Put("/{reportID}", rr.put)
		r.Patch("/{reportID}", rr.patch)
		r.Delete("/{reportID}", rr.delete)
	})
}

// @Summary Get all reports
// @Description Получить список всех отчетов
// @Tags reports
// @Accept json
// @Produce json
// @Success 200 {array} models.Report
// @Failure 500 {object} map[string]string
// @Router /reports [get]
func (rr *reportRoutes) getAll(w http.ResponseWriter, r *http.Request) {
	reports, err := rr.reportService.GetReports(r.Context())
	if err != nil {
		rr.logger.Error("error getting reports", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "failed to get reports")
		return
	}

	writeJSON(w, http.StatusOK, reports)
}

// @Summary Get report by ID
// @Description Получить отчет по ID
// @Tags reports
// @Accept json
// @Produce json
// @Param reportID path int true "ID отчета"
// @Success 200 {object} models.Report
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/{reportID} [get]

func (rr *reportRoutes) getByID(w http.ResponseWriter, r *http.Request) {
	reportIDParam := chi.URLParam(r, "reportID")
	reportID, err := parseIDParam(reportIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid reportID param")
		return
	}

	report, err := rr.reportService.GetReportByID(r.Context(), reportID)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "report not found")
			return
		default:
			rr.logger.Error("error getting report by ID", map[string]any{
				"report_id": reportID,
				"error":     err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to get report by ID")
			return
		}
	}

	writeJSON(w, http.StatusOK, report)
}

// @Summary Get reports by user Telegram ID
// @Description Получить все отчеты пользователя по Telegram ID
// @Tags reports
// @Accept json
// @Produce json
// @Param tgID path int64 true "Telegram User ID"
// @Success 200 {array} models.Report
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/tg/{tgID} [get]
func (rr *reportRoutes) getByUserTgID(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgID")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid tgID param")
		return
	}

	reports, err := rr.reportService.GetReportsByTgID(r.Context(), tgID)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "user not found")
			return
		default:
			rr.logger.Error("error getting reports by user tgID", map[string]any{
				"tg_id": tgID,
				"error": err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to get reports by user tgID")
			return
		}
	}

	writeJSON(w, http.StatusOK, reports)
}

type reportCreateRequest struct {
	UserID    int     `json:"user_id"`
	Name      string  `json:"name"`
	Users     int     `json:"users"`
	Customers int     `json:"customers"`
	AVP       float64 `json:"avp"`
	APC       int     `json:"apc"`
	TMS       float64 `json:"tms"`
	COGS      float64 `json:"cogs"`
	COGS1s    float64 `json:"cogs1s"`
	FC        float64 `json:"fc"`
	RR        float64 `json:"rr"`
	AGR       float64 `json:"agr"`
}

// @Summary Create a new report
// @Description Создать новый отчет
// @Tags reports
// @Accept json
// @Produce json
// @Param report body reportCreateRequest true "Report to create"
// @Success 201 {object} models.Report
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports [post]
func (rr *reportRoutes) create(w http.ResponseWriter, r *http.Request) {
	var req reportCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		rr.logger.Error("error decoding create report request", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	report := service.ReportCreateInput{
		UserID:    req.UserID,
		Name:      req.Name,
		Users:     req.Users,
		Customers: req.Customers,
		AVP:       req.AVP,
		APC:       req.APC,
		TMS:       req.TMS,
		COGS:      req.COGS,
		COGS1s:    req.COGS1s,
		FC:        req.FC,
		RR:        req.RR,
		AGR:       req.AGR,
	}

	createdReport, err := rr.reportService.CreateReport(r.Context(), report)
	if err != nil {
		switch err {
		case repoerrors.ErrOwnerNotFound:
			writeError(w, http.StatusBadRequest, "user not found")
			return
		default:
			rr.logger.Error("error creating report", map[string]any{
				"error": err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to create report")
			return
		}
	}

	writeJSON(w, http.StatusCreated, createdReport)
}

// @Summary Create a new report with Telegram ID
// @Description Создать новый отчет, используя Telegram ID пользователя
// @Tags reports
// @Accept json
// @Produce json
// @Param tgID path int64 true "Telegram User ID"
// @Param report body reportCreateRequest true "Report to create"
// @Success 201 {object} models.Report
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/tg/{tgID} [post]
func (rr *reportRoutes) createWithTg(w http.ResponseWriter, r *http.Request) {
	tgIDParam := chi.URLParam(r, "tgID")
	tgID, err := parseTgIDParam(tgIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid tgID param")
		return
	}

	var req reportCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		rr.logger.Error("error decoding create report with tgID request", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	report := service.ReportCreateInput{
		Name:      req.Name,
		Users:     req.Users,
		Customers: req.Customers,
		AVP:       req.AVP,
		APC:       req.APC,
		TMS:       req.TMS,
		COGS:      req.COGS,
		COGS1s:    req.COGS1s,
		FC:        req.FC,
		RR:        req.RR,
		AGR:       req.AGR,
	}

	createdReport, err := rr.reportService.CreateReportWithTgID(r.Context(), tgID, report)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "user not found")
			return
		case repoerrors.ErrOwnerNotFound:
			writeError(w, http.StatusBadRequest, "user not found")
			return
		default:
			rr.logger.Error("error creating report with tgID", map[string]any{
				"tg_id": tgID,
				"error": err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to create report")
			return
		}
	}

	writeJSON(w, http.StatusCreated, createdReport)
}

type reportUpdateRequest struct {
	Name      *string  `json:"name,omitempty"`
	Users     *int     `json:"users,omitempty"`
	Customers *int     `json:"customers,omitempty"`
	AVP       *float64 `json:"avp,omitempty"`
	APC       *int     `json:"apc,omitempty"`
	TMS       *float64 `json:"tms,omitempty"`
	COGS      *float64 `json:"cogs,omitempty"`
	COGS1s    *float64 `json:"cogs1s,omitempty"`
	FC        *float64 `json:"fc,omitempty"`
	RR        *float64 `json:"rr,omitempty"`
	AGR       *float64 `json:"agr,omitempty"`
}

// @Summary Update report by ID (full)
// @Description Обновить отчет по ID
// @Tags reports
// @Accept json
// @Produce json
// @Param reportID path int true "ID отчета"
// @Param report body reportUpdateRequest true "Report fields to update"
// @Success 200 {object} models.Report
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/{reportID} [patch]
func (rr *reportRoutes) patch(w http.ResponseWriter, r *http.Request) {
	reportIDParam := chi.URLParam(r, "reportID")
	reportID, err := parseIDParam(reportIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid reportID param")
		return
	}

	var req reportUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	report := service.ReportUpdateInput{
		ID: reportID,
	}

	if req.Name != nil {
		report.Name = *req.Name
	}
	if req.Users != nil {
		report.Users = *req.Users
	}
	if req.Customers != nil {
		report.Customers = *req.Customers
	}
	if req.AVP != nil {
		report.AVP = *req.AVP
	}
	if req.APC != nil {
		report.APC = *req.APC
	}
	if req.TMS != nil {
		report.TMS = *req.TMS
	}
	if req.COGS != nil {
		report.COGS = *req.COGS
	}
	if req.COGS1s != nil {
		report.COGS1s = *req.COGS1s
	}
	if req.FC != nil {
		report.FC = *req.FC
	}
	if req.RR != nil {
		report.RR = *req.RR
	}
	if req.AGR != nil {
		report.AGR = *req.AGR
	}

	updatedReport, err := rr.reportService.PatchReport(r.Context(), report)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "report not found")
			return
		default:
			rr.logger.Error("error updating report", map[string]any{
				"report_id": reportID,
				"error":     err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to update report")
			return
		}
	}

	writeJSON(w, http.StatusOK, updatedReport)
}

// @Summary Patch report by ID (partial)
// @Description Частичное обновление отчета по ID
// @Tags reports
// @Accept json
// @Produce json
// @Param reportID path int true "ID отчета"
// @Param report body reportUpdateRequest true "Report fields to update"
// @Success 200 {object} models.Report
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/{reportID} [put]
func (rr *reportRoutes) put(w http.ResponseWriter, r *http.Request) {
	reportIDParam := chi.URLParam(r, "reportID")
	reportID, err := parseIDParam(reportIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid reportID param")
		return
	}

	var req reportUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	report := service.ReportUpdateInput{
		ID: reportID,
	}

	if req.Name != nil {
		report.Name = *req.Name
	}
	if req.Users != nil {
		report.Users = *req.Users
	}
	if req.Customers != nil {
		report.Customers = *req.Customers
	}
	if req.AVP != nil {
		report.AVP = *req.AVP
	}
	if req.APC != nil {
		report.APC = *req.APC
	}
	if req.TMS != nil {
		report.TMS = *req.TMS
	}
	if req.COGS != nil {
		report.COGS = *req.COGS
	}
	if req.COGS1s != nil {
		report.COGS1s = *req.COGS1s
	}
	if req.FC != nil {
		report.FC = *req.FC
	}
	if req.RR != nil {
		report.RR = *req.RR
	}
	if req.AGR != nil {
		report.AGR = *req.AGR
	}

	updatedReport, err := rr.reportService.PatchReport(r.Context(), report)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "report not found")
			return
		default:
			rr.logger.Error("error updating report", map[string]any{
				"report_id": reportID,
				"error":     err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to update report")
			return
		}
	}

	writeJSON(w, http.StatusOK, updatedReport)
}

// @Summary Delete report by ID
// @Description Удалить отчет по ID
// @Tags reports
// @Accept json
// @Produce json
// @Param reportID path int true "ID отчета"
// @Success 204
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /reports/{reportID} [delete]
func (rr *reportRoutes) delete(w http.ResponseWriter, r *http.Request) {
	reportIDParam := chi.URLParam(r, "reportID")
	reportID, err := parseIDParam(reportIDParam)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid reportID param")
		return
	}

	err = rr.reportService.DeleteReport(r.Context(), reportID)
	if err != nil {
		switch err {
		case repoerrors.ErrNotFound:
			writeError(w, http.StatusNotFound, "report not found")
			return
		default:
			rr.logger.Error("error deleting report", map[string]any{
				"report_id": reportID,
				"error":     err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "failed to delete report")
			return
		}
	}

	writeJSON(w, http.StatusNoContent, "success")
}
