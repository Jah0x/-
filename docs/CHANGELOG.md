# Changelog

## [0.3.0] - 2024-05-21
### Added
- Backend MVP: FastAPI приложение с конфигурацией, JSON-логированием, JWT-утилитами и асинхронным подключением к БД.
- SQLAlchemy модели для пользователей, устройств, подписок, планов, регионов, gateway и Outline нод, сессий; первая миграция Alembic.
- API `/api/v1/health`, `/api/v1/auth/validate-device`, заглушки нод, usage и heartbeat.
- Тесты для health и validate-device.
- Обновления документации: архитектурный обзор и описание control-plane API.

## [0.2.0] - 2024-05-21
### Added
- Базовая структура репозитория: backend, gateway, docs, deploy, docker-compose, Makefile, .env.example.
- Каркас документации и описания правил разработки.

## [0.1.0] - 2024-05-20
### Added
- Formalized HTTVPS specification with structured overview, components, roadmap, non-functional requirements, coding rules, and assumptions/open questions.
- Introduced staged development plan (Stages 0–8) in `docs/00-spec-httvps.md`.
- Added architecture and protocol documentation skeletons: `01-architecture-overview.md`, `02-control-plane-api.md`, `03-httvps-protocol.md`, `04-gateway-design.md`, `05-outline-pool.md`.
