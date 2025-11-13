package service

import (
	"context"
	"fmt"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type UserService struct {
	userRepo repo.User
}

func NewUserService(userRepo repo.User) *UserService {
	return &UserService{
		userRepo: userRepo,
	}
}

func (s *UserService) GetUsers(ctx context.Context) ([]models.User, error) {
	return s.userRepo.GetUsers(ctx)
}

func (s *UserService) GetUserByID(ctx context.Context, userID int) (*models.User, error) {
	return s.userRepo.GetUserByID(ctx, userID)
}

func (s *UserService) GetUserByTgID(ctx context.Context, tgID int64) (*models.User, error) {
	return s.userRepo.GetUserByTgID(ctx, tgID)
}

func (s *UserService) CreateUser(ctx context.Context, user models.User) (*models.User, error) {
	return s.userRepo.CreateUser(ctx, user)
}

func (s *UserService) AddBusinessToUserByID(ctx context.Context, userID int, business models.Business) (*models.User, error) {
	return s.userRepo.AddBusinessToUser(ctx, userID, business)
}

func (s *UserService) AddBusinessToUserByTgID(ctx context.Context, tgId int64, business models.Business) (*models.User, error) {
	user, err := s.userRepo.GetUserByTgID(ctx, tgId)
	if err != nil {
		return nil, fmt.Errorf("failed to get user by tg id: %w", err)
	}

	return s.userRepo.AddBusinessToUser(ctx, user.ID, business)
}

func (s *UserService) PutUserByID(ctx context.Context, user models.User) (*models.User, error) {
	return s.userRepo.UpdateUser(ctx, user)
}

func (s *UserService) PutUserByTgID(ctx context.Context, tgID int64, user models.User) (*models.User, error) {
	userFromDB, err := s.userRepo.GetUserByTgID(ctx, tgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user by tg id: %w", err)
	}

	user.ID = userFromDB.ID
	return s.userRepo.UpdateUser(ctx, user)
}

func (s *UserService) PatchUser(ctx context.Context, user models.User) (*models.User, error) {
	userFromDB, err := s.userRepo.GetUserByID(ctx, user.ID)
	if err != nil {
		return nil, err
	}

	if user.Login != "" {
		userFromDB.Login = user.Login
	}

	if user.Password != "" {
		userFromDB.Password = user.Password
	}

	if user.Email != "" {
		userFromDB.Email = user.Email
	}

	if user.Churned != userFromDB.Churned {
		userFromDB.Churned = user.Churned
	}

	if user.IsAdmin != userFromDB.IsAdmin {
		userFromDB.IsAdmin = user.IsAdmin
	}

	return s.userRepo.UpdateUser(ctx, *userFromDB)
}

func (s *UserService) DeleteUserByID(ctx context.Context, userID int) error {
	return s.userRepo.DeleteUser(ctx, userID)
}

func (s *UserService) DeleteUserByTgID(ctx context.Context, tgID int64) error {
	user, err := s.userRepo.GetUserByTgID(ctx, tgID)
	if err != nil {
		return fmt.Errorf("failed to get user by tg id: %w", err)
	}

	return s.userRepo.DeleteUser(ctx, user.ID)
}
