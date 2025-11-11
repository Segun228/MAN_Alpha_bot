package v1

import (
	"net/http"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
)

func NewRouter(r *chi.Mux, logger utils.Logger, allowedOrigins []string) {
	r.Use(LoggingMiddleware(logger))
	r.Use(RecoveryMiddleware(logger))
	r.Use(CORSMiddleware(allowedOrigins))
	r.Use(PrometheusMiddleware)

	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Gateway is running"))
	})

	r.Route("/api", func(api chi.Router) {
		api.Mount("/users", userRoutes())
		api.Mount("/bot", botRoutes())
	})
}

func userRoutes() http.Handler {
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("User endpoint placeholder"))
	})

	return r
}

func botRoutes() http.Handler {
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Bot endpoint placeholder"))
	})

	return r
}
