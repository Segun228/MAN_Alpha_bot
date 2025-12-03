package service

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/mocks"
	"github.com/stretchr/testify/assert"
	"go.uber.org/mock/gomock"
	"golang.org/x/crypto/bcrypt"
)

func TestUserService_CreateUser(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockUserRepo := mocks.NewMockUser(ctrl)

	passwordHasher := newHasher()

	userService := NewUserService(mockUserRepo, passwordHasher)

	rawPassword := "Qwerty1!"

	userInput := models.User{
		Login:        "testuser",
		PasswordHash: rawPassword,
		Email:        "test@example.com",
	}

	userToCreate := models.User{
		Login: userInput.Login,
		Email: userInput.Email,
		// PasswordHash будет проверен отдельно
	}

	createdUser := userToCreate
	createdUser.ID = 1
	createdUser.CreatedAt = time.Now()
	createdUser.UpdatedAt = time.Now()

	t.Run("Success - User is created wit hashed password", func(t *testing.T) {
		mockUserRepo.EXPECT().
			CreateUser(gomock.Any(), gomock.Any()).
			DoAndReturn(func(ctx context.Context, user models.User) (*models.User, error) {
				assert.NotEmpty(t, user.PasswordHash, "password hash should not be empty")
				assert.NotEqual(t, rawPassword, user.PasswordHash, "password should be hashed")

				err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(rawPassword))
				assert.NoError(t, err, "hashed password shuld correcpond to the raw password")

				assert.Equal(t, userToCreate.Login, user.Login)
				assert.Equal(t, userToCreate.Email, user.Email)

				createdUser.PasswordHash = user.PasswordHash
				return &createdUser, nil
			}).
			Times(1)

		user, err := userService.CreateUser(context.Background(), userInput)
		assert.NoError(t, err)
		assert.Equal(t, &createdUser, user)
	})

	t.Run("Failure - Repository returns an error", func(t *testing.T) {
		repoError := errors.New("failed to create user")

		mockUserRepo.EXPECT().
			CreateUser(gomock.Any(), gomock.Any()).
			Return(nil, repoError)

		result, err := userService.CreateUser(context.Background(), userInput)

		assert.Nil(t, result)
		assert.Equal(t, repoError, err)
	})
}

func TestUserService_GetUserByID(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockUserRepo := mocks.NewMockUser(ctrl)
	passwordHasher := newHasher()
	userService := NewUserService(mockUserRepo, passwordHasher)

	testUser := &models.User{
		ID:    1,
		Login: "testuser",
	}

	t.Run("Success - User found", func(t *testing.T) {
		mockUserRepo.EXPECT().GetUserByID(gomock.Any(), 1).Return(testUser, nil)

		user, err := userService.GetUserByID(context.Background(), 1)

		assert.NoError(t, err)
		assert.Equal(t, testUser, user)
	})

	t.Run("Failure - User not found", func(t *testing.T) {
		repoErr := errors.New("user not found")
		mockUserRepo.EXPECT().GetUserByID(gomock.Any(), 2).Return(&models.User{}, nil)

		user, err := userService.GetUserByID(context.Background(), 2)

		assert.Empty(t, user)
		assert.Error(t, repoErr, err)
	})
}

func TestUserService_PatchUser(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockUserRepo := mocks.NewMockUser(ctrl)
	passwordHasher := newHasher()
	userService := NewUserService(mockUserRepo, passwordHasher)

	rawPassword := "newPassword"
	existingUser := &models.User{
		ID:           1,
		Login:        "oldLogin",
		PasswordHash: "oldHash",
		Email:        "old@example.com",
	}

	t.Run("Success - Patch login and password", func(t *testing.T) {
		updateData := models.User{
			ID:           1,
			Login:        "newLogin",
			PasswordHash: rawPassword,
		}

		mockUserRepo.EXPECT().GetUserByID(gomock.Any(), 1).Return(existingUser, nil)

		mockUserRepo.EXPECT().
			UpdateUser(gomock.Any(), gomock.Any()).
			DoAndReturn(func(ctx context.Context, updatedUser models.User) (*models.User, error) {
				assert.Equal(t, "newLogin", updatedUser.Login)
				assert.Equal(t, "old@example.com", updatedUser.Email)

				assert.NotEqual(t, rawPassword, updatedUser.PasswordHash)
				assert.NoError(t, bcrypt.CompareHashAndPassword([]byte(updatedUser.PasswordHash), []byte(rawPassword)))

				return &updatedUser, nil
			})

		user, err := userService.PatchUser(context.Background(), updateData)

		assert.NoError(t, err)
		assert.NotNil(t, user)
		assert.Equal(t, "newLogin", user.Login)
		assert.Equal(t, "old@example.com", user.Email)
	})

	t.Run("Failure - User to patch not found", func(t *testing.T) {
		updateData := models.User{
			ID:    2,
			Login: "newLogin",
		}

		repoErr := errors.New("not found")

		mockUserRepo.EXPECT().GetUserByID(gomock.Any(), 2).Return(nil, repoErr)

		user, err := userService.PatchUser(context.Background(), updateData)

		assert.Empty(t, user)
		assert.Error(t, repoErr, err)
	})
}

func TestUserService_DeleteUser(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockUserRepo := mocks.NewMockUser(ctrl)
	passwordHasher := newHasher()
	userService := NewUserService(mockUserRepo, passwordHasher)

	t.Run("Success - User deleted", func(t *testing.T) {
		mockUserRepo.EXPECT().DeleteUser(gomock.Any(), 1).Return(nil)

		err := userService.DeleteUserByID(context.Background(), 1)

		assert.NoError(t, err)
	})
}
