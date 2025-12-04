package service

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"
)

type ReportService struct {
	reportRepo repo.Reports
	userRepo   repo.User
}

func NewReportsService(reportRepo repo.Reports, userRepo repo.User) *ReportService {
	return &ReportService{
		reportRepo: reportRepo,
		userRepo:   userRepo,
	}
}

func (s *ReportService) GetReports(ctx context.Context) ([]models.Report, error) {
	return s.reportRepo.GetReports(ctx)
}

func (s *ReportService) GetReportByID(ctx context.Context, reportID int) (*models.Report, error) {
	return s.reportRepo.GetReportByID(ctx, reportID)
}

func (s *ReportService) GetReportsByTgID(ctx context.Context, tgID int64) ([]models.Report, error) {
	user, err := s.userRepo.GetUserByTgID(ctx, tgID)
	if err != nil {
		return nil, err
	}

	return s.reportRepo.GetByReportsUserID(ctx, user.ID)
}

func (s *ReportService) CreateReport(ctx context.Context, report ReportCreateInput) (*models.Report, error) {
	newReport := models.Report{
		UserID:    report.UserID,
		Name:      report.Name,
		Users:     report.Users,
		Customers: report.Customers,
		AVP:       report.AVP,
		APC:       report.APC,
		TMS:       report.TMS,
		COGS:      report.COGS,
		COGS1s:    report.COGS1s,
		FC:        report.FC,
		RR:        report.RR,
		AGR:       report.AGR,
	}

	return s.reportRepo.CreateReport(ctx, newReport)
}

func (s *ReportService) CreateReportWithTgID(ctx context.Context, tgID int64, report ReportCreateInput) (*models.Report, error) {
	user, err := s.userRepo.GetUserByTgID(ctx, tgID)
	if err != nil {
		return nil, err
	}

	newReport := models.Report{
		UserID:    user.ID,
		Name:      report.Name,
		Users:     report.Users,
		Customers: report.Customers,
		AVP:       report.AVP,
		APC:       report.APC,
		TMS:       report.TMS,
		COGS:      report.COGS,
		COGS1s:    report.COGS1s,
		FC:        report.FC,
		RR:        report.RR,
		AGR:       report.AGR,
	}

	return s.reportRepo.CreateReport(ctx, newReport)
}

func (s *ReportService) PutReport(ctx context.Context, report ReportUpdateInput) (*models.Report, error) {
	updatedReport := models.Report{
		ID:        report.ID,
		UserID:    report.UserID,
		Name:      report.Name,
		Users:     report.Users,
		Customers: report.Customers,
		AVP:       report.AVP,
		APC:       report.APC,
		TMS:       report.TMS,
		COGS:      report.COGS,
		COGS1s:    report.COGS1s,
		FC:        report.FC,
		RR:        report.RR,
		AGR:       report.AGR,
	}

	return s.reportRepo.UpdateReport(ctx, updatedReport)
}

func (s *ReportService) PatchReport(ctx context.Context, report ReportUpdateInput) (*models.Report, error) {
	existingReport, err := s.reportRepo.GetReportByID(ctx, report.ID)
	if err != nil {
		return nil, err
	}

	if report.UserID != 0 {
		existingReport.UserID = report.UserID
	}

	if report.Name != "" {
		existingReport.Name = report.Name
	}

	if report.Users != 0 {
		existingReport.Users = report.Users
	}

	if report.Customers != 0 {
		existingReport.Customers = report.Customers
	}

	if report.AVP != 0 {
		existingReport.AVP = report.AVP
	}

	if report.APC != 0 {
		existingReport.APC = report.APC
	}

	if report.TMS != 0 {
		existingReport.TMS = report.TMS
	}

	if report.COGS != 0 {
		existingReport.COGS = report.COGS
	}

	if report.COGS1s != 0 {
		existingReport.COGS1s = report.COGS1s
	}

	if report.FC != 0 {
		existingReport.FC = report.FC
	}

	if report.RR != 0 {
		existingReport.RR = report.RR
	}

	if report.AGR != 0 {
		existingReport.AGR = report.AGR
	}

	return s.reportRepo.UpdateReport(ctx, *existingReport)
}

func (s *ReportService) DeleteReport(ctx context.Context, reportID int) error {
	return s.reportRepo.DeleteReport(ctx, reportID)
}
