package models

import "time"

type User struct {
	ID         int       `db:"id" json:"id"`
	TelegramID int64     `db:"telegram_id" json:"telegram_id"`
	Login      string    `db:"login" json:"login"`
	Password   string    `db:"password" json:"password"`
	Email      string    `db:"email" json:"email"`
	Churned    bool      `db:"churned" json:"churned"`
	IsAdmin    bool      `db:"is_admin" json:"is_admin"`
	CreatedAt  time.Time `db:"created_at" json:"created_at"`
	UpdatedAt  time.Time `db:"updated_at" json:"updated_at"`

	Businesses []Business `db:"-" json:"businesses"`
}
