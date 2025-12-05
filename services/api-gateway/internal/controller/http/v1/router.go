package v1

import (
	"log/slog"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"

	_ "github.com/Segun228/MAN_Alpha_bot/services/api-gateway/docs"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/config"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/metrics"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/go-chi/chi"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	httpSwagger "github.com/swaggo/http-swagger"
)

func NewRouter(r *chi.Mux, services *service.Services, m *metrics.Metrics, logger utils.Logger, allowedOrigins []string, botSecretKey string, servicesConfig config.ServicesConfig, defenderEnabled bool) {
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

	newAuthRoutes(r, services.Token, logger, servicesConfig.UserServiceURL)

	r.Route("/api", func(api chi.Router) {
		api.Use(HybridAuthMiddleware(services.Token, logger, botSecretKey))

		api.Mount("/users", createProfixedHandler("/api/users", servicesConfig.UserServiceURL))
	})

	r.Route("/models", func(models chi.Router) {
		models.Use(DefenderCheckMiddleware(defenderEnabled, servicesConfig.DefenderURL, logger))

		models.Mount("/chat", createProfixedHandler("/models/chat", servicesConfig.ChatModelURL))
		models.Mount("/docs", createProfixedHandler("/models/docs", servicesConfig.DocsModelURL))
		models.Mount("/recomendator", createProfixedHandler("/models/recomendator", servicesConfig.RecomendatorURL))
		models.Mount("/summarizer", createProfixedHandler("/models/summarizer", servicesConfig.SummarizerURL))
		models.Mount("/business_analyzer", createProfixedHandler("/models/business_analyzer", servicesConfig.BusinessAnalyzerURL))
		models.Mount("/defender", createProfixedHandler("/models/defender", servicesConfig.DefenderURL))
		models.Mount("/speech", createProfixedHandler("/models/speech", servicesConfig.SpeechServiceURL))
		models.Mount("/model", createProfixedHandler("/models/model", servicesConfig.ModelServiceURL))
	})

	r.Route("/utils", func(u chi.Router) {
		u.Use(HybridAuthMiddleware(services.Token, logger, botSecretKey))

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

	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)

		userID, ok := req.Context().Value(userIDKey).(int)
		if ok {
			req.Header.Set("X-User-ID", strconv.Itoa(userID))
		}

		req.Header.Del("Authorization")
	}

	return http.StripPrefix(prefix, proxy)
}
