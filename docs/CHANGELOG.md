# Changelog

## [0.11.0] - 2026-05-20
### Added
- Control-plane admin API для CRUD тарифов, регионов, Outline- и gateway-нод с ответами об ошибках конфликтов/отсутствия регионов.
- Аудит админских действий в таблице `admin_audit_logs` и endpoint `/api/v1/admin/audit`.
- CLI `app/admin_cli.py` для админов с операциями над тарифами, регионами, нодами и просмотром аудита.

## [0.10.1] - 2026-05-12
### Added
- SDK `sdk/` для HTTVPS: handshake-клиент, управление потоками, пример подключения и совместимые тесты.
- Документация протокола дополнена поведением SDK при handshake и обмене потоками.

## [0.10.0] - 2026-05-06
### Added
- Продакшн Dockerfile для backend и gateway с безопасным запуском через gunicorn и статический Go-бинарник.
- Kubernetes-манифесты в `deploy/k8s` для backend и gateway, пример секретов для DSN и TLS, цели в Makefile для их применения.
- CI/CD workflow на GitHub Actions с прогоном тестов и публикацией продакшн-образов в GHCR.

## [0.9.2] - 2026-04-05
### Added
- Расширены метрики gateway: счётчики подключений/handshake по исходам, длительность handshake и сессий, ошибки потоков/протокола, upstream операции, открытие/закрытие потоков и трафик.
- Backend получил middleware для трассировки `X-Request-ID`, улучшенное JSON-логирование с `request_id` и Prometheus-метрики `/metrics` для latency, in-progress, кодов ответов и исключений.
- Добавлены готовые PrometheusRule алерты и Grafana дашборды для gateway/backend (`docs/monitoring/*`).

## [0.9.1] - 2026-03-20
### Added
- В backend добавлены модели пулов Outline и региональные связи (`outline_pools`, `outline_pool_nodes`, `outline_pool_regions`), расширен assign-outline запросом `pool_code` и сервисом выбора ноды по пулу.
- Настройки backend получили `OUTLINE_DEFAULT_POOL_CODE`, чтобы выдавать сессии из нужного пула по умолчанию.
- Gateway OutlineUpstream хранит привязки сессий в сторе (memory/Redis/NATS), при подключении вытягивает состояние из внешнего стора и чистит его через `UnbindSession`.
- Обновлены описание архитектуры и раздел Outline pool с деталями по пулам, сторам и кодам ошибок.

## [0.9.0] - 2026-02-10
### Added
- Завершена спецификация HTTVPS: определён handshake с session_token, коды ошибок, лимиты потоков и правила работы с Outline.
- Backend выдаёт дескриптор сессии через `/api/v1/httvps/session` и валидацию токена для gateway через `/internal/httvps/validate-session`.
- Gateway реализует серверную часть протокола HTTVPS с проверкой токена, лимитами потоков и маршрутизацией через Outline/fake upstream.
- Добавлен референс-клиент `client/httvps-cli` для ручной проверки туннеля и инструкции по его запуску.

## [0.8.0] - 2026-01-10
### Added
- Health-check сервиса Outline: периодические запросы к API нод с записью статуса, latency и ошибок в БД, новые поля модели и миграция.
- Алгоритм выбора ноды учитывает статус: игнорирует `down`, предпочитает `healthy`, при отсутствии отдаёт ошибку `no_healthy_outline_nodes`.
- Admin API `/api/v1/admin/outline-nodes` для просмотра статусов, деталей нод и ручного запуска проверки под `X-Admin-Token`.
- Конфигурация с переменными `OUTLINE_HEALTHCHECK_*`, автоматический фоновой воркер health-check и покрытие тестами логики статусов и выбора ноды.

## [0.7.0] - 2025-12-15
### Added
- Backend хранит Outline-ноды с доступом к Outline API и таблицу выданных access-ключей, миграции Alembic обновлены.
- Добавлен асинхронный клиент Outline API и интеграция assign-outline с созданием реальных ключей и привязкой к устройству.
- Gateway и его протокол читают расширенный ответ assign-outline (id/URL ключа), обновлены структуры upstream.
- Добавлены unit-тесты для Outline-клиента и обновлены тесты assign-outline.
- Добавлен revoke-outline: отзыв последнего access-key устройства, попытка удалить ключ через Outline API и ответ с результатом.

## [0.6.0] - 2025-11-30
### Added
- Конфигурация gateway получила `upstream_mode` (fake/outline) и примеры в `.env.example`, `docker-compose.yml`, `config/example-config.yaml`.
- В gateway реализованы OutlineUpstream на базе Shadowsocks, клиент assign-outline для backend и привязка сессий к конкретным Outline-нодам.
- Backend endpoint `/api/v1/nodes/assign-outline` теперь читает ноды из БД, возвращает `node_id` и отдаёт ошибку 503 при отсутствии активных нод; добавлены тесты.
- Обновлена документация: dev-plan Stage 3, архитектурный обзор, протокол, описание gateway и outline pool.

## [0.5.0] - 2025-11-29
### Added
- Формализован поэтапный план разработки в `docs/00-dev-plan.md` и отражён в README.
- Реализован Stage 2: HTTVPS-gateway (MVP) на Go с HTTPS/WebSocket сервером, конфигурацией, метриками, заглушкой upstream и unit-тестами.
- Обновлены протокол и архитектурное описание для нового gateway, добавлены примеры запуска и ручной проверки.

## [0.4.0] - 2025-11-28
### Added
- Приведён к финалу Этап 0: шаблон `.env.example`, актуализированный `docker-compose.yml`, `Makefile` с базовыми целями, обновлённый README и Dockerfile backend для локального запуска.
- Реализован Этап 1: FastAPI backend с конфигурацией, JSON-логированием, JWT-утилитами, асинхронным подключением к БД, миграцией Alembic и моделями пользователей, устройств, подписок, тарифов, регионов, gateway/Outline-нод и сессий.
- Эндпоинты `/api/v1/health`, `/api/v1/auth/validate-device`, заглушка `/api/v1/nodes/assign-outline`, обработка `/api/v1/usage/report` и heartbeat `/api/v1/gateway/heartbeat`, `/api/v1/outline/heartbeat`.
- Минимальные unit-тесты для healthcheck и валидации устройства.
- Документация обновлена: архитектурный обзор и описание control-plane API отражают реализованную структуру.

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
