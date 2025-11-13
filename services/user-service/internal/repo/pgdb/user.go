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

type UserRepo struct {
	*postgres.Postgres
}

func NewUserRepo(pg *postgres.Postgres) *UserRepo {
	return &UserRepo{pg}
}

func (r *UserRepo) GetUsers(ctx context.Context) ([]models.User, error) {
	sql, args, _ := r.Builder.
		Select("id, telegram_id, login, email, churned, is_admin, created_at, updated_at").
		From("users").
		ToSql()

	rows, err := r.Pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, err
	}

	var users []models.User
	for rows.Next() {
		var user models.User
		err := rows.Scan(
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
			return nil, err
		}
		users = append(users, user)
	}

	return users, nil
}

func (r *UserRepo) GetUserByID(ctx context.Context, userID int) (*models.User, error) {
	sql, args, _ := r.Builder.
		Select("id, telegram_id, login, password, email, churned, is_admin, created_at, updated_at").
		From("users").
		Where("id = ?", userID).
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
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}
		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &user, nil
}

func (r *UserRepo) GetUserByTgID(ctx context.Context, tgID int64) (*models.User, error) {
	sql, args, _ := r.Builder.
		Select("id, telegram_id, login, password, email, churned, is_admin, created_at, updated_at").
		From("users").
		Where("telegram_id = ?", tgID).
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
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, repoerrors.ErrNotFound
		}
		return nil, fmt.Errorf("failed to scan row: %w", err)
	}

	return &user, nil
}

func (r *UserRepo) CreateUser(ctx context.Context, user models.User) (*models.User, error) {
	sql, args, _ := r.Builder.
		Insert("users").
		Columns("telegram_id", "login", "password", "email", "churned", "is_admin").
		Values(user.TelegramID, user.Login, user.Password, user.Email, user.Churned, user.IsAdmin).
		Suffix("RETURNING id, created_at, updated_at").
		ToSql()

	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.CreatedAt,
		&user.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	return &user, nil
}

func (r *UserRepo) AddBusinessToUserByID(ctx context.Context, userID int, business models.Business) (*models.User, error) {
	sql, args, _ := r.Builder.
		Insert("businesses").
		Columns("name", "description", "user_id").
		Values(business.Name, business.Description, userID).
		Suffix("RETURNING id").
		ToSql()

	err := r.Pool.QueryRow(ctx, sql, args...).Scan(&business.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	user, err := r.GetUserByID(ctx, userID)
	if err != nil {
		return nil, err
	}

	user.Businesses = append(user.Businesses, business)
	return user, nil
}

func (r *UserRepo) AddBusinessToUserByTgID(ctx context.Context, tgId int64, business models.Business) (*models.User, error) {
	user, err := r.GetUserByTgID(ctx, tgId)
	if err != nil {
		return nil, err
	}

	sql, args, _ := r.Builder.
		Insert("businesses").
		Columns("name", "description", "user_id").
		Values(business.Name, business.Description, user.ID).
		Suffix("RETURNING id").
		ToSql()

	err = r.Pool.QueryRow(ctx, sql, args...).Scan(&business.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	user.Businesses = append(user.Businesses, business)
	return user, nil
}

func (r *UserRepo) UpdateUser(ctx context.Context, user models.User) (*models.User, error) {
	sql, args, _ := r.Builder.
		Update("users").
		Set("login", user.Login).
		Set("password", user.Password).
		Set("email", user.Email).
		Set("churned", user.Churned).
		Set("is_admin", user.IsAdmin).
		Where("id = ?", user.ID).
		Suffix("RETURNING updated_at").
		ToSql()

	err := r.Pool.QueryRow(ctx, sql, args...).Scan(&user.UpdatedAt)

	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	return &user, nil
}

func (r *UserRepo) DeleteUserByID(ctx context.Context, userID int) error {
	sql, args, _ := r.Builder.
		Delete("users").
		Where("id = ?", userID).
		ToSql()

	_, err := r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	return nil
}

func (r *UserRepo) DeleteUserByTgID(ctx context.Context, tgID int64) error {
	sql, args, _ := r.Builder.
		Delete("users").
		Where("telegram_id = ?", tgID).
		ToSql()

	_, err := r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	return nil
}
