# Control Plane API

## Базовые принципы
- REST/JSON, версионирование под `/api/v1`.
- Авторизация устройств через JWT-токены, выпускаемые backend.
- Все ответы содержат предсказуемые структуры успеха/ошибок.

## Маршруты
### GET /api/v1/health
Возвращает `{ "status": "ok" }` для проверки доступности.

### POST /api/v1/auth/validate-device
- Вход: `{ "device_id": "string", "token": "jwt" }`.
- Логика: проверка подписи/срока JWT, совпадение device_id, поиск устройства в БД, наличие активной подписки.
- Успех: `{ "allowed": true, "user_id": int, "subscription_status": "active" }`.
- Ошибка: HTTP 403 с `{ "allowed": false, "reason": "device_not_found|no_active_subscription|invalid_token|device_mismatch" }`.

### POST /api/v1/nodes/assign-outline
- Вход: `{ "device_id": "string", "region_code": "string|null" }`
- Логика: ищет активные Outline-ноды в указанном регионе, при отсутствии — берёт любую активную ноду (с учётом `priority`). При наличии `api_url`/`api_key` создаёт на Outline сервере персональный access-key и сохраняет его в БД.
- Успех: `{ "node_id": int, "host": "string", "port": int, "method": "string|null", "password": "string|null", "region": "string|null", "access_key_id": "string|null", "access_url": "string|null" }`.
- Ошибка: HTTP 503 с `{ "detail": "no_outline_nodes_available" }`, если нет активных нод, либо текстом ошибки провижининга Outline.

### POST /api/v1/usage/report
- Вход: `{ "session_id": int|null, "device_id": "string", "bytes_up": int, "bytes_down": int }`
- Действие: при наличии `session_id` увеличивает счётчики bytes_up/bytes_down сессии; иначе просто подтверждает приём.
- Выход: `{ "status": "accepted" }`

### POST /api/v1/gateway/heartbeat
- Вход: `{ "node_id": int|null, "region": "string|null", "status": "string|null", "uptime_sec": int?, "active_sessions": int?, "cpu_load": float?, "mem_load": float?, "bytes_up": int?, "bytes_down": int?, "last_error": "string|null", "timestamp": "iso-datetime|null" }`.
- Действие: при наличии node_id обновляет `last_heartbeat_at` gateway-ноды, иначе возвращает `ignored`.
- Выход: `{ "status": "ok|ignored" }`.

### POST /api/v1/outline/heartbeat
- Вход: тот же формат, что и для gateway heartbeat.
- Действие: при наличии node_id обновляет `last_heartbeat_at` Outline-ноды, иначе возвращает `ignored`.
- Выход: `{ "status": "ok|ignored" }`.

## Модели данных
- Пользователь (`users`): id, email, is_active, created_at, updated_at.
- План (`plans`): id, name, description, traffic_limit, period_days, price.
- Регион (`regions`): id, code, name.
- Устройство (`devices`): id, user_id, device_id, created_at.
- Подписка (`subscriptions`): id, user_id, plan_id, valid_until, status, created_at, updated_at.
- Outline-нода (`outline_nodes`): id, name, region_id, host, port, method, password, api_url, api_key, tag, priority, is_active, is_deleted, last_heartbeat_at.
- Outline-ключ (`outline_access_keys`): id, device_id, outline_node_id, access_key_id, password, method, port, access_url, revoked, created_at.
- Gateway-нода (`gateway_nodes`): id, region_id, host, port, is_active, last_heartbeat_at.
- Сессия (`sessions`): id, device_id, outline_node_id, gateway_node_id, started_at, ended_at, bytes_up, bytes_down, status.
