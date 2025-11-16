package pgdb

import (
	"context"
	"fmt"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/postgres"
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
		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &business, nil
}

func (r *BusinessRepo) GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error) {
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
		Select("u.id, u.telegram_id, u.login, u.password, u.email, u.churned, u.is_admin, u.created_at, u.updated_at").
		From("users u").
		Join("businesses b ON u.id = b.user_id").
		Where("b.id = ?", businessID).
		ToSql()

	user := models.User{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.TelegramID,
		&user.Login,
		&user.Password,
		&user.Email,
		&user.Churned,
		&user.IsAdmin,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &user, nil
}

func (r *BusinessRepo) UpdateBusiness(ctx context.Context, business models.Business) (*models.Business, error) {
	sql, args, _ := r.Builder.
		Update("businesses").
		Set("name", business.Name).
		Set("description", business.Description).
		Where("id = ?", business.ID).
		ToSql()

	_, err := r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	return &business, nil
}

func (r *BusinessRepo) DeleteBusiness(ctx context.Context, businessID int) error {
	sql, args, _ := r.Builder.
		Delete("businesses").
		Where("id = ?", businessID).
		ToSql()

	_, err := r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	return nil
}
