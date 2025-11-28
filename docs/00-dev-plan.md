# Дорожная карта разработки

## Stage 0: Инициализация репозитория
- Цель: подготовить исходную структуру проекта и базовые правила.
- Задачи: создать директории backend/gateway/docs, прописать Makefile и docker-compose, задать .env.example и общие правила разработки.
- Затрагиваемые файлы: корень репозитория (Makefile, docker-compose.yml, .gitignore, README.md, .env.example), docs/00-spec-httvps.md.
- Внешние зависимости: базовые инструменты разработки (Python, Go, Docker).

## Stage 1: Backend (MVP control plane)
- Цель: минимальный контрол-плейн на FastAPI/PostgreSQL.
- Задачи: конфигурация приложения, JSON-логирование, JWT-утилиты, асинхронное подключение к БД, модели пользователей/устройств/подписок/регионов/нод/сессий, миграция Alembic, эндпоинты health, validate-device, heartbeat/usage/nodes заглушки, unit-тесты.
- Затрагиваемые файлы: backend/app/*, backend/alembic/*, backend/tests/*, docker-compose.yml, .env.example, docs/01-architecture-overview.md, docs/02-control-plane-api.md, docs/CHANGELOG.md.
- Внешние зависимости: FastAPI, SQLAlchemy, Alembic, asyncpg, PyJWT.

## Stage 2: HTTVPS-gateway (MVP)
- Цель: рабочий дата-плейн на Go с WebSocket-туннелем и заглушкой upstream.
- Задачи: конфигурация через env/YAML, HTTPS+WebSocket сервер, обработка hello/stream_* кадров, валидация устройства через backend, in-memory менеджер сессий и потоков, заглушка upstream (echo/devnull), Prometheus-метрики, JSON-логирование, unit-тесты, Dockerfile и интеграция в docker-compose.
- Затрагиваемые файлы: gateway/cmd/httvps-gateway, gateway/internal/{config,server,protocol,auth,sessions,upstream,metrics}, gateway/config/example-config.yaml, gateway/Dockerfile, docker-compose.yml, .env.example, docs/03-httvps-protocol.md, docs/04-gateway-design.md, docs/01-architecture-overview.md, docs/CHANGELOG.md, README.md.
- Внешние зависимости: Go стандартная библиотека, gorilla/websocket, prometheus/client_golang, yaml.v3, uuid.

## Stage 3: Интеграция с Outline
- Цель: подключить реальный Outline/Shadowsocks вместо заглушки с сохранением dev-режима.
- Задачи: выбор upstream режима (fake/outline) в конфигурации gateway, запрос назначения Outline-ноды в backend с привязкой к сессии, реальный OutlineUpstream на базе Shadowsocks клиента, обработка ошибок/фейловера, обновление протокола и тестов.
- Затрагиваемые файлы: backend (assign-outline из БД, схемы и тесты), gateway/internal/{config,protocol,upstream,nodes}, docs/00-05, docs/CHANGELOG.md, примеры конфигурации и docker-compose.
- Внешние зависимости: Outline/Shadowsocks клиентские библиотеки.

## Stage 4: Мульти-gateway и пул Outline
- Цель: балансировка и пул ресурсов для нескольких gateway и Outline-ноды.
- Задачи: пул Outline, распределение по регионам, обновление схем БД, синхронизация сессий между gateway, расширение API backend для назначения нод.
- Затрагиваемые файлы: backend модели/сервисы, gateway/internal/upstream, docs/01-architecture-overview.md, docs/05-outline-pool.md, docs/CHANGELOG.md.
- Внешние зависимости: Redis/консистентный стор для состояния, возможно NATS/Kafka для событий.

## Stage 5: Мониторинг и логирование
- Цель: полнофункциональные метрики, логирование и алертинг.
- Задачи: расширение метрик gateway и backend, трассировка запросов, сбор логов, дашборды Prometheus/Grafana, алерты по доступности и ошибкам.
- Затрагиваемые файлы: gateway/internal/metrics, backend/обвязка логов и метрик, docs/CHANGELOG.md, docs/01-architecture-overview.md.
- Внешние зависимости: Prometheus, Grafana, Loki/ELK, OpenTelemetry SDK.

## Stage 6: Упаковка и деплой
- Цель: подготовить Docker/K8s артефакты для продакшена.
- Задачи: production Dockerfile для backend/gateway, Helm chart или k8s-манифесты, настройка TLS/секретов, CI/CD пайплайн, документация по деплою.
- Затрагиваемые файлы: deploy/*, Dockerfile*, Makefile, docs/README.md, docs/CHANGELOG.md.
- Внешние зависимости: Docker, Kubernetes/Helm, cert-manager, CI/CD (GitHub Actions/GitLab CI).

## Stage 7: Клиентский SDK
- Цель: SDK/клиент для подключения к HTTVPS.
- Задачи: библиотека для handshake и управления потоками, примеры подключения, тесты на совместимость, поддержка мобильных платформ.
- Затрагиваемые файлы: отдельный sdk/* каталог, docs/03-httvps-protocol.md, docs/CHANGELOG.md.
- Внешние зависимости: язык-специфичные SDK-инструменты, WebSocket клиентские библиотеки.

## Stage 8: Админ-управление и конфигурация
- Цель: интерфейс и API для управления тарифами, нодами и настройками.
- Задачи: расширение control-plane API для CRUD тарифов/регионов/нод, UI или CLI для админов, управление лимитами и политиками, аудит действий.
- Затрагиваемые файлы: backend/api/*, backend/services/*, docs/02-control-plane-api.md, docs/01-architecture-overview.md, docs/CHANGELOG.md, README.md.
- Внешние зависимости: UI-фреймворк или CLI-библиотека, authN/authZ решения.

