package service

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/hasher"
	"golang.org/x/crypto/bcrypt"
)

type AuthService struct {
	userRepo repo.User
	hasher   hasher.PasswordHasher
}

func NewAuthService(userRepo repo.User, hasher hasher.PasswordHasher) *AuthService {
	return &AuthService{
		userRepo: userRepo,
		hasher:   hasher,
	}
}

func (s *AuthService) VerifyUserCredentials(ctx context.Context, login, password string) (int, error) {
	user, err := s.userRepo.GetUserByLogin(ctx, login)
	if err != nil {
		return 0, err
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password))
	if err != nil {
		return 0, ErrInvalidCredentials
	}

	return user.ID, nil
}
