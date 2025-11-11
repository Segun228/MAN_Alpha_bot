package v1

import (
	"log/slog"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func NewRouter(r *chi.Mux, logger utils.Logger, allowedOrigins []string, jwtSecret string, botSecretKey string) {
	auth := NewAuth([]byte(jwtSecret), []byte(botSecretKey))

	r.Use(LoggingMiddleware(logger))
	r.Use(RecoveryMiddleware(logger))
	r.Use(CORSMiddleware(allowedOrigins))
	r.Use(PrometheusMiddleware)

	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Gateway is running"))
	})

	r.Handle("/metrics", promhttp.Handler())

	// TODO: add real proxy servers when main services will be ready
	r.Route("/api", func(api chi.Router) {
		// Setting up public routes
		api.Mount("/bot", botRoutes())

		// Setting up protected routes
		api.Group(func(protected chi.Router) {
			protected.Use(auth.Middleware(logger))

			api.Mount("/users", userRoutes())
		})
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

func createReverseProxy(targetURL string) *httputil.ReverseProxy {
	remote, err := url.Parse(targetURL)
	if err != nil {
		slog.Error("failed to parse target url", "url", targetURL, "error", err)
		os.Exit(1)
	}

	return httputil.NewSingleHostReverseProxy(remote)
}
