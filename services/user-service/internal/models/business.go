package models

type Business struct {
	ID          int    `db:"id" json:"id"`
	Name        string `db:"name" json:"name"`
	Description string `db:"description" json:"description"`
	UserID      int    `db:"user_id" json:"user_id"`
}
