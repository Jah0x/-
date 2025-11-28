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
- Логика: ищет активные Outline-ноды в указанном регионе, при отсутствии — берёт любую активную ноду (с учётом `priority`). При наличии `api_url`/`api_key` создаёт на Outline сервере персональный access-key и сохраняет его в БД. Ноды со статусом `down` игнорируются, `healthy` имеют приоритет над `degraded`/`unknown`.
- Успех: `{ "node_id": int, "host": "string", "port": int, "method": "string|null", "password": "string|null", "region": "string|null", "access_key_id": "string|null", "access_url": "string|null" }`.
- Ошибка: HTTP 503 с `{ "detail": "no_outline_nodes_available" }`, если нет активных нод, `{ "detail": "no_healthy_outline_nodes" }`, если все отмечены `down`, либо текстом ошибки провижининга Outline.

### POST /api/v1/nodes/revoke-outline
- Вход: `{ "device_id": "string" }`.
- Логика: находит последний неотозванный Outline access-key для устройства, помечает его `revoked=true`, пытается вызвать удаление ключа через Outline API (ошибка удаления не фатальна).
- Успех: `{ "revoked": true|false }` (false, если активных ключей не найдено).
- Ошибка: HTTP 404 с `{ "detail": "device_not_found" }` при отсутствии устройства.

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

### GET /api/v1/admin/outline-nodes
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает список Outline-нод с полями `id`, `name`, `host`, `port`, `region`, `tag`, `priority`, `is_active`, `last_check_status`, `last_check_at`, `recent_latency_ms`, `last_error`, `active_access_keys`.

### GET /api/v1/admin/outline-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает детальный статус указанной Outline-ноды в том же формате, что и список.

### POST /api/v1/admin/outline-nodes/{id}/check
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Запускает немедленный health-check ноды и возвращает актуальный статус.

### GET /api/v1/admin/plans
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает список тарифов с полями `id`, `name`, `description`, `traffic_limit`, `period_days`, `price`.

### POST /api/v1/admin/plans
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Создаёт тариф, вход: `name`, опционально `description`, `traffic_limit`, `period_days`, `price`. Возвращает созданный тариф.

### GET /api/v1/admin/plans/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает тариф по id или 404.

### PUT /api/v1/admin/plans/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Обновляет произвольные поля тарифа (пустое тело — 400), на успех отдаёт свежую версию, 404 если не найден.

### DELETE /api/v1/admin/plans/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Удаляет тариф, на успех `{ "status": "deleted" }`, 404 если не найден.

### GET /api/v1/admin/regions
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает список регионов `id`, `code`, `name`.

### POST /api/v1/admin/regions
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Создаёт регион по `code` и `name`. При дубликате `code` отдаёт 409 `region_code_exists`.

### GET /api/v1/admin/regions/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает регион по id или 404.

### PUT /api/v1/admin/regions/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Обновляет регион (допускается смена `code` с проверкой уникальности). Пустое тело даёт 400 `empty_body`, 404 при отсутствии региона, 409 при конфликте `code`.

### DELETE /api/v1/admin/regions/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Удаляет регион, на успех `{ "status": "deleted" }`.

### GET /api/v1/admin/outline-nodes
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает конфигурацию активных Outline-нод: `id`, `name`, `region`, `host`, `port`, `method`, `password`, `api_url`, `api_key`, `tag`, `priority`, `is_active`, `is_deleted`.

### POST /api/v1/admin/outline-nodes
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Создаёт Outline-ноду (опционально `region_code`). Невалидный регион даёт 404 `region_not_found`. Возвращает созданную конфигурацию.

### GET /api/v1/admin/outline-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает конфигурацию ноды или 404.

### PUT /api/v1/admin/outline-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Обновляет поля ноды, допускает перенос в другой регион (`region_code`), активирует/деактивирует `is_active`. Пустое тело даёт 400, отсутствующий регион — 404 `region_not_found`, несуществующая нода — 404 `not_found`.

### DELETE /api/v1/admin/outline-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Помечает ноду удалённой и деактивирует, ответ `{ "status": "deleted" }`.

### GET /api/v1/admin/gateway-nodes
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает конфигурации gateway-нод: `id`, `region`, `host`, `port`, `is_active`.

### POST /api/v1/admin/gateway-nodes
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Создаёт gateway-ноду, `region_code` опционален. Неизвестный регион даёт 404 `region_not_found`.

### GET /api/v1/admin/gateway-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает конфигурацию gateway-ноды или 404.

### PUT /api/v1/admin/gateway-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Обновляет хост/порт/регион и статус активности. Пустое тело — 400, неизвестный регион — 404 `region_not_found`, отсутствующая нода — 404 `not_found`.

### DELETE /api/v1/admin/gateway-nodes/{id}
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Удаляет ноду, ответ `{ "status": "deleted" }`.

### GET /api/v1/admin/audit
- Требует заголовок `X-Admin-Token: <BACKEND_SECRET_KEY>`.
- Возвращает последние записи аудита (limit по умолчанию 100, ограничен 1000) с полями `id`, `actor`, `action`, `resource_type`, `resource_id`, `payload`, `created_at`.

## Модели данных
- Пользователь (`users`): id, email, is_active, created_at, updated_at.
- План (`plans`): id, name, description, traffic_limit, period_days, price.
- Регион (`regions`): id, code, name.
- Устройство (`devices`): id, user_id, device_id, created_at.
- Подписка (`subscriptions`): id, user_id, plan_id, valid_until, status, created_at, updated_at.
- Outline-нода (`outline_nodes`): id, name, region_id, host, port, method, password, api_url, api_key, tag, priority, is_active, is_deleted, last_heartbeat_at, last_check_at, last_check_status, last_error, recent_latency_ms.
- Outline-ключ (`outline_access_keys`): id, device_id, outline_node_id, access_key_id, password, method, port, access_url, revoked, created_at.
- Gateway-нода (`gateway_nodes`): id, region_id, host, port, is_active, last_heartbeat_at.
- Сессия (`sessions`): id, device_id, outline_node_id, gateway_node_id, started_at, ended_at, bytes_up, bytes_down, status.
- Аудит админских действий (`admin_audit_logs`): id, actor, action, resource_type, resource_id, payload (JSON), created_at.
