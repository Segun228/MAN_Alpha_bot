package v1

import (
	"encoding/json"
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
)

type modelsRoutes struct {
	modelsService service.Models
	logger        utils.Logger
}

func newModelsRoutes(r chi.Router, modelsService service.Models, logger utils.Logger) {
	mr := &modelsRoutes{
		modelsService: modelsService,
		logger:        logger,
	}

	r.Route("/models", func(rt chi.Router) {
		rt.Post("/chat", mr.chat)
		rt.Post("/docs", mr.docs)

		rt.Post("/summarize/text", mr.summarizeText)
		rt.Post("/summarize/dialog", mr.summarizeDialog)

		rt.Post("/recomendations", mr.recomendations)

		rt.Post("/analyzer/swot", mr.analyze("swot-analysis"))
		rt.Post("/analyzer/cjm", mr.analyze("customer-journey-map"))
		rt.Post("/analyzer/bmc", mr.analyze("bmc"))
		rt.Post("/analyzer/vpc", mr.analyze("vpc"))
		rt.Post("/analyzer/pest", mr.analyze("pest"))
	})
}

func (mr *modelsRoutes) chat(w http.ResponseWriter, r *http.Request) {
	var req service.AskChatModelRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	resp, err := mr.modelsService.AskChatModel(r.Context(), req)
	if err != nil {
		mr.logger.Error("error asking chat model", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, resp)
}

func (mr *modelsRoutes) docs(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Question string `json:"question"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	resp, err := mr.modelsService.AskDocsMode(r.Context(), req.Question)
	if err != nil {
		mr.logger.Error("error asking docs model", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, resp)
}

func (mr *modelsRoutes) summarizeText(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Text string `json:"text"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	summary, err := mr.modelsService.AskSummarizerFirst(r.Context(), req.Text)
	if err != nil {
		mr.logger.Error("error summarizing text", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"summary": summary})
}

func (mr *modelsRoutes) summarizeDialog(w http.ResponseWriter, r *http.Request) {
	var req service.SummarizerSecondRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	summary, err := mr.modelsService.AskSummarizerSecond(r.Context(), req)
	if err != nil {
		mr.logger.Error("error summarizing dialog", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"summary": summary})
}

func (mr *modelsRoutes) recomendations(w http.ResponseWriter, r *http.Request) {
	var req service.UniversalRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	recs, err := mr.modelsService.AskRecsModel(r.Context(), req)
	if err != nil {
		mr.logger.Error("error getting recomendations", map[string]any{
			"error": err.Error(),
		})
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"recomendations": recs})
}

func (mr *modelsRoutes) analyze(method string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req service.UniversalRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}

		analysis, err := mr.modelsService.AskAnalyzer(r.Context(), req, method)
		if err != nil {
			mr.logger.Error("error getting analysis", map[string]any{
				"method": method,
				"error":  err.Error(),
			})
			writeError(w, http.StatusInternalServerError, "internal server error")
			return
		}

		writeJSON(w, http.StatusOK, map[string]string{"analysis": analysis})
	}
}
