package service

import (
	"context"
	"testing"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo/mocks"
	"github.com/stretchr/testify/assert"
	"go.uber.org/mock/gomock"
)

func TestReportService_GetReportByID(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockReportsRepo := mocks.NewMockReports(ctrl)
	reportService := NewReportsService(mockReportsRepo, nil)

	reportID := 1
	expectedReport := &models.Report{ID: reportID, Name: "Test"}

	t.Run("Success", func(t *testing.T) {
		mockReportsRepo.EXPECT().GetReportByID(gomock.Any(), reportID).Return(expectedReport, nil)
		report, err := reportService.GetReportByID(context.Background(), reportID)
		assert.NoError(t, err)
		assert.Equal(t, expectedReport, report)
	})
}

func TestReportService_CreateReport(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockReportsRepo := mocks.NewMockReports(ctrl)
	mockUserRepo := mocks.NewMockUser(ctrl)
	reportService := NewReportsService(mockReportsRepo, mockUserRepo)

	reportToCreate := ReportCreateInput{
		UserID: 1,
		Name:   "New Report",
	}

	createdReport := &models.Report{
		ID:        1,
		UserID:    1,
		Name:      "New Report",
		CreatedAt: time.Now(),
	}

	t.Run("Success - Report created", func(t *testing.T) {
		mockReportsRepo.EXPECT().CreateReport(gomock.Any(), gomock.Any()).Return(createdReport, nil)

		result, err := reportService.CreateReport(context.Background(), reportToCreate)

		assert.NoError(t, err)
		assert.Equal(t, createdReport, result)
	})
}

func TestReportService_PatchReport(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockReportsRepo := mocks.NewMockReports(ctrl)
	reportService := NewReportsService(mockReportsRepo, nil)

	reportToPatch := models.Report{
		ID:   1,
		Name: "Updated Report",
	}

	reportToPatchInput := ReportUpdateInput{
		ID:   1,
		Name: "Updated Report",
	}

	t.Run("Success", func(t *testing.T) {
		mockReportsRepo.EXPECT().GetReportByID(gomock.Any(), reportToPatch.ID).Return(&reportToPatch, nil)

		mockReportsRepo.EXPECT().UpdateReport(gomock.Any(), reportToPatch).Return(&reportToPatch, nil)

		updatedReport, err := reportService.PatchReport(context.Background(), reportToPatchInput)

		assert.NoError(t, err)
		assert.Equal(t, &reportToPatch, updatedReport)
	})
}

func TestReportService_DeleteReport(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockReportsRepo := mocks.NewMockReports(ctrl)
	reportService := NewReportsService(mockReportsRepo, nil)

	reportID := 1

	t.Run("Success", func(t *testing.T) {
		mockReportsRepo.EXPECT().DeleteReport(gomock.Any(), reportID).Return(nil)
		err := reportService.DeleteReport(context.Background(), reportID)
		assert.NoError(t, err)
	})
}
