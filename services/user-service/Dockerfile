FROM golang:1.24-alpine AS builder

WORKDIR /app

COPY . .

WORKDIR /app/services/user-service

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -o /app/user-service ./cmd/app

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /app/user-service .

COPY ./services/user-service/configs ./configs

CMD ["/app/user-service"]