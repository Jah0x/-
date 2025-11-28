# HTTVPS

HTTVPS обеспечивает туннель поверх HTTPS (WebSocket/HTTP/2), который внешне выглядит как обычный HTTPS-трафик. Трафик маршрутизируется через пул Outline-серверов и управляется собственным контрол-плейном.

## Состав
- backend: контрол-плейн на FastAPI и PostgreSQL
- gateway: дата-плейн для HTTPS/WebSocket-трафика
- docs: спецификации и архитектура

## Быстрый старт через docker-compose
1. Скопируйте `.env.example` в `.env` и при необходимости измените параметры.
2. Запустите окружение: `make up` (поднимет PostgreSQL и backend).
3. Логи сервисов: `make logs`.
4. Остановить окружение: `make down`.

Backend поднимается на `${BACKEND_PORT}` и использует PostgreSQL на `${POSTGRES_PORT}`.
