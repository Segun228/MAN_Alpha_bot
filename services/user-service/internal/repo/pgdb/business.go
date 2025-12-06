package pgdb

import (
	"context"
	"errors"
	"fmt"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/postgres"
	"github.com/jackc/pgx/v5"
)

type BusinessRepo struct {
	*postgres.Postgres
}

func NewBusinessRepo(pg *postgres.Postgres) *BusinessRepo {
	return &BusinessRepo{pg}
}

func (r *BusinessRepo) GetBusinesses(ctx context.Context) ([]models.Business, error) {
	sql, args, _ := r.Builder.
		Select("id, name, description, user_id").
		From("businesses").
		ToSql()

	rows, err := r.Pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query row: %w", err)
	}
	defer rows.Close()

	var businesses []models.Business
	for rows.Next() {
		var business models.Business
		err := rows.Scan(
			&business.ID,
			&business.Name,
			&business.Description,
			&business.UserID,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		businesses = append(businesses, business)
	}

	return businesses, nil
}

func (r *BusinessRepo) GetBusinessByID(ctx context.Context, businessID int) (*models.Business, error) {
	sql, args, _ := r.Builder.
		Select("id, name, description, user_id").
		From("businesses").
		Where("id = ?", businessID).
		ToSql()

	business := models.Business{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&business.ID,
		&business.Name,
		&business.Description,
		&business.UserID,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}

		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &business, nil
}

func (r *BusinessRepo) GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error) {
	checkUserSql, checkUserArgs, _ := r.Builder.
		Select("id").
		From("users").
		Where("id = ?", userID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkUserSql, checkUserArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrOwnerNotFound
		}
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	sql, args, _ := r.Builder.
		Select("id, name, description, user_id").
		From("businesses").
		Where("user_id = ?", userID).
		ToSql()

	rows, err := r.Pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query row: %w", err)
	}
	defer rows.Close()

	var businesses []models.Business
	for rows.Next() {
		var business models.Business
		err := rows.Scan(
			&business.ID,
			&business.Name,
			&business.Description,
			&business.UserID,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		businesses = append(businesses, business)
	}

	return businesses, nil
}

func (r *BusinessRepo) GetBusinessOwner(ctx context.Context, businessID int) (*models.User, error) {
	sql, args, _ := r.Builder.
		Select("u.id, u.telegram_id, u.login, u.email, u.churned, u.is_admin, u.created_at, u.updated_at").
		From("users u").
		Join("businesses b ON u.id = b.user_id").
		Where("b.id = ?", businessID).
		ToSql()

	user := models.User{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.TelegramID,
		&user.Login,
		&user.Email,
		&user.Churned,
		&user.IsAdmin,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}

		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &user, nil
}

func (r *BusinessRepo) UpdateBusiness(ctx context.Context, business models.Business) (*models.Business, error) {
	checkUserSql, checkUserArgs, _ := r.Builder.
		Select("id").
		From("businesses").
		Where("id = ?", business.ID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkUserSql, checkUserArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	sql, args, _ := r.Builder.
		Update("businesses").
		Set("name", business.Name).
		Set("description", business.Description).
		Where("id = ?", business.ID).
		ToSql()

	_, err = r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	return &business, nil
}

func (r *BusinessRepo) DeleteBusiness(ctx context.Context, businessID int) error {
	checkUserSql, checkUserArgs, _ := r.Builder.
		Select("id").
		From("businesses").
		Where("id = ?", businessID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, checkUserSql, checkUserArgs...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return repoerrors.ErrNotFound
		}
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	sql, args, _ := r.Builder.
		Delete("businesses").
		Where("id = ?", businessID).
		ToSql()

	_, err = r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	return nil
}
