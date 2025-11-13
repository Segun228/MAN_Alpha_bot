package v1

import (
	"net/http"

	_ "github.com/Segun228/MAN_Alpha_bot/services/user-service/docs"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/go-chi/chi/v5"
	httpSwagger "github.com/swaggo/http-swagger"
)

func NewRouter(services *service.Services) http.Handler {
	r := chi.NewRouter()

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	r.Get("/swagger/*", httpSwagger.WrapHandler)

	r.Route("/v1", func(r chi.Router) {
		newUserRoutes(r, services.User)
		newBusinessRoutes(r, services.Business)
	})

	return r
}
