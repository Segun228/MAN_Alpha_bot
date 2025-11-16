package v1

import (
	"log/slog"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/config"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/metrics"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func NewRouter(r *chi.Mux, m *metrics.Metrics, logger utils.Logger, allowedOrigins []string, botSecretKey string, servicesConfig config.ServicesConfig) {
	r.Use(CORSMiddleware(allowedOrigins))
	r.Use(LoggingMiddleware(logger))
	r.Use(RecoveryMiddleware(logger))
	r.Use(PrometheusMiddleware(m))
	r.Use(BotAuthMiddleware(botSecretKey))

	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Gateway is running"))
	})

	r.Handle("/metrics", promhttp.Handler())

	r.Route("/api", func(api chi.Router) {
		api.Mount("/users", createProfixedHandler("/api/users", servicesConfig.UserServiceURL))
	})
}

func createProfixedHandler(prefix, targetURL string) http.Handler {
	remote, err := url.Parse(targetURL)
	if err != nil {
		slog.Error("failed to parse target url", "url", targetURL, "error", err)
		os.Exit(1)
	}

	proxy := httputil.NewSingleHostReverseProxy(remote)

	return http.StripPrefix(prefix, proxy)
}
