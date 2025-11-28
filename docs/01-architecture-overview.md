# Architecture Overview

## Компоненты
- Backend (control plane): FastAPI + PostgreSQL, асинхронный SQLAlchemy, Alembic. Управляет пользователями, устройствами, подписками, регионами и реестром узлов, принимает heartbeat и usage-события.
- Gateway (data plane): HTTPS/WebSocket терминатор, использует API backend для валидации устройств, ведёт сессии и проксирует потоки к upstream (в MVP — заглушка эхо).
- Outline pool: набор Shadowsocks-нод, скрытых за gateway (будет подключён на следующих этапах).
- Клиент: выполняет HTTVPS-handshake, запрашивает у backend валидность устройства и параметры узлов.

## Backend слои и каталоги
- `app/core`: конфигурация (`config.py`), подключение к БД (`database.py`), JWT-утилиты (`security.py`), JSON-логирование (`logging.py`).
- `app/models`: SQLAlchemy-модели (`user.py`, `device.py`, `subscription.py`, `plan.py`, `region.py`, `outline_node.py`, `gateway_node.py`, `session.py`).
- `app/schemas`: Pydantic-схемы для API (`auth.py`, `device.py`, `plan.py`, `subscription.py`, `region.py`, `nodes.py`, `session.py`, `usage.py`, `heartbeat.py`).
- `app/services`: прикладная логика (`auth_service.py`, `device_service.py`, `subscriptions_service.py`, `nodes_service.py`, `sessions_service.py`, `heartbeat_service.py`).
- `app/api/v1`: роутеры FastAPI (`health.py`, `auth.py`, `nodes.py`, `usage.py`, `heartbeat.py`) собираются в `api/v1/__init__.py` и подключаются из `app/main.py`.
- `alembic/`: `env.py` с async-настройкой и миграции схемы в `versions/`.
- `tests/`: unit-тесты healthcheck и валидации устройства.

## Gateway слои и каталоги
- `cmd/httvps-gateway`: точка входа, сборка зависимостей и запуск сервера.
- `internal/config`: загрузка конфигурации из env/YAML (`GATEWAY_LISTEN_ADDR`, пути до TLS, `BACKEND_BASE_URL`, таймауты, логирование, метрики, лимиты потоков).
- `internal/server`: HTTPS + WebSocket сервер, маршруты `/ws` и `/metrics`.
- `internal/protocol`: схемы кадров и обработчик сессии (handshake, stream_open/data/close, ping/pong).
- `internal/auth`: клиент backend `/api/v1/auth/validate-device`.
- `internal/sessions`: in-memory учёт сессий и потоков с ограничением `GATEWAY_MAX_STREAMS`.
- `internal/upstream`: заглушка эхо для потоков (будет заменена на Outline-клиент).
- `internal/metrics`: Prometheus-метрики активных сессий/потоков, handshakes, трафика, ошибок backend.

## Потоки
1. Device validation: клиент отправляет `hello` в gateway, который вызывает `/api/v1/auth/validate-device` backend и возвращает `auth_result`.
2. Stream handling: после успешного handshake клиент открывает `stream_open`, передаёт `stream_data` (base64). В MVP gateway эхо-ответом отправляет `stream_data` обратно.
3. Usage и heartbeat: `/api/v1/usage/report` принимает трафиковые счётчики по session_id; `/api/v1/gateway/heartbeat` и `/api/v1/outline/heartbeat` фиксируют последний heartbeat узлов.
4. Health: `/api/v1/health` подтверждает готовность backend.

## Конфигурация и окружение
- Backend: настройки из `.env` через `core.config.Settings`: `BACKEND_DB_DSN`, `BACKEND_SECRET_KEY`, `BACKEND_DEBUG`, `BACKEND_HOST`, `BACKEND_PORT`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.
- Gateway: env-переменные или `config/example-config.yaml` с адресом прослушки, путями TLS, ссылкой на backend и параметрами логов/метрик/лимитов.
- Docker Compose поднимает PostgreSQL, backend и gateway; `.env.example` содержит шаблон значений, `deploy/certs` содержит dev-TLS для gateway.

## Логирование и метрики
- Backend: JSON-логи через `core.logging.configure_logging`, уровень задаётся `BACKEND_DEBUG`.
- Gateway: slog JSON/Text с уровнем `GATEWAY_LOG_LEVEL` и метрики Prometheus на `/metrics` при включённом `GATEWAY_METRICS_ENABLED`.
