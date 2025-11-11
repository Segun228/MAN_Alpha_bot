FROM golang:1.24-alpine AS builder

WORKDIR /app

COPY . .

WORKDIR /app/services/api-gateway

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -o /app/api-gateway ./cmd/app

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /app/api-gateway .

COPY ./services/api-gateway/configs ./configs

CMD ["/app/api-gateway"]