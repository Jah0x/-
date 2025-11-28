# Gateway

HTTVPS gateway реализует WebSocket-туннель поверх HTTPS и маршрутизацию потоков к upstream. Версия MVP использует заглушку upstream и аутентификацию устройств через backend.

## Конфигурация

- Переменные окружения: `GATEWAY_LISTEN_ADDR`, `GATEWAY_TLS_CERT_PATH`, `GATEWAY_TLS_KEY_PATH`, `BACKEND_BASE_URL`, `BACKEND_TIMEOUT`, `GATEWAY_LOG_LEVEL`, `GATEWAY_LOG_FORMAT`, `GATEWAY_METRICS_ENABLED`, `GATEWAY_METRICS_PATH`, `GATEWAY_MAX_STREAMS`.
- Альтернатива: YAML-файл, пример в `config/example-config.yaml`.

## Запуск локально

```
GATEWAY_LISTEN_ADDR=0.0.0.0:8443 \
GATEWAY_TLS_CERT_PATH=./deploy/certs/gateway-cert.pem \
GATEWAY_TLS_KEY_PATH=./deploy/certs/gateway-key.pem \
BACKEND_BASE_URL=http://localhost:8000 \
BACKEND_TIMEOUT=5s \
GO111MODULE=on go run ./cmd/httvps-gateway
```

Метрики доступны на `/metrics` при включённом флаге.

## Тесты

```
go test ./...
```

