package crypto

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type UserCryptoRepo struct {
	Repo      repo.User
	Encrypter Decrypter
}

func NewUserCryptoRepo(repo repo.User, encrypter Decrypter) *UserCryptoRepo {
	return &UserCryptoRepo{
		Repo:      repo,
		Encrypter: encrypter,
	}
}

func (r *UserCryptoRepo) GetUsers(ctx context.Context) ([]models.User, error) {
	users, err := r.Repo.GetUsers(ctx)
	if err != nil {
		return nil, err
	}

	for i := range users {
		users[i].Email, err = r.Encrypter.Decrypt(users[i].Email)
		if err != nil {
			return nil, err
		}

		for j := range users[i].Businesses {
			users[i].Businesses[j].Name, err = r.Encrypter.Decrypt(users[i].Businesses[j].Name)
			if err != nil {
				return nil, err
			}
			users[i].Businesses[j].Description, err = r.Encrypter.Decrypt(users[i].Businesses[j].Description)
			if err != nil {
				return nil, err
			}
		}
	}

	return users, nil
}

func (r *UserCryptoRepo) GetUserIDByTgID(ctx context.Context, tgID int64) (int, error) {
	return r.Repo.GetUserIDByTgID(ctx, tgID)
}

func (r *UserCryptoRepo) GetTgIDByUserID(ctx context.Context, userID int) (int64, error) {
	return r.Repo.GetTgIDByUserID(ctx, userID)
}

func (r *UserCryptoRepo) GetUserByID(ctx context.Context, userID int) (*models.User, error) {
	user, err := r.Repo.GetUserByID(ctx, userID)
	if err != nil {
		return nil, err
	}

	user.Email, err = r.Encrypter.Decrypt(user.Email)
	if err != nil {
		return nil, err
	}

	for i := range user.Businesses {
		user.Businesses[i].Name, err = r.Encrypter.Decrypt(user.Businesses[i].Name)
		if err != nil {
			return nil, err
		}
		user.Businesses[i].Description, err = r.Encrypter.Decrypt(user.Businesses[i].Description)
		if err != nil {
			return nil, err
		}
	}

	return user, nil
}

func (r *UserCryptoRepo) GetUserByLogin(ctx context.Context, login string) (*models.User, error) {
	user, err := r.Repo.GetUserByLogin(ctx, login)
	if err != nil {
		return nil, err
	}

	user.Email, err = r.Encrypter.Decrypt(user.Email)
	if err != nil {
		return nil, err
	}

	for i := range user.Businesses {
		user.Businesses[i].Name, err = r.Encrypter.Decrypt(user.Businesses[i].Name)
		if err != nil {
			return nil, err
		}
		user.Businesses[i].Description, err = r.Encrypter.Decrypt(user.Businesses[i].Description)
		if err != nil {
			return nil, err
		}
	}

	return user, nil
}

func (r *UserCryptoRepo) GetUserByTgID(ctx context.Context, tgID int64) (*models.User, error) {
	user, err := r.Repo.GetUserByTgID(ctx, tgID)
	if err != nil {
		return nil, err
	}

	user.Email, err = r.Encrypter.Decrypt(user.Email)
	if err != nil {
		return nil, err
	}

	for i := range user.Businesses {
		user.Businesses[i].Name, err = r.Encrypter.Decrypt(user.Businesses[i].Name)
		if err != nil {
			return nil, err
		}
		user.Businesses[i].Description, err = r.Encrypter.Decrypt(user.Businesses[i].Description)
		if err != nil {
			return nil, err
		}
	}

	return user, nil
}

func (r *UserCryptoRepo) CreateUser(ctx context.Context, user models.User) (*models.User, error) {
	var err error
	user.Email, err = r.Encrypter.Encrypt(user.Email)
	if err != nil {
		return nil, err
	}

	return r.Repo.CreateUser(ctx, user)
}

func (r *UserCryptoRepo) AddBusinessToUser(ctx context.Context, userID int, business models.Business) (*models.User, error) {
	var err error
	business.Name, err = r.Encrypter.Encrypt(business.Name)
	if err != nil {
		return nil, err
	}
	business.Description, err = r.Encrypter.Encrypt(business.Description)
	if err != nil {
		return nil, err
	}

	return r.Repo.AddBusinessToUser(ctx, userID, business)
}

func (r *UserCryptoRepo) UpdateUser(ctx context.Context, user models.User) (*models.User, error) {
	var err error
	user.Email, err = r.Encrypter.Encrypt(user.Email)
	if err != nil {
		return nil, err
	}

	return r.Repo.UpdateUser(ctx, user)
}

func (r *UserCryptoRepo) DeleteUser(ctx context.Context, userID int) error {
	return r.Repo.DeleteUser(ctx, userID)
}
