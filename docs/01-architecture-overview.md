# Architecture Overview

## Компоненты
- Backend (control plane): FastAPI + PostgreSQL, асинхронный SQLAlchemy, Alembic. Управляет пользователями, устройствами, подписками, регионами и реестром узлов, принимает heartbeat и usage-события.
- Gateway (data plane): HTTPS/WebSocket терминатор, использует API backend для валидации устройств и назначения Outline-ноды.
- Outline pool: набор Shadowsocks-нод, скрытых за gateway.
- Клиент: выполняет HTTVPS-handshake, запрашивает у backend валидность устройства и параметры узлов.

## Backend слои и каталоги
- `app/core`: конфигурация (`config.py`), подключение к БД (`database.py`), JWT-утилиты (`security.py`), JSON-логирование (`logging.py`).
- `app/models`: SQLAlchemy-модели (`user.py`, `device.py`, `subscription.py`, `plan.py`, `region.py`, `outline_node.py`, `gateway_node.py`, `session.py`).
- `app/schemas`: Pydantic-схемы для API (`auth.py`, `device.py`, `plan.py`, `subscription.py`, `region.py`, `nodes.py`, `session.py`, `usage.py`, `heartbeat.py`).
- `app/services`: прикладная логика (`auth_service.py`, `device_service.py`, `subscriptions_service.py`, `nodes_service.py`, `sessions_service.py`, `heartbeat_service.py`).
- `app/api/v1`: роутеры FastAPI (`health.py`, `auth.py`, `nodes.py`, `usage.py`, `heartbeat.py`) собираются в `api/v1/__init__.py` и подключаются из `app/main.py`.
- `alembic/`: `env.py` с async-настройкой и миграции схемы в `versions/`.
- `tests/`: минимальные unit-тесты healthcheck и валидации устройства.

## Потоки
1. Device validation: клиент вызывает `/api/v1/auth/validate-device`, backend проверяет JWT, устройство и активную подписку.
2. Node assignment: `/api/v1/nodes/assign-outline` возвращает заглушку Outline-ноды с полями host/port/method/password/region.
3. Usage и heartbeat: `/api/v1/usage/report` принимает трафиковые счётчики по session_id; `/api/v1/gateway/heartbeat` и `/api/v1/outline/heartbeat` фиксируют последний heartbeat узлов.
4. Health: `/api/v1/health` подтверждает готовность приложения.

## Конфигурация и окружение
- Настройки читаются из `.env` через `core.config.Settings`: `BACKEND_DB_DSN`, `BACKEND_SECRET_KEY`, `BACKEND_DEBUG`, `BACKEND_HOST`, `BACKEND_PORT`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.
- Docker Compose поднимает PostgreSQL и backend; `.env.example` содержит шаблон значений, `BACKEND_DB_DSN` по умолчанию указывает на сервис `postgres`.

## Логирование
JSON-логи включаются в `app/main.py` через `core.logging.configure_logging`, уровень задаётся переменной `BACKEND_DEBUG`.
