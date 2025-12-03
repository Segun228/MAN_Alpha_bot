package app

import (
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/config"
	v1 "github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/controller/http/v1"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/httpserver"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/metrics"
	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/fsnotify/fsnotify"
	"github.com/go-chi/chi"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/sirupsen/logrus"
)

// @title           Api Gateway
// @version         1.0
func Run(configPath string) {
	var cfgMutex sync.RWMutex

	// Configuration
	cfg, err := config.NewConfig(configPath)
	if err != nil {
		logrus.Fatalf("Config error: %s", err)
	}

	// Logger
	log := utils.NewLogger(cfg.Env)

	// Config watching
	go config.WatchConfig(func(e fsnotify.Event) {
		log.Info("config gile changed, reloading...", logrus.Fields{"file": e.Name})

		cfgMutex.Lock()
		reloadedCfg, err := config.NewConfig(configPath)
		if err != nil {
			log.Error("error updating config", logrus.Fields{"error": err})
			return
		}

		cfg = reloadedCfg
		cfgMutex.Unlock()

		log = utils.NewLogger(reloadedCfg.Env)
		log.Info("config reloaded successfully")
	})

	// Reading actual config
	cfgMutex.RLock()
	srvCfg := cfg.HttpServer
	authCfg := cfg.Auth
	servicesCfg := cfg.Services
	securityCfg := cfg.Security
	cfgMutex.RUnlock()

	// Prometheus metrics
	reg := prometheus.NewRegistry()
	m := metrics.NewMetrics(reg)

	// Chi router
	log.Info("initializing router...")
	router := chi.NewRouter()

	deps := service.ServicesDependencies{
		AccessTokenTTL:  authCfg.AccessTokenTTL,
		RefreshTokenTTL: authCfg.RefreshTokenTTL,
		SigningKey:      authCfg.SigningKey,
	}

	services := service.NewServices(&deps)
	v1.NewRouter(router, services, m, log, srvCfg.AllowedOrigins, authCfg.BotKey, servicesCfg, securityCfg.DefenderCheck.Enabled)

	// HTTP Server
	log.Info("starting http server...")
	log.Debug("server", logrus.Fields{"port": cfg.HttpServer.Port})
	httpServer := httpserver.New(
		router,
		httpserver.Port(srvCfg.Port),
		httpserver.ReadTimeout(srvCfg.ReadTimeout),
		httpserver.WriteTimeout(srvCfg.WriteTimeout),
		httpserver.IdleTimeout(srvCfg.IdleTimeout),
	)

	// Waiting signal
	log.Info("configuring gracefull shuttdown...")
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt, syscall.SIGTERM)

	select {
	case s := <-interrupt:
		log.Info("catched interrupt signal", logrus.Fields{"signal": s.String()})
	case err = <-httpServer.Notify():
		log.Error("catched http server notify signal", logrus.Fields{"error": err})
	}

	// Gracefull shutdown
	log.Info("shutting down service...")
	if err = httpServer.Shutdown(); err != nil {
		log.Error("failed to shut http server down", logrus.Fields{"error": err})
	}
}
