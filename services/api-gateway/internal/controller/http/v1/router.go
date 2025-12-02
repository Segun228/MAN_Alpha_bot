package v1

import (
	"log/slog"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"

	_ "github.com/Segun228/MAN_Alpha_bot/services/api-gateway/docs"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/config"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/metrics"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	httpSwagger "github.com/swaggo/http-swagger"
)

func NewRouter(r *chi.Mux, services *service.Services, m *metrics.Metrics, logger utils.Logger, allowedOrigins []string, botSecretKey string, servicesConfig config.ServicesConfig) {
	r.Use(CORSMiddleware(allowedOrigins))
	r.Use(loggingMiddleware(logger))
	r.Use(RecoveryMiddleware(logger))
	r.Use(PrometheusMiddleware(m))

	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Gateway is running"))
	})

	r.Handle("/metrics", promhttp.Handler())

	r.Get("/swagger/*", httpSwagger.WrapHandler)

	r.Route("/auth", func(auth chi.Router) {
		newAuthRoutes(auth, services.Token, logger, servicesConfig.UserServiceURL)
	})

	r.Route("/api", func(api chi.Router) {
		api.Use(HybridAuthMiddleware(services.Token, logger, botSecretKey))

		api.Mount("/users", createProfixedHandler("/api/users", servicesConfig.UserServiceURL))
	})

	r.Route("/models", func(models chi.Router) {
		models.Mount("/chat", createProfixedHandler("/models/chat", servicesConfig.ChatModelURL))
		models.Mount("/docs", createProfixedHandler("/models/docs", servicesConfig.DocsModelURL))
		models.Mount("/summarizer", createProfixedHandler("/models/summarizer", servicesConfig.SummarizerURL))
		models.Mount("/defender", createProfixedHandler("/models/defender", servicesConfig.DefenderURL))
		models.Mount("/recomendator", createProfixedHandler("/models/recomendator", servicesConfig.RecomendatorURL))
		models.Mount("/business_analyzer", createProfixedHandler("/models/business_analyzer", servicesConfig.BusinessAnalyzerURL))
	})

	r.Route("/utils", func(u chi.Router) {
		u.Mount("/db", createProfixedHandler("/utils/db", servicesConfig.DBServiceURL))
		u.Mount("/email", createProfixedHandler("/utils/email", servicesConfig.EmailServiceURL))
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
