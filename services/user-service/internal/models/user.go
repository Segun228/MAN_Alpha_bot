package models

import "time"

type User struct {
	ID         int       `db:"id"`
	TelegramID int64     `db:"telegram_id"`
	Login      string    `db:"login"`
	Password   string    `db:"password"`
	Email      string    `db:"email"`
	Churned    bool      `db:"churned"`
	IsAdmin    bool      `db:"is_admin"`
	CreatedAt  time.Time `db:"created_at"`
	UpdatedAt  time.Time `db:"updated_at"`

	Businesses []Business `db:"-"`
}
