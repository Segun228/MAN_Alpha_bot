package models

type Business struct {
	ID          int    `db:"id"`
	Name        string `db:"name"`
	Description string `db:"description"`
	UserID      int    `db:"user_id"`
}
