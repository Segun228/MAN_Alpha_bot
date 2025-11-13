package service

import (
	"context"
	"fmt"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type BusinessService struct {
	businessRepo repo.Business
}

func NewBusinessService(businessRepo repo.Business) *BusinessService {
	return &BusinessService{
		businessRepo: businessRepo,
	}
}

func (s *BusinessService) GetBusinesses(ctx context.Context) ([]models.Business, error) {
	return s.businessRepo.GetBusinesses(ctx)
}

func (s *BusinessService) GetBusinessByID(ctx context.Context, businessID int) (*models.Business, error) {
	return s.businessRepo.GetBusinessByID(ctx, businessID)
}

func (s *BusinessService) GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error) {
	return s.businessRepo.GetBusinessesByUserID(ctx, userID)
}

func (s *BusinessService) GetBusinessOwner(ctx context.Context, businessID int) (*models.User, error) {
	return s.businessRepo.GetBusinessOwner(ctx, businessID)
}

func (s *BusinessService) PutBusiness(ctx context.Context, business models.Business) (*models.Business, error) {
	return s.businessRepo.UpdateBusiness(ctx, business)
}

func (s *BusinessService) PatchBusiness(ctx context.Context, business models.Business) (*models.Business, error) {
	businessFromDB, err := s.businessRepo.GetBusinessByID(ctx, business.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to get business by id: %w", err)
	}

	if business.Name != "" {
		businessFromDB.Name = business.Name
	}
	if business.Description != "" {
		businessFromDB.Description = business.Description
	}

	return s.businessRepo.UpdateBusiness(ctx, business)
}

func (s *BusinessService) DeleteBusiness(ctx context.Context, businessID int) error {
	return s.businessRepo.DeleteBusiness(ctx, businessID)
}
