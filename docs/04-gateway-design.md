# Gateway Design

## Архитектура
- Transport: TLS-терминатор и WebSocket upgrade на `/ws`, обработка ping/pong и отключений.
- Auth layer: приём `hello`, вызов backend `/api/v1/auth/validate-device`, возврат `auth_result`.
- Session manager: in-memory учёт сессий и потоков, лимит `GATEWAY_MAX_STREAMS`, очистка при обрывах.
- Upstream: в MVP `FakeUpstream` (echo/blackhole), интерфейс совместим с будущим Outline-клиентом.
- Metrics/logging: Prometheus метрики и slog JSON/Text логи.

## Сетевые маршруты
- `/ws`: WebSocket с кадрами `hello`, `stream_open`, `stream_data` (base64), `stream_close`, `ping/pong`, `error`.
- `/metrics`: promhttp handler при включённом `GATEWAY_METRICS_ENABLED`.

## Сессии и потоки
- На успешный `hello` создаётся `session_id`, сохраняется device_id и пустой набор потоков.
- `stream_open` резервирует поток в `sessions.Manager` и проксируется в upstream.
- `stream_data` передаётся в upstream; эхо-ответ возвращается как `stream_data` клиенту.
- `stream_close` освобождает поток; закрытие WebSocket очищает все связанные потоки и сессию.

## Интеграция с backend
- Клиент `internal/auth.Client` обращается к `POST /api/v1/auth/validate-device` с полями `device_id`, `token`.
- Ответ backend парсится в `ValidateDeviceResult` с `allowed`, `user_id`, `subscription_status`, `reason`.
- Ошибки/отказы фиксируются в метриках `httvps_gateway_handshakes_total` и `httvps_gateway_backend_errors_total`.

## Конфигурация
- Источники: env или YAML (`config/example-config.yaml`).
- Ключевые параметры: `GATEWAY_LISTEN_ADDR`, `GATEWAY_TLS_CERT_PATH`, `GATEWAY_TLS_KEY_PATH`, `BACKEND_BASE_URL`, `BACKEND_TIMEOUT`, `GATEWAY_LOG_LEVEL`, `GATEWAY_LOG_FORMAT`, `GATEWAY_METRICS_ENABLED`, `GATEWAY_METRICS_PATH`, `GATEWAY_MAX_STREAMS`.

## Метрики и логи
- Метрики: активные сессии/потоки, handshakes (accepted/rejected/error), длительность handshake, ошибки backend, трафик bytes_in/bytes_out.
- Логи: JSON/Text через slog, поля минимум `device_id`, `session_id`, событие (`session_started`, ошибки потоков), уровень настраивается из конфигурации.
