# HTTVPS

HTTVPS обеспечивает туннель поверх HTTPS (WebSocket/HTTP/2), который внешне выглядит как обычный HTTPS-трафик. Трафик маршрутизируется через пул Outline-серверов и управляется собственным контрол-плейном.

## Состав
- backend: контрол-плейн на FastAPI и PostgreSQL
- gateway: дата-плейн для HTTPS/WebSocket-трафика
- docs: спецификации и архитектура

## Быстрый старт через docker-compose
1. Скопируйте `.env.example` в `.env` и при необходимости измените параметры.
2. Запустите окружение: `make up` (поднимет PostgreSQL, backend и gateway).
3. Примените миграции в контейнере backend: `docker-compose exec backend alembic upgrade head`.
4. Логи сервисов: `make logs`.
5. Остановить окружение: `make down`.

Backend поднимается на `${BACKEND_PORT}` и использует PostgreSQL на `${POSTGRES_PORT}`. Gateway слушает `${GATEWAY_LISTEN_ADDR}` с TLS-сертификатами из `deploy/certs`.

## Gateway (MVP)
- HTTPS + WebSocket-туннель, JSON-фреймы по спецификации из `docs/03-httvps-protocol.md`.
- Handshake через кадр `hello`, валидацию устройства в backend и назначение Outline-ноды (режим `outline`).
- Поддержка кадров `stream_open` / `stream_data` / `stream_close`; upstream выбирается конфигом `GATEWAY_UPSTREAM_MODE` (`fake` по умолчанию, `outline` для реального Shadowsocks).
- Метрики Prometheus на `/metrics` при включённом флаге.

### Ручная проверка соединения
1. Поднимите сервисы: `make up` и примените миграции.
2. Подготовьте токен устройства через backend (используйте уже существующий эндпоинт `/api/v1/auth/validate-device`).
3. Подключитесь WebSocket-клиентом к `wss://localhost:8443/ws` с отключённой проверкой сертификата (например, `npx wscat --no-check -c wss://localhost:8443/ws`).
4. Отправьте `hello`:
   ```json
   {"type":"hello","device_id":"<device>","token":"<token>","client_version":"1.0"}
   ```
5. После `auth_result` отправьте:
   ```json
   {"type":"stream_open","stream_id":"s1"}
   {"type":"stream_data","stream_id":"s1","data":"aGVsbG8="}
   ```
   В ответ придёт эхо `stream_data` с тем же `data`.

## Документация
Полный набор спецификаций расположен в `docs/*.md`, включая протокол, архитектуру и дорожную карту разработки.

## Дорожная карта
- Stage 0: инициализация репозитория (структура, окружение, базовые правила).
- Stage 1: backend MVP (контрол-плейн, БД, аутентификация устройств).
- Stage 2: gateway MVP (WebSocket-туннель, заглушка upstream, метрики).
- Stage 3: интеграция с Outline (assign из backend, OutlineUpstream, переключаемый режим fake/outline).

Подробнее: [docs/00-dev-plan.md](docs/00-dev-plan.md).
