package service

import (
	"fmt"
	"strconv"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/service/serviceerrors"
	"github.com/golang-jwt/jwt/v5"
)

type TokenService struct {
	accessTokenTTL  time.Duration
	refreshTokenTTL time.Duration
	signingKey      string
}

func NewTokenService(accessTokenTTL, refreshTokenTTL time.Duration, signingKey string) *TokenService {
	return &TokenService{
		accessTokenTTL:  accessTokenTTL,
		refreshTokenTTL: refreshTokenTTL,
		signingKey:      signingKey,
	}
}

type Tokens struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

func (s *TokenService) GenerateTokens(userID int) (*Tokens, error) {
	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": fmt.Sprintf("%d", userID),
		"exp": time.Now().Add(s.accessTokenTTL).Unix(),
		"iat": time.Now().Unix(),
	})

	accessTokenString, err := accessToken.SignedString([]byte(s.signingKey))
	if err != nil {
		return nil, err
	}

	refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": fmt.Sprintf("%d", userID),
		"exp": time.Now().Add(s.refreshTokenTTL).Unix(),
		"iat": time.Now().Unix(),
	})

	refreshTokenString, err := refreshToken.SignedString([]byte(s.signingKey))
	if err != nil {
		return nil, err
	}

	return &Tokens{
		AccessToken:  accessTokenString,
		RefreshToken: refreshTokenString,
	}, nil
}

func (s *TokenService) ParseToken(tokenString string) (int, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(s.signingKey), nil
	})

	if err != nil {
		return 0, err
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok || !token.Valid {
		return 0, serviceerrors.ErrInvalidToken
	}

	userID, err := strconv.Atoi(fmt.Sprintf("%.f", claims["sub"]))
	if err != nil {
		return 0, fmt.Errorf("invalid user id in token claims: %v", err)
	}

	return userID, nil
}
