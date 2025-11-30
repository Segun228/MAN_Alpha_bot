package pgdb

import (
	"context"
	"errors"

	"github.com/Masterminds/squirrel"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/postgres"
	"github.com/jackc/pgx/v5"
)

type ReportsRepo struct {
	*postgres.Postgres
}

func NewReportsRepo(pg *postgres.Postgres) *ReportsRepo {
	return &ReportsRepo{pg}
}

func (r *ReportsRepo) GetReports(ctx context.Context) ([]models.Report, error) {
	sql, args, _ := r.Builder.
		Select("id, user_id, name, users, customers, avp, apc, tms, cogs, cogs1s, fc, rr, agr, created_at, updated_at").
		From("reports").
		ToSql()

	rows, err := r.Pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var reports []models.Report
	for rows.Next() {
		var report models.Report
		err := rows.Scan(
			&report.ID,
			&report.UserID,
			&report.Name,
			&report.Users,
			&report.Customers,
			&report.AVP,
			&report.APC,
			&report.TMS,
			&report.COGS,
			&report.COGS1s,
			&report.FC,
			&report.RR,
			&report.AGR,
			&report.CreatedAt,
			&report.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		reports = append(reports, report)
	}

	return reports, nil
}

func (r *ReportsRepo) GetReportByID(ctx context.Context, reportID int) (*models.Report, error) {
	sql, args, _ := r.Builder.
		Select("id, user_id, name, users, customers, avp, apc, tms, cogs, cogs1s, fc, rr, agr, created_at, updated_at").
		From("reports").
		Where("id = ?", reportID).
		ToSql()

	row := r.Pool.QueryRow(ctx, sql, args...)

	var report models.Report
	err := row.Scan(
		&report.ID,
		&report.UserID,
		&report.Name,
		&report.Users,
		&report.Customers,
		&report.AVP,
		&report.APC,
		&report.TMS,
		&report.COGS,
		&report.COGS1s,
		&report.FC,
		&report.RR,
		&report.AGR,
		&report.CreatedAt,
		&report.UpdatedAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}
		return nil, err
	}

	return &report, nil
}

func (r *ReportsRepo) CreateReport(ctx context.Context, report models.Report) (*models.Report, error) {
	checkSql, checkArgs, _ := r.Builder.
		Select("id").
		From("users").
		Where("id = ?", report.UserID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkSql, checkArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrOwnerNotFound
		}
		return nil, err
	}

	sql, args, _ := r.Builder.
		Insert("reports").
		Columns("user_id", "name", "users", "customers", "avp", "apc", "tms", "cogs", "cogs1s", "fc", "rr", "agr").
		Values(report.UserID, report.Name, report.Users, report.Customers, report.AVP, report.APC, report.TMS, report.COGS, report.COGS1s, report.FC, report.RR, report.AGR).
		Suffix("RETURNING id, created_at, updated_at").
		ToSql()
	err = r.Pool.QueryRow(ctx, sql, args...).Scan(
		&report.ID,
		&report.CreatedAt,
		&report.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	return &report, nil
}

func (r *ReportsRepo) UpdateReport(ctx context.Context, report models.Report) (*models.Report, error) {
	checkSql, checkArgs, _ := r.Builder.
		Select("id").
		From("users").
		Where("id = ?", report.UserID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkSql, checkArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrOwnerNotFound
		}
		return nil, err
	}

	sql, args, _ := r.Builder.
		Update("reports").
		Set("name", report.Name).
		Set("users", report.Users).
		Set("customers", report.Customers).
		Set("avp", report.AVP).
		Set("apc", report.APC).
		Set("tms", report.TMS).
		Set("cogs", report.COGS).
		Set("cogs1s", report.COGS1s).
		Set("fc", report.FC).
		Set("rr", report.RR).
		Set("agr", report.AGR).
		Set("updated_at", squirrel.Expr("NOW()")).
		Where("id = ?", report.ID).
		Suffix("RETURNING updated_at").
		ToSql()
	err = r.Pool.QueryRow(ctx, sql, args...).Scan(&report.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}

		return nil, err
	}

	return &report, nil
}

func (r *ReportsRepo) DeleteReport(ctx context.Context, reportID int) error {
	checkSql, checkArgs, _ := r.Builder.
		Select("id").
		From("reports").
		Where("id = ?", reportID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkSql, checkArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return repoerrors.ErrNotFound
		}
		return err
	}

	sql, args, _ := r.Builder.
		Delete("reports").
		Where("id = ?", reportID).
		ToSql()

	_, err = r.Pool.Exec(ctx, sql, args...)
	return err
}
