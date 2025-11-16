package v1

import (
	"net/http"

	_ "github.com/Segun228/MAN_Alpha_bot/services/user-service/docs"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/go-chi/chi/v5"
	httpSwagger "github.com/swaggo/http-swagger"
)

func NewRouter(services *service.Services, logger utils.Logger, botApiKey string) http.Handler {
	r := chi.NewRouter()
	r.Use(loggingMiddleware(logger))

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	r.Get("/swagger/*", httpSwagger.WrapHandler)

	r.Route("/", func(r chi.Router) {
		r.Use(BotAuthMiddleware(botApiKey))
		newUserRoutes(r, services.User, logger)
		newBusinessRoutes(r, services.Business, logger)
		newModelsRoutes(r, services.Models, logger)
	})

	return r
}
