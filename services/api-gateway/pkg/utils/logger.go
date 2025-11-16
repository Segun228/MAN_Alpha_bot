package utils

import (
	"os"

	"github.com/sirupsen/logrus"
)

type Logger interface {
	Debug(msg string, fields ...map[string]any)
	Info(msg string, fields ...map[string]any)
	Warn(msg string, fields ...map[string]any)
	Error(msg string, fields ...map[string]any)
}

const (
	envLocal = "local"
	envDev   = "dev"
	envProd  = "prod"
)

type logrusLogger struct {
	entry *logrus.Entry
}

func (l *logrusLogger) Debug(msg string, fields ...map[string]any) {
	if len(fields) > 0 {
		l.entry.WithFields(fields[0]).Debug(msg)
	} else {
		l.entry.Debug(msg)
	}
}
func (l *logrusLogger) Info(msg string, fields ...map[string]any) {
	if len(fields) > 0 {
		l.entry.WithFields(fields[0]).Info(msg)
	} else {
		l.entry.Info(msg)
	}
}
func (l *logrusLogger) Warn(msg string, fields ...map[string]any) {
	if len(fields) > 0 {
		l.entry.WithFields(fields[0]).Warn(msg)
	} else {
		l.entry.Warn(msg)
	}
}
func (l *logrusLogger) Error(msg string, fields ...map[string]any) {
	if len(fields) > 0 {
		l.entry.WithFields(fields[0]).Error(msg)
	} else {
		l.entry.Error(msg)
	}
}

func NewLogger(env string) Logger {
	log := logrus.New()
	log.SetOutput(os.Stdout)

	switch env {
	case envLocal:
		log.SetLevel(logrus.DebugLevel)
		log.SetFormatter(&logrus.TextFormatter{
			FullTimestamp: true,
			ForceColors:   true,
		})
	case envDev:
		log.SetLevel(logrus.DebugLevel)
		log.SetFormatter(&logrus.JSONFormatter{})
	case envProd:
		log.SetLevel(logrus.InfoLevel)
		log.SetFormatter(&logrus.JSONFormatter{})
	default:
		log.SetLevel(logrus.DebugLevel)
		log.SetFormatter(&logrus.TextFormatter{FullTimestamp: true})
	}

	return &logrusLogger{entry: logrus.NewEntry(log)}
}
