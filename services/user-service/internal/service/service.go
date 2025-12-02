package service

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/hasher"
)

type UserCreateInput struct {
	TelegramID int64
	Login      string
	Password   string
	Email      string
}

type UserUpdateInput struct {
	ID         int
	TelegramID int64

	Login    string
	Password string
	Email    string
	Churned  bool
	IsAdmin  bool
}

type User interface {
	GetUsers(ctx context.Context) ([]models.User, error)
	GetUserByID(ctx context.Context, userID int) (*models.User, error)
	GetUserByTgID(ctx context.Context, tgID int64) (*models.User, error)
	CreateUser(ctx context.Context, user models.User) (*models.User, error)
	AddBusinessToUserByID(ctx context.Context, userID int, business models.Business) (*models.User, error)
	AddBusinessToUserByTgID(ctx context.Context, tgId int64, business models.Business) (*models.User, error)
	PutUserByID(ctx context.Context, user models.User) (*models.User, error)
	PutUserByTgID(ctx context.Context, tgID int64, user models.User) (*models.User, error)
	PatchUser(ctx context.Context, user models.User) (*models.User, error)
	DeleteUserByID(ctx context.Context, userID int) error
	DeleteUserByTgID(ctx context.Context, tgID int64) error
}

type BusinessCreateInput struct {
	Name        string
	Description string
	UserID      int
}

type BusinessUpdateInput struct {
	ID          int
	Name        string
	Description string
}

type Business interface {
	GetBusinesses(ctx context.Context) ([]models.Business, error)
	GetBusinessByID(ctx context.Context, businessID int) (*models.Business, error)
	GetBusinessesByUserID(ctx context.Context, userID int) ([]models.Business, error)
	GetBusinessOwner(ctx context.Context, businessID int) (*models.User, error)
	PutBusiness(ctx context.Context, business models.Business) (*models.Business, error)
	PatchBusiness(ctx context.Context, business models.Business) (*models.Business, error)
	DeleteBusiness(ctx context.Context, businessID int) error
}

type ReportCreateInput struct {
	UserID    int
	Name      string
	Users     int
	Customers int
	AVP       float64
	APC       int
	TMS       float64
	COGS      float64
	COGS1s    float64
	FC        float64
	RR        float64
	AGR       float64
}

type ReportUpdateInput struct {
	ID        int
	UserID    int
	Name      string
	Users     int
	Customers int
	AVP       float64
	APC       int
	TMS       float64
	COGS      float64
	COGS1s    float64
	FC        float64
	RR        float64
	AGR       float64
}

type Reports interface {
	GetReports(ctx context.Context) ([]models.Report, error)
	GetReportByID(ctx context.Context, reportID int) (*models.Report, error)
	GetReportsByTgID(ctx context.Context, tgID int64) ([]models.Report, error)
	CreateReport(ctx context.Context, report ReportCreateInput) (*models.Report, error)
	CreateReportWithTgID(ctx context.Context, tgID int64, report ReportCreateInput) (*models.Report, error)
	PutReport(ctx context.Context, report ReportUpdateInput) (*models.Report, error)
	PathcReport(ctx context.Context, report ReportUpdateInput) (*models.Report, error)
	DeleteReport(ctx context.Context, reportID int) error
}

type Auth interface {
	VerifyUserCredentials(ctx context.Context, login, password string) (int, error)
}

type Services struct {
	User
	Business
	Reports
	Auth
}

type ServicesDependencies struct {
	Repos  *repo.Repositories
	Hasher hasher.PasswordHasher
}

func NewServices(deps *ServicesDependencies) *Services {
	return &Services{
		User:     NewUserService(deps.Repos.User, deps.Hasher),
		Business: NewBusinessService(deps.Repos.Business),
		Reports:  NewReportsService(deps.Repos.Reports, deps.Repos.User),
		Auth:     NewAuthService(deps.Repos.User, deps.Hasher),
	}
}
