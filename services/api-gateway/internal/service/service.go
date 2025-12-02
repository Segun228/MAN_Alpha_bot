package service

import "time"

type Token interface {
	GenerateTokens(userID int) (*Tokens, error)
	ParseToken(tokenString string) (int, error)
}

type Services struct {
	Token
}

type ServicesDependencies struct {
	AccessTokenTTL  time.Duration
	RefreshTokenTTL time.Duration
	SigningKey      string
}

func NewServices(deps *ServicesDependencies) *Services {
	return &Services{
		Token: NewTokenService(deps.AccessTokenTTL, deps.RefreshTokenTTL, deps.SigningKey),
	}
}
