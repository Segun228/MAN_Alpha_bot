package crypto

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type BusinessCryptoRepo struct {
	Repo      repo.Business
	Encrypter Decrypter
}

func NewBusinessCryptoRepo(repo repo.Business, encrypter Decrypter) *BusinessCryptoRepo {
	return &BusinessCryptoRepo{
		Repo:      repo,
		Encrypter: encrypter,
	}
}

func (r *BusinessCryptoRepo) GetBusinesses(ctx context.Context) ([]models.Business, error) {
	businesses, err := r.Repo.GetBusinesses(ctx)
	if err != nil {
		return nil, err
	}

	for i := range businesses {
		businesses[i].Name, err = r.Encrypter.Decrypt(businesses[i].Name)
		if err != nil {
			return nil, err
		}
		businesses[i].Description, err = r.Encrypter.Decrypt(businesses[i].Description)
		if err != nil {
			return nil, err
		}
	}

	return businesses, nil
}

func (r *BusinessCryptoRepo) GetBusinessByID(ctx context.Context, businessID int) (*models.Business, error) {
	business, err := r.Repo.GetBusinessByID(ctx, businessID)
	if err != nil {
		return nil, err
	}

	business.Name, err = r.Encrypter.Decrypt(business.Name)
	if err != nil {
		return nil, err
	}
	business.Description, err = r.Encrypter.Decrypt(business.Description)
	if err != nil {
		return nil, err
	}

	return business, nil
}

func (r *BusinessCryptoRepo) GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error) {
	businesses, err := r.Repo.GetBusinessesByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}

	for i := range businesses {
		businesses[i].Name, err = r.Encrypter.Decrypt(businesses[i].Name)
		if err != nil {
			return nil, err
		}
		businesses[i].Description, err = r.Encrypter.Decrypt(businesses[i].Description)
		if err != nil {
			return nil, err
		}
	}

	return businesses, nil
}

func (r *BusinessCryptoRepo) GetBusinessOwner(ctx context.Context, businessID int) (*models.User, error) {
	user, err := r.Repo.GetBusinessOwner(ctx, businessID)
	if err != nil {
		return nil, err
	}

	user.Email, err = r.Encrypter.Decrypt(user.Email)
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (r *BusinessCryptoRepo) UpdateBusiness(ctx context.Context, business models.Business) (*models.Business, error) {
	var err error
	business.Name, err = r.Encrypter.Encrypt(business.Name)
	if err != nil {
		return nil, err
	}
	business.Description, err = r.Encrypter.Encrypt(business.Description)
	if err != nil {
		return nil, err
	}

	return r.Repo.UpdateBusiness(ctx, business)
}

func (r *BusinessCryptoRepo) DeleteBusiness(ctx context.Context, businessID int) error {
	return r.Repo.DeleteBusiness(ctx, businessID)
}
