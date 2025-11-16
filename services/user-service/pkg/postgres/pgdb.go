package postgres

import (
	"context"
	"fmt"
	"time"

	"github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	defaultMaxPoolSize  = 1
	defaultConnAttempts = 10
	defaultConnTimeout  = time.Second
)

type PgxPool interface {
	Close()
	Acquire(ctx context.Context) (*pgxpool.Conn, error)
	Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error)
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
	SendBatch(ctx context.Context, b *pgx.Batch) pgx.BatchResults
	Begin(ctx context.Context) (pgx.Tx, error)
	BeginTx(ctx context.Context, txOptions pgx.TxOptions) (pgx.Tx, error)
	CopyFrom(ctx context.Context, tableName pgx.Identifier, columnNames []string, rowSrc pgx.CopyFromSource) (int64, error)
	Ping(ctx context.Context) error
}

type Postgres struct {
	maxPoolSize  int
	connAttempts int
	connTimeout  time.Duration

	Builder squirrel.StatementBuilderType
	Pool    PgxPool
}

func New(url string, opts ...Option) (*Postgres, error) {
	pg := &Postgres{
		connAttempts: defaultConnAttempts,
		maxPoolSize:  defaultMaxPoolSize,
		connTimeout:  defaultConnTimeout,
	}

	for _, opt := range opts {
		opt(pg)
	}

	pg.Builder = squirrel.StatementBuilder.PlaceholderFormat(squirrel.Dollar)

	poolCfg, err := pgxpool.ParseConfig(url)
	if err != nil {
		return nil, fmt.Errorf("failed to parse pgxpool config: %w", err)
	}

	poolCfg.MaxConns = int32(pg.maxPoolSize)

	connTries := pg.connAttempts

	for pg.connAttempts > 0 {
		pg.Pool, err = pgxpool.NewWithConfig(context.Background(), poolCfg)
		if err == nil {
			break
		}

		time.Sleep(pg.connTimeout)
		pg.connAttempts--
	}

	if err != nil {
		return nil, fmt.Errorf("failed to connect to postgres with %d attempts: %w", connTries, err)
	}

	return pg, nil
}

func (p *Postgres) Close() {
	if p.Pool != nil {
		p.Pool.Close()
	}
}
