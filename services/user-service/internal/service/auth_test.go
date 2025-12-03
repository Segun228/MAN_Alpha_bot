package service

import (
	"context"
	"testing"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/mocks"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/repoerrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/hasher"
	"github.com/stretchr/testify/assert"
	"go.uber.org/mock/gomock"
	"golang.org/x/crypto/bcrypt"
)

func hashPassword(password string) string {
	bytes, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes)
}

type bcryptHasher struct{}

func newHasher() hasher.PasswordHasher {
	return &bcryptHasher{}
}

func (h *bcryptHasher) Hash(password string) (string, error) {
	hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hashedBytes), nil
}

func TestUserService_VerifyUserCredentials(t *testing.T) {
	login := "testuser"
	correctPassword := "Qwerty1!"
	incorrectPassword := "wrongpassword"

	hashedPassword := hashPassword(correctPassword)
	expectedUserID := 1

	testUser := &models.User{
		ID:           expectedUserID,
		Login:        login,
		PasswordHash: hashedPassword,
		Email:        "test@example.com",
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	ctrl := gomock.NewController(t)

	mockUserRepo := mocks.NewMockUser(ctrl)
	passwordHasher := newHasher()

	authService := NewAuthService(mockUserRepo, passwordHasher)

	testCases := []struct {
		name          string
		login         string
		password      string
		mockSetup     func()
		expectedID    int
		expectedError error
	}{
		{
			name:     "valid credentials",
			login:    login,
			password: correctPassword,
			mockSetup: func() {
				mockUserRepo.EXPECT().GetUserByLogin(gomock.Any(), login).Return(testUser, nil)
			},
			expectedID:    expectedUserID,
			expectedError: nil,
		},
		{
			name:     "incorrect password",
			login:    login,
			password: incorrectPassword,
			mockSetup: func() {
				mockUserRepo.EXPECT().GetUserByLogin(gomock.Any(), login).Return(testUser, nil)
			},
			expectedID:    0,
			expectedError: ErrInvalidCredentials,
		},
		{
			name:     "user not found",
			login:    login,
			password: correctPassword,
			mockSetup: func() {
				mockUserRepo.EXPECT().GetUserByLogin(gomock.Any(), login).Return(nil, repoerrors.ErrNotFound)
			},
			expectedID:    0,
			expectedError: repoerrors.ErrNotFound,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			tc.mockSetup()

			userID, err := authService.VerifyUserCredentials(context.Background(), tc.login, tc.password)

			assert.Equal(t, tc.expectedID, userID)
			assert.Equal(t, tc.expectedError, err)
		})
	}
}
