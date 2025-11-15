package service

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
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

type Models interface {
	AskChatModel(ctx context.Context, input AskChatModelRequest) (string, error)
	AskDocsMode(ctx context.Context, text string) (string, error)
	AskSummarizerFirst(ctx context.Context, text string) (string, error)
	AskSummarizerSecond(ctx context.Context, input SummarizerSecondRequest) (string, error)
	AskRecsModel(ctx context.Context, input UniversalRequest) (string, error)
	AskAnalyzer(ctx context.Context, input UniversalRequest, analysisType string) (string, error)
}

type Services struct {
	User
	Business
	Models
}

type ServicesDependencies struct {
	Repos *repo.Repositories

	ChatModelUrl string
	DocsModelUrl string
	SummModelUrl string
	RecsModelUrl string
	AnalizerUrl  string
}

func NewServices(deps *ServicesDependencies) *Services {
	return &Services{
		User:     NewUserService(deps.Repos.User),
		Business: NewBusinessService(deps.Repos.Business),
		Models:   NewModelService(deps.ChatModelUrl, deps.DocsModelUrl, deps.SummModelUrl, deps.RecsModelUrl, deps.AnalizerUrl),
	}
}
