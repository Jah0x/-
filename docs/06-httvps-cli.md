# HTTVPS CLI

## Назначение
`httvps-cli` — минимальный референс-клиент для ручной проверки протокола HTTVPS. Он получает временный токен у backend, выполняет handshake с gateway и открывает один поток к удалённому хосту.

## Требования
- Go 1.24+
- Доступный backend и gateway (docker-compose из корня репозитория).

## Запуск локального стенда
1. Запустите зависимости: `make up`.
2. Убедитесь, что backend доступен на `http://localhost:8000`, gateway — на `https://localhost:8443/ws` (self-signed).
3. Подготовьте значения устройства и токена, допустимые для backend.

## Пример использования
Из каталога `client/httvps-cli`:
```bash
BACKEND_BASE=http://localhost:8000 \
DEVICE_ID=device-1 \
DEVICE_TOKEN=test-token \
go run . \
  -backend ${BACKEND_BASE} \
  -device ${DEVICE_ID} \
  -token ${DEVICE_TOKEN} \
  -target example.com:80 \
  -insecure true
```

Флаги:
- `-backend` — базовый URL backend.
- `-gateway` — явный URL gateway (если отличается от ответа backend).
- `-device`, `-token` — данные устройства.
- `-region` — желаемый код региона (опционально передаётся в backend).
- `-target` — целевой хост:порт для тестового запроса.
- `-insecure` — пропустить проверку TLS для локальных стендов.
- `-version` — версия протокола (по умолчанию `1`).

CLI отправляет HTTP GET на указанный `target`, печатая ответ в stdout. В Outline-режиме первый `stream_data` содержит Shadowsocks address header перед HTTP-запросом.
