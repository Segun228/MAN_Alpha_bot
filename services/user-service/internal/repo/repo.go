package repo

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/pgdb"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/postgres"
)

type User interface {
	GetUsers(ctx context.Context) ([]models.User, error)
	GetUserByID(ctx context.Context, userID int) (*models.User, error)
	GetUserByTgID(ctx context.Context, tgID int64) (*models.User, error)
	CreateUser(ctx context.Context, user models.User) (*models.User, error)
	AddBusinessToUser(ctx context.Context, userID int, business models.Business) (*models.User, error)
	UpdateUser(ctx context.Context, user models.User) (*models.User, error)
	DeleteUser(ctx context.Context, userID int) error
}

type Business interface {
	GetBusinesses(ctx context.Context) ([]models.Business, error)
	GetBusinessByID(ctx context.Context, businessID int) (*models.Business, error)
	GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error)
	GetBusinessOwner(ctx context.Context, businessID int) (*models.User, error)
	UpdateBusiness(ctx context.Context, business models.Business) (*models.Business, error)
	DeleteBusiness(ctx context.Context, businessID int) error
}

type Repositories struct {
	User
	Business
}

func NewRepositories(pg *postgres.Postgres) *Repositories {
	return &Repositories{
		User:     pgdb.NewUserRepo(pg),
		Business: pgdb.NewBusinessRepo(pg),
	}
}
