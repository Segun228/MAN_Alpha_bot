package broker

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/models"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/utils"
)

func InitLogQueue(bufferSize int) chan models.Log {
	return make(chan models.Log, bufferSize)
}

func StartLogProcessor(ctx context.Context, logQueue chan models.Log, logsBroker MessageBroker, logger utils.Logger) {
	go func() {
		for {
			select {
			case logEntry, ok := <-logQueue:
				if !ok {
					logger.Info("log queue closed, processor shutting down")
					return
				}

				if err := logsBroker.SendLogs(ctx, []models.Log{logEntry}); err != nil {
					logger.Error("error sending log to broker", map[string]any{
						"error":  err,
						"action": logEntry.Action,
					})
				}
			case <-ctx.Done():
				logger.Info("log processor shutting down")
				return
			}
		}
	}()
}
