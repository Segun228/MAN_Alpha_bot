package crypto

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type ReportsCryptoRepo struct {
	Repo      repo.Reports
	Encrypter Decrypter
}

func NewReportsCryptoRepo(repo repo.Reports, encrypter Decrypter) *ReportsCryptoRepo {
	return &ReportsCryptoRepo{
		Repo:      repo,
		Encrypter: encrypter,
	}
}

func (r *ReportsCryptoRepo) GetReports(ctx context.Context) ([]models.Report, error) {
	reports, err := r.Repo.GetReports(ctx)
	if err != nil {
		return nil, err
	}

	for i := range reports {
		reports[i].Name, err = r.Encrypter.Decrypt(reports[i].Name)
		if err != nil {
			return nil, err
		}
	}

	return reports, nil
}

func (r *ReportsCryptoRepo) GetReportByID(ctx context.Context, reportID int) (*models.Report, error) {
	report, err := r.Repo.GetReportByID(ctx, reportID)
	if err != nil {
		return nil, err
	}

	report.Name, err = r.Encrypter.Decrypt(report.Name)
	if err != nil {
		return nil, err
	}

	return report, nil
}

func (r *ReportsCryptoRepo) GetByReportsUserID(ctx context.Context, userID int) ([]models.Report, error) {
	reports, err := r.Repo.GetByReportsUserID(ctx, userID)
	if err != nil {
		return nil, err
	}

	for i := range reports {
		reports[i].Name, err = r.Encrypter.Decrypt(reports[i].Name)
		if err != nil {
			return nil, err
		}
	}

	return reports, nil
}

func (r *ReportsCryptoRepo) CreateReport(ctx context.Context, report models.Report) (*models.Report, error) {
	var err error
	report.Name, err = r.Encrypter.Encrypt(report.Name)
	if err != nil {
		return nil, err
	}

	return r.Repo.CreateReport(ctx, report)
}

func (r *ReportsCryptoRepo) UpdateReport(ctx context.Context, report models.Report) (*models.Report, error) {
	var err error
	report.Name, err = r.Encrypter.Encrypt(report.Name)
	if err != nil {
		return nil, err
	}

	return r.Repo.UpdateReport(ctx, report)
}

func (r *ReportsCryptoRepo) DeleteReport(ctx context.Context, reportID int) error {
	return r.Repo.DeleteReport(ctx, reportID)
}
