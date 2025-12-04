package broker

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/broker/brokererrors"
	"github.com/Segun228/MAN_Alpha_bot/services/user-service/pkg/models"
	"github.com/segmentio/kafka-go"
)

type Producer struct {
	writer *kafka.Writer
}

func NewProducer(brokers []string, topic string) *Producer {
	writer := &kafka.Writer{
		Addr:         kafka.TCP(brokers...),
		Topic:        topic,
		Balancer:     &kafka.LeastBytes{},
		WriteTimeout: 10 * time.Second,
		ReadTimeout:  10 * time.Second,
	}
	return &Producer{writer: writer}
}

func (p *Producer) ProduceLogs(ctx context.Context, logs []models.Log) error {
	kafkaMessages := make([]kafka.Message, 0, len(logs))
	var serErr brokererrors.SerialisationError

	for i, log := range logs {
		msgBytes, err := json.Marshal(log)
		if err != nil {
			serErr.FailedCount++
			serErr.Errors = append(serErr.Errors, fmt.Errorf("log %d %s/%s: failed to marshal log: %w",
				i,
				log.Source,
				log.Action,
				err,
			))
			continue
		}

		kafkaMessages = append(kafkaMessages, kafka.Message{
			Value: msgBytes,
		})
		serErr.SuccessfullCount++
	}

	if len(kafkaMessages) > 0 {
		if err := p.writer.WriteMessages(ctx, kafkaMessages...); err != nil {
			return fmt.Errorf("failed to sent %d messages to Kafka: %w", len(kafkaMessages), err)
		}
	}

	if serErr.FailedCount > 0 {
		return serErr
	}

	return nil
}

func (p *Producer) Close() error {
	return p.writer.Close()
}
