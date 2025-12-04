package broker

import (
	"context"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/models"
)

type MessageBroker interface {
	SendLogs(ctx context.Context, logs []models.Log) error
	Close() error
}

type KafkaBroker struct {
	producer *Producer
}

func NewKafkaBroker(producer *Producer) *KafkaBroker {
	return &KafkaBroker{
		producer: producer,
	}
}

func (k *KafkaBroker) SendLogs(ctx context.Context, logs []models.Log) error {
	return k.producer.ProduceLogs(ctx, logs)
}

func (k *KafkaBroker) Close() error {
	return k.producer.Close()
}
