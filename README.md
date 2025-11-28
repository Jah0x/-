# HTTVPS

HTTVPS обеспечивает туннель поверх HTTPS (WebSocket/HTTP/2), который внешне выглядит как обычный HTTPS-трафик. Трафик маршрутизируется через пул Outline-серверов и управляется собственным контрол-плейном.

## Состав
- backend: контрол-плейн на FastAPI и PostgreSQL
- gateway: дата-плейн для HTTPS/WebSocket-трафика
- docs: спецификации и архитектура

## Быстрый старт через docker-compose
1. Скопируйте `.env.example` в `.env` и при необходимости измените параметры.
2. Запустите окружение: `make up` (поднимет PostgreSQL и backend).
3. Примените миграции в контейнере backend: `docker-compose exec backend alembic upgrade head`.
4. Логи сервисов: `make logs`.
5. Остановить окружение: `make down`.

Backend поднимается на `${BACKEND_PORT}` и использует PostgreSQL на `${POSTGRES_PORT}`. Основные переменные задаются в `.env`: параметры Postgres (`POSTGRES_*`), строка подключения backend (`BACKEND_DB_DSN`), секретный ключ и настройки JWT.
