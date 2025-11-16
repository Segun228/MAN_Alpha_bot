package app

import (
	"errors"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/golang-migrate/migrate/v4"
	// migrate tools
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
)

const (
	defaultAttempts = 20
	defaultTimeout  = time.Second
)

func runMigrations(pgUrl string) {
	var (
		attempts = defaultAttempts
		err      error
		m        *migrate.Migrate
	)

	for attempts > 0 {
		m, err = migrate.New("file://./migrations", pgUrl)
		if err == nil {
			break
		}

		log.Printf("Migrate: pgdb is trying to connect, attempts left: %d", attempts)
		time.Sleep(defaultTimeout)
		attempts--
	}

	if err != nil {
		log.Fatalf("Migrate: pgdb connect error: %s", err)
	}

	err = m.Up()
	defer func() { _, _ = m.Close() }()
	if err != nil && !errors.Is(err, migrate.ErrNoChange) {
		log.Fatalf("Migrate: up error: %s", err)
	}

	if errors.Is(err, migrate.ErrNoChange) {
		log.Printf("Migrate: no change")
		return
	}

	log.Printf("Migrate: up success")
}
