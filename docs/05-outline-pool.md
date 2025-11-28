# Outline Pool and Node Management

## Node and pool models
- **Outline node:** region, endpoint, access key/credentials, capacity weights, health status, last heartbeat, tags.
- **Gateway node:** region, public endpoint, TLS settings, capacity weights, health status, last heartbeat, tags.
- **Outline pool:** код, имя, `is_default`, `is_active`.
- **Outline pool node:** связь пула с конкретной Outline-нодой, `priority`, `is_active` для мягкого выключения без удаления.
- **Outline pool region:** приоритезирует регионы для пула (`priority`, `is_active`), чтобы выбрать ближайший регион при отсутствии явного запроса.
- Backend отслеживает и ноды, и пуловые связи, использует их при выдаче назначения в `assign_outline_node`.

## Selection policies
- Алгоритм Stage 5: ищет активные (`is_active=true`, `is_deleted=false`) ноды в регионе; если нет — любой регион. Из списка отбрасывает `last_check_status=down`, приоритет отдаётся `healthy`, при отсутствии берутся `degraded`/`unknown`. Порядок внутри группы сохраняет сортировку по `priority` и `id`.
- Расширение пула: запрос `/api/v1/nodes/assign-outline` принимает `pool_code`, backend ищет активный пул (`outline_pools`), затем выбирает ноды из `outline_pool_nodes` с учётом регионов (`outline_pool_regions` → явный `region_code` → остальные).
- Extensible: планируется добавить веса, метрики нагрузки/heartbeat и гибкие фильтры по тегам.
- Fallback: при отсутствии активных нод — ошибка `no_outline_nodes_available`, при наличии только `down` — ошибка `no_healthy_outline_nodes`; при неизвестном пуле — `outline_pool_not_found`; gateway транслирует понятный ответ клиенту.

## Heartbeat and healthcheck
- Heartbeat payload (JSON): `node_id`, `region`, `uptime_sec`, `active_sessions`, `cpu_load`, `mem_load`, `bytes_up`, `bytes_down`, `last_error`, `timestamp`.
- Gateways и Outline агенты отправляют `/gateway/heartbeat` и `/outline/heartbeat`; backend использует `node_id` для обновления `last_heartbeat_at`.
- Периодический health-check Outline: фоновой воркер запрашивает `/access-keys` с таймаутом `OUTLINE_HEALTHCHECK_TIMEOUT_SECONDS`, измеряет latency и присваивает статус `healthy`/`degraded`/`down` по порогу `OUTLINE_HEALTHCHECK_DEGRADED_THRESHOLD_MS`. Результат сохраняется в полях `last_check_at`, `last_check_status`, `recent_latency_ms`, `last_error` и доступен через admin API.

## Gateway state sync
- OutlineUpstream может сохранять привязки сессий к пулам и нодам в стор: `memory` (по умолчанию), Redis (`GATEWAY_REDIS_*`), NATS KV (`GATEWAY_NATS_*`). TTL задаётся `GATEWAY_SESSION_STORE_TTL`.
- При старте другого экземпляра привязки подтягиваются из стора: `OpenStream` загрузит Outline-нодe из Redis/NATS и продолжит поток без ручной миграции.
- `UnbindSession` очищает стор при закрытии WebSocket, закрывает все открытые потоки.

## Security of SS secrets
- Store Outline access keys securely (env/secret manager/K8s secrets); avoid logging secrets.
- Rotate access keys on a defined schedule; propagate updates to gateways via secure config channels.
- Limit scope of credentials per region/pool; maintain audit trail for key access and rotation events.
