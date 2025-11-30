package models

import "time"

type Report struct {
	ID        int       `db:"id" json:"id"`
	UserID    int       `db:"user_id" json:"user_id"`
	Name      string    `db:"name" json:"name"`
	Users     int       `db:"users" json:"users"`
	Customers int       `db:"customers" json:"customers"`
	AVP       float64   `db:"avp" json:"avp"`
	APC       int       `db:"apc" json:"apc"`
	TMS       float64   `db:"tms" json:"tms"`
	COGS      float64   `db:"cogs" json:"cogs"`
	COGS1s    float64   `db:"cogs1s" json:"cogs1s"`
	FC        float64   `db:"fc" json:"fc"`
	RR        float64   `db:"rr" json:"rr"`
	AGR       float64   `db:"agr" json:"agr"`
	CreatedAt time.Time `db:"created_at" json:"created_at"`
	UpdatedAt time.Time `db:"updated_at" json:"updated_at"`
}
