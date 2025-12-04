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
	defer rows.Close()

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

func (r *UserRepo) GetUserIDByTgID(ctx context.Context, tgID int64) (int, error) {
	sql, args, _ := r.Builder.
		Select("id").
		From("users").
		Where("telegram_id = ?", tgID).
		ToSql()

	var id int
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(&id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return 0, repoerrors.ErrNotFound
		}
		return 0, fmt.Errorf("failed to scan row: %w", err)
	}

	return id, nil
}

func (r *UserRepo) GetTgIDByUserID(ctx context.Context, userID int) (int64, error) {
	sql, args, _ := r.Builder.
		Select("telegram_id").
		From("users").
		Where("id = ?", userID).
		ToSql()

	var tgID int64
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(&tgID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return 0, repoerrors.ErrNotFound
		}
		return 0, fmt.Errorf("failed to scan row: %w", err)
	}

	return tgID, nil
}

func (r *UserRepo) GetUserByID(ctx context.Context, userID int) (*models.User, error) {
	sql, args, _ := r.Builder.
		Select("id, telegram_id, login, password_hash, email, churned, is_admin, created_at, updated_at").
		From("users").
		Where("id = ?", userID).
		ToSql()

	user := models.User{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.TelegramID,
		&user.Login,
		&user.PasswordHash,
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

	sql, args, _ = r.Builder.
		Select("id, name, description, user_id").
		From("businesses").
		Where("user_id = ?", user.ID).
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

	user.Businesses = businesses

	return &user, nil
}

func (r *UserRepo) GetUserByLogin(ctx context.Context, login string) (*models.User, error) {
	sql, args, _ := r.Builder.
		Select("id, telegram_id, login, password_hash, email, churned, is_admin, created_at, updated_at").
		From("users").
		Where("login = ?", login).
		ToSql()

	user := models.User{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.TelegramID,
		&user.Login,
		&user.PasswordHash,
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
		Select("id, telegram_id, login, email, password_hash, churned, is_admin, created_at, updated_at").
		From("users").
		Where("telegram_id = ?", tgID).
		ToSql()

	user := models.User{}
	err := r.Pool.QueryRow(ctx, sql, args...).Scan(
		&user.ID,
		&user.TelegramID,
		&user.Login,
		&user.Email,
		&user.PasswordHash,
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

	sql, args, _ = r.Builder.
		Select("id, name, description, user_id").
		From("businesses").
		Where("user_id = ?", user.ID).
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

	user.Businesses = businesses

	return &user, nil
}

func (r *UserRepo) CreateUser(ctx context.Context, user models.User) (*models.User, error) {
	sql, args, _ := r.Builder.
		Insert("users").
		Columns("telegram_id", "login", "password_hash", "email", "churned", "is_admin").
		Values(user.TelegramID, user.Login, user.PasswordHash, user.Email, user.Churned, user.IsAdmin).
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

func (r *UserRepo) AddBusinessToUser(ctx context.Context, userID int, business models.Business) (*models.User, error) {
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
		Insert("businesses").
		Columns("name", "description", "user_id").
		Values(business.Name, business.Description, userID).
		Suffix("RETURNING id").
		ToSql()

	err = r.Pool.QueryRow(ctx, sql, args...).Scan(&business.ID)
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

func (r *UserRepo) UpdateUser(ctx context.Context, user models.User) (*models.User, error) {
	checkUserSql, checkUserArgs, _ := r.Builder.
		Select("id").
		From("users").
		Where("id = ?", user.ID).
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
		Update("users").
		Set("login", user.Login).
		Set("password_hash", user.PasswordHash).
		Set("email", user.Email).
		Set("churned", user.Churned).
		Set("is_admin", user.IsAdmin).
		Where("id = ?", user.ID).
		Suffix("RETURNING telegram_id, updated_at").
		ToSql()

	err = r.Pool.QueryRow(ctx, sql, args...).Scan(&user.TelegramID, &user.UpdatedAt)

	if err != nil {
		return nil, fmt.Errorf("failed to execute sql request: %w", err)
	}

	return &user, nil
}

func (r *UserRepo) DeleteUser(ctx context.Context, userID int) error {
	checkUserSql, checkUserArgs, _ := r.Builder.
		Select("id").
		From("users").
		Where("id = ?", userID).
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
		Delete("users").
		Where("id = ?", userID).
		ToSql()

	_, err = r.Pool.Exec(ctx, sql, args...)
	if err != nil {
		return fmt.Errorf("failed to execute sql request: %w", err)
	}

	return nil
}
