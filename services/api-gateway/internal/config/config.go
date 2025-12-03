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
		Auth       AuthConfig       `maptructure:"auth"`
		Services   ServicesConfig   `mapstructure:"services"`
		Security   SecutrityConfig  `mapstructure:"security"`
	}

	HttpServerConfig struct {
		Port           string        `mapstructure:"port"`
		ReadTimeout    time.Duration `mapstructure:"read_timeout"`
		WriteTimeout   time.Duration `mapstructutre:"write_timeout"`
		IdleTimeout    time.Duration `mapstructure:"idle_timeout"`
		AllowedOrigins []string      `mapstructure:"allowed_origins"`
	}

	AuthConfig struct {
		AccessTokenTTL  time.Duration `mapstructure:"access_token_ttl"`
		RefreshTokenTTL time.Duration `mapstructure:"refresh_token_ttl"`
		SigningKey      string        `mapstructure:"jwt_sign_key"`
		BotKey          string        `mapstructure:"bot_key"`
	}

	ServicesConfig struct {
		UserServiceURL      string `mapstructure:"user_service_url"`
		ChatModelURL        string `mapstructure:"chat_model_url"`
		DocsModelURL        string `mapstructure:"docs_model_url"`
		RecomendatorURL     string `mapstructure:"recomendator_url"`
		SummarizerURL       string `mapstructure:"summarizer_url"`
		BusinessAnalyzerURL string `mapstructure:"business_analyzer_url"`
		DefenderURL         string `mapstructure:"defender_url"`
		DBServiceURL        string `mapstructure:"db_service_url"`
		EmailServiceURL     string `mapstructure:"email_service_url"`
		ModelServiceURL     string `mapstructure:"model_service_url"`
		SpeechServiceURL    string `mapstrcture:"speech_service_url"`
	}

	SecutrityConfig struct {
		DefenderCheck DefenderCheckConfig `mapstructure:"defender_check"`
	}

	DefenderCheckConfig struct {
		Enabled bool `mapstructure:"enabled"`
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
