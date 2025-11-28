# Architecture Overview

## Компоненты
- Backend (control plane): FastAPI + PostgreSQL, асинхронный SQLAlchemy, Alembic. Управляет пользователями, устройствами, подписками, регионами и реестром узлов, принимает heartbeat и usage-события, назначает Outline-ноды устройствам.
- Gateway (data plane): HTTPS/WebSocket терминатор, использует API backend для валидации устройств, ведёт сессии и проксирует потоки к upstream. Upstream выбирается конфигурацией: `FakeUpstream` для dev или `OutlineUpstream` для реального Shadowsocks.
- Outline pool: набор Shadowsocks-нод, скрытых за gateway, обновляется heartbeat-сообщениями и используется backend для назначения; пулы/региональные связи хранятся в `outline_pools`, `outline_pool_nodes`, `outline_pool_regions`.
- Клиент: выполняет HTTVPS-handshake, запрашивает у backend валидность устройства и выбирает регион.

## Backend слои и каталоги
- `app/core`: конфигурация (`config.py`), подключение к БД (`database.py`), JWT-утилиты (`security.py`), JSON-логирование (`logging.py`).
- `app/models`: SQLAlchemy-модели (`user.py`, `device.py`, `subscription.py`, `plan.py`, `region.py`, `outline_node.py`, `gateway_node.py`, `session.py`, `outline_pool*.py`).
- `app/schemas`: Pydantic-схемы для API (`auth.py`, `device.py`, `plan.py`, `subscription.py`, `region.py`, `nodes.py`, `session.py`, `usage.py`, `heartbeat.py`).
- `app/services`: прикладная логика (`auth_service.py`, `device_service.py`, `subscriptions_service.py`, `nodes_service.py`, `sessions_service.py`, `heartbeat_service.py`, `outline_pool_service.py`).
- `app/api/v1`: роутеры FastAPI (`health.py`, `auth.py`, `nodes.py`, `usage.py`, `heartbeat.py`) собираются в `api/v1/__init__.py` и подключаются из `app/main.py`.
- `alembic/`: `env.py` с async-настройкой и миграции схемы в `versions/`.
- `tests/`: unit-тесты healthcheck и валидации устройства.

## Gateway слои и каталоги
- `cmd/httvps-gateway`: точка входа, сборка зависимостей и запуск сервера.
- `internal/config`: загрузка конфигурации из env/YAML (`GATEWAY_LISTEN_ADDR`, пути до TLS, `BACKEND_BASE_URL`, таймауты, логирование, метрики, лимиты потоков, `GATEWAY_UPSTREAM_MODE`).
- `internal/server`: HTTPS + WebSocket сервер, маршруты `/ws` и `/metrics`.
- `internal/protocol`: схемы кадров и обработчик сессии (handshake, stream_open/data/close, ping/pong, ошибки).
- `internal/auth`: клиент backend `/api/v1/auth/validate-device`.
- `internal/nodes`: клиент `/api/v1/nodes/assign-outline`.
- `internal/sessions`: in-memory учёт сессий и потоков с ограничением `GATEWAY_MAX_STREAMS`.
- `internal/upstream`: `FakeUpstream` для эхо/dev и `OutlineUpstream` для Shadowsocks соединений с синхронизацией стора (memory/Redis/NATS) для привязок сессий к пулам и нодам.
- `internal/metrics`: Prometheus-метрики активных сессий/потоков, handshakes, трафика, ошибок backend.

## Потоки
1. Device validation: клиент отправляет `hello` в gateway, который вызывает `/api/v1/auth/validate-device` backend и возвращает `auth_result`.
2. Outline assignment: при режиме `outline` gateway запрашивает `/api/v1/nodes/assign-outline` с `device_id` и `region`, связывает сессию с выданной Outline-нодой.
3. Stream handling: после успешного handshake клиент открывает `stream_open`, передаёт `stream_data` (base64). В `fake` режиме gateway эхо-ответом отправляет данные обратно; в `outline` режиме трафик уходит в Shadowsocks-соединение к выбранной ноде.
4. Usage и heartbeat: `/api/v1/usage/report` принимает трафиковые счётчики по session_id; `/api/v1/gateway/heartbeat` и `/api/v1/outline/heartbeat` фиксируют последний heartbeat узлов.
5. Health: `/api/v1/health` подтверждает готовность backend.

## Конфигурация и окружение
- Backend: настройки из `.env` через `core.config.Settings`: `BACKEND_DB_DSN`, `BACKEND_SECRET_KEY`, `BACKEND_DEBUG`, `BACKEND_HOST`, `BACKEND_PORT`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.
- Gateway: env-переменные или `config/example-config.yaml` с адресом прослушки, путями TLS, ссылкой на backend и параметрами логов/метрик/лимитов, выбором `GATEWAY_SESSION_STORE` (`memory`/`redis`/`nats`), Redis/NATS реквизитами и TTL `GATEWAY_SESSION_STORE_TTL`.
- Docker Compose поднимает PostgreSQL, backend и gateway; `.env.example` содержит шаблон значений, `deploy/certs` содержит dev-TLS для gateway.

## Логирование и метрики
- Backend: JSON-логи через `core.logging.configure_logging`, уровень задаётся `BACKEND_DEBUG`; middleware `RequestContextMiddleware` выдаёт `X-Request-ID` и прокидывает его в логи; `MetricsMiddleware` снимает latency, in-progress, счётчики по методам/путям/кодам и исключения, экспорт на `/metrics` в Prometheus-формате.
- Gateway: slog JSON/Text с уровнем `GATEWAY_LOG_LEVEL` и метрики Prometheus на `/metrics` при включённом `GATEWAY_METRICS_ENABLED`; добавлены гистограммы длительности handshake и сессий, счётчики итогов handshake и подключений, открытий/закрытий потоков, ошибок потоков/протокола и upstream ошибок с разбивкой по операциям, трафик in/out и backend ошибки.

## Наблюдаемость, дашборды и алерты
- PrometheusRule манифест `docs/monitoring/prometheus-rules.yaml` поднимает алерты по error-rate handshake/5xx, всплескам upstream ошибок, низкой длительности сессий, p95 latency backend и исключениям в хендлерах.
- Grafana дашборды: `docs/monitoring/gateway-grafana-dashboard.json` визуализирует активные сессии/потоки, скорость handshake по результатам, upstream ошибки, трафик и p95 длительность сессий; `docs/monitoring/backend-grafana-dashboard.json` показывает in-flight запросы, RPS по роутам, p95 latency, 5xx rate и исключения.
