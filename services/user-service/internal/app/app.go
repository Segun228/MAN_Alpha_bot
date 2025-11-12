package app

import (
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/config"
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

	// Waiting signal
	log.Info("configuring gracefull shuttdown...")
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt, syscall.SIGTERM)

	select {
	case s := <-interrupt:
		log.Info("catched interrupt signal", logrus.Fields{"signal": s.String()})
	}
}
