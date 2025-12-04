package models

import "time"

type Log struct {
	Timestamp       time.Time `json:"timestamp"`
	TraceID         string    `json:"trace_id"`
	UserID          int       `json:"user_id"`
	IsAuthenticated bool      `json:"is_authenticated"`
	TelegramID      string    `json:"telegram_id"`
	Platform        string    `json:"platform"`
	Action          string    `json:"action"`
	RequestMethod   string    `json:"request_method"`
	RequestBody     string    `json:"request_body"`
	ResponseCode    int       `json:"response_code"`
	Level           string    `json:"level"`
	EventType       string    `json:"event_type"`
	Source          string    `json:"source"`
	Env             string    `json:"env"`
	Message         string    `json:"message"`
}
