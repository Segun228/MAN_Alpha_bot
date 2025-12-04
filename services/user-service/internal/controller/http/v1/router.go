package v1

import (
	"fmt"
	"net/http"

	_ "github.com/Segun228/MAN_Alpha_bot/services/user-service/docs"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/broker"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	httpSwagger "github.com/swaggo/http-swagger"
)

func NewRouter(services *service.Services, logger utils.Logger, logsBroker broker.MessageBroker, botApiKey, env string) http.Handler {
	r := chi.NewRouter()
	r.Use(loggingMiddleware(logger, logsBroker, env))

	r.Handle("/metrics", promhttp.Handler())

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	r.Get("/swagger/*", httpSwagger.WrapHandler)

	newAuthRoutes(r, services.Auth, services.User, logger)

	r.Route("/", func(r chi.Router) {
		r.Use(TrustedSerciceMiddleware(botApiKey, logger))

		newUserRoutes(r, services.User, logger)
		newBusinessRoutes(r, services.Business, services.User, logger)
		newReportRoutes(r, services.Reports, services.User, logger)
	})

	return r
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
