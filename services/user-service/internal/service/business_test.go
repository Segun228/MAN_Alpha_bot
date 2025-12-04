package service

import (
	"context"
	"errors"
	"testing"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/mocks"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"
)

func TestBusinessService_GetBusinessByID(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockBusinessRepo := mocks.NewMockBusiness(ctrl)
	businessService := NewBusinessService(mockBusinessRepo)

	businessID := 1
	expectedBusiness := &models.Business{
		ID:   1,
		Name: "Test",
	}

	t.Run("Success", func(t *testing.T) {
		mockBusinessRepo.EXPECT().GetBusinessByID(gomock.Any(), businessID).Return(expectedBusiness, nil)
		business, err := businessService.GetBusinessByID(context.Background(), businessID)
		assert.NoError(t, err)
		assert.Equal(t, expectedBusiness, business)
	})
}

func TestUserService_AddBusinessToUserID(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockUserRepo := mocks.NewMockUser(ctrl)

	userService := NewUserService(mockUserRepo, nil)

	userID := 1
	businessToAdd := models.Business{
		Name:        "Test Business",
		Description: "A test business",
	}

	t.Run("Success - Add business to user", func(t *testing.T) {
		existingUser := models.User{
			ID:    1,
			Login: "testuser",
		}

		mockUserRepo.EXPECT().AddBusinessToUser(gomock.Any(), userID, businessToAdd).
			DoAndReturn(func(ctx context.Context, id int, business models.Business) (*models.User, error) {
				existingUser.Businesses = append(existingUser.Businesses, business)
				return &existingUser, nil
			})

		updatedUser, err := userService.AddBusinessToUserByID(context.Background(), userID, businessToAdd)

		assert.NoError(t, err)
		require.NotNil(t, updatedUser)
		require.Len(t, updatedUser.Businesses, 1)
		assert.Equal(t, "Test Business", updatedUser.Businesses[0].Name)
	})

	t.Run("Failure - User not found", func(t *testing.T) {
		repoErr := errors.New("user not found")
		mockUserRepo.EXPECT().AddBusinessToUser(gomock.Any(), userID, businessToAdd).Return(nil, repoErr)

		updatedUser, err := userService.AddBusinessToUserByID(context.Background(), userID, businessToAdd)

		assert.Empty(t, updatedUser)
		assert.Equal(t, repoErr, err)
	})
}

func TestBusinessService_GetBusinessesByUserID(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockBusinessRepo := mocks.NewMockBusiness(ctrl)
	businessService := NewBusinessService(mockBusinessRepo)

	userID := 1
	expectedBusinesses := []models.Business{
		{ID: 1, Name: "Business 1"},
		{ID: 2, Name: "Business 2"},
	}

	t.Run("Success", func(t *testing.T) {
		mockBusinessRepo.EXPECT().GetBusinessesByUserID(gomock.Any(), userID).Return(expectedBusinesses, nil)
		businesses, err := businessService.GetBusinessesByUserID(context.Background(), userID)
		assert.NoError(t, err)
		assert.Equal(t, expectedBusinesses, businesses)
	})
}

func TestBusinessesService_PatchBusiness(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockBusinessRepo := mocks.NewMockBusiness(ctrl)
	businessService := NewBusinessService(mockBusinessRepo)

	updateData := models.Business{
		ID:   1,
		Name: "Updated Business",
	}

	existingBusiness := &models.Business{
		ID:          1,
		Name:        "Old Name",
		Description: "Old Description",
	}

	t.Run("Success", func(t *testing.T) {
		mockBusinessRepo.EXPECT().GetBusinessByID(gomock.Any(), updateData.ID).Return(existingBusiness, nil)

		mockBusinessRepo.EXPECT().UpdateBusiness(gomock.Any(), gomock.Any()).Return(&updateData, nil)

		updatedBusiness, err := businessService.PatchBusiness(context.Background(), updateData)

		assert.NoError(t, err)
		assert.Equal(t, &updateData, updatedBusiness)
	})
}

func TestBusinessService_DeleteBusiness(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockBusinessRepo := mocks.NewMockBusiness(ctrl)
	businessService := NewBusinessService(mockBusinessRepo)

	businessID := 1

	t.Run("Success", func(t *testing.T) {
		mockBusinessRepo.EXPECT().DeleteBusiness(gomock.Any(), businessID).Return(nil)
		err := businessService.DeleteBusiness(context.Background(), businessID)
		assert.NoError(t, err)
	})
}
