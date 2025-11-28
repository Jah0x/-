# Architecture Overview

## Компоненты
- Backend (control plane): FastAPI + PostgreSQL, асинхронный SQLAlchemy, Alembic. Отвечает за пользователей, устройства, подписки, регионы и реестр узлов.
- Gateway (data plane): HTTPS/WebSocket терминатор, использует API backend для валидации устройств и назначения Outline-ноды.
- Outline pool: набор Shadowsocks-нод, скрытых за gateway.
- Клиент: выполняет handshake HTTVPS, запрашивает в backend валидность устройства и параметры узлов.

## Backend слои
- core: конфигурация, подключение к БД, безопасность, логирование
- models: SQLAlchemy-модели пользователей, устройств, подписок, регионов и узлов
- schemas: Pydantic-схемы DTO для API
- services: доменная логика (валидация устройств, выбор узлов, работа с подписками)
- api: версионированные роутеры FastAPI
- alembic: миграции схемы

## Потоки
1. Device validation: клиент вызывает `/api/v1/auth/validate-device`, backend проверяет токен и подписку.
2. Node assignment: `/api/v1/nodes/assign-outline` отдаёт данные Outline-ноды (пока заглушка) с учётом региона.
3. Usage и heartbeat: `/api/v1/usage/report`, `/api/v1/gateway/heartbeat`, `/api/v1/outline/heartbeat` принимают базовые данные (заглушки).
4. Health: `/api/v1/health` проверяет готовность приложения.

## Конфигурация и окружение
- Настройки читаются из `.env` через `core.config.Settings`.
- Docker Compose поднимает PostgreSQL и backend; backend использует переменные `BACKEND_DB_DSN`, `BACKEND_SECRET_KEY`, `BACKEND_HOST`, `BACKEND_PORT` и JWT-настройки.

## Логирование
Backend выводит JSON-логи через `core.logging.configure_logging`, уровень задаётся флагом `BACKEND_DEBUG`.
