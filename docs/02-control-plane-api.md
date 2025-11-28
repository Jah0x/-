# Control Plane API

## Базовые принципы
- REST/JSON, версионирование под `/api/v1`.
- Авторизация устройств через JWT-токены, выпускаемые backend.
- Все ответы содержат предсказуемые структуры успеха/ошибок.

## Маршруты
### GET /api/v1/health
Возвращает `{ "status": "ok" }` для проверки доступности.

### POST /api/v1/auth/validate-device
- Вход: `{ "device_id": "string", "token": "jwt" }`
- Логика: проверка токена, поиск устройства, проверка активной подписки.
- Успех: `{ "allowed": true, "user_id": int, "subscription_status": "active" }`
- Ошибка: HTTP 403 с `{ "allowed": false, "reason": "..." }`

### POST /api/v1/nodes/assign-outline
- Вход: `{ "device_id": "string", "region_code": "string|null" }`
- Сейчас возвращает статический узел для разработки: `{ "host": "outline.example.com", "port": 12345, "method": "aes-256-gcm", "password": "placeholder", "region": "<region_code>" }`

### POST /api/v1/usage/report
- Вход: `{ "session_id": int|null, "device_id": "string", "bytes_up": int, "bytes_down": int }`
- Выход: `{ "status": "accepted" }`

### POST /api/v1/gateway/heartbeat
- Вход: `{ "node_id": int|null, "region": "string|null", "status": "string|null" }`
- Выход: `{ "status": "ok" }`

### POST /api/v1/outline/heartbeat
- Вход: `{ "node_id": int|null, "region": "string|null", "status": "string|null" }`
- Выход: `{ "status": "ok" }`

## Модели данных
- Пользователи, устройства, планы, подписки, регионы, gateway/outline-ноды, сессии — описаны в SQLAlchemy-моделях backend.
- Первая миграция Alembic создаёт все таблицы и базовые поля для дальнейших этапов.
