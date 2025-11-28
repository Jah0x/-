FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/httvps-gateway ./cmd/httvps-gateway

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /out/httvps-gateway /usr/local/bin/httvps-gateway
COPY config/example-config.yaml /app/config/example-config.yaml
EXPOSE 8443
ENTRYPOINT ["/usr/local/bin/httvps-gateway"]
