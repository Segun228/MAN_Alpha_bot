package config

import (
	"fmt"
	"strings"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/spf13/viper"
)

type (
	Config struct {
		Env        string           `mapstructure:"env"`
		HttpServer HttpServerConfig `mapstructure:"http_server"`
		PG         PGConfig         `mapstructure:"pg"`
		Auth       AuthConfig       `maptructure:"auth"`
		Services   ServicesConfig   `mapstructure:"services"`
	}

	HttpServerConfig struct {
		Port         string        `mapstructure:"port"`
		ReadTimeout  time.Duration `mapstructure:"read_timeout"`
		WriteTimeout time.Duration `mapstructutre:"write_timeout"`
		IdleTimeout  time.Duration `mapstructure:"idle_timeout"`
	}

	PGConfig struct {
		Url string `mapstructure:"url"`
	}

	AuthConfig struct {
		JWTSignKey string `mapstructure:"jwt_sign_key"`
	}

	ServicesConfig struct {
	}
)

func NewConfig(path string) (*Config, error) {
	viper.SetConfigFile(path)

	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var cfg Config

	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return &cfg, nil
}

func WatchConfig(onChange func(e fsnotify.Event)) {
	viper.WatchConfig()
	viper.OnConfigChange(onChange)
}
