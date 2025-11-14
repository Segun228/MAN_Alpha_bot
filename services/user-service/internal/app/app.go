package app

import (
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/config"
	v1 "github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/controller/http/v1"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/service"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/httpserver"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/postgres"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
	"github.com/fsnotify/fsnotify"
	"github.com/sirupsen/logrus"
)

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

	log.Info("Initializing postgres...")
	pg, err := postgres.New(cfg.PG.Url)
	if err != nil {
		logrus.Fatal(err)
	}
	defer pg.Close()

	runMigrations(cfg.PG.Url)

	log.Info("init repos")
	repositories := repo.NewRepositories(pg)

	deps := service.ServicesDependencies{
		Repos: repositories,
	}
	services := service.NewServices(&deps)

	handler := v1.NewRouter(services, log, cfg.Auth.BotKey)

	httpServer := httpserver.New(handler, httpserver.Port("8083"))

	// Waiting signal
	log.Info("configuring gracefull shuttdown...")
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt, syscall.SIGTERM)

	select {
	case s := <-interrupt:
		log.Info("catched interrupt signal", logrus.Fields{"signal": s.String()})
	case err = <-httpServer.Notify():
		log.Error("http server notify error", logrus.Fields{"error": err})
	}

	err = httpServer.Shutdown()
	if err != nil {
		log.Error("http server shutdown error", logrus.Fields{"error": err})
	}
}
