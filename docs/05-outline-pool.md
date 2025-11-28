# Outline Pool and Node Management

## Node models
- **Outline node:** region, endpoint, access key/credentials, capacity weights, health status, last heartbeat, tags.
- **Gateway node:** region, public endpoint, TLS settings, capacity weights, health status, last heartbeat, tags.
- Backend tracks both types, linking assignments and health data.

## Selection policies
- Текущий алгоритм: поиск активных (`is_active=true`) нод в указанном регионе и выбор первой по возрастанию id. При отсутствии кандидатов в регионе берётся первая активная нода из всего пула.
- Extensible: планируется добавить веса, метрики нагрузки/heartbeat и гибкие фильтры по тегам.
- Fallback: при отсутствии активных нод backend отвечает ошибкой, gateway шлёт `outline_unavailable`.

## Heartbeat and healthcheck
- Heartbeat payload (JSON): `node_id`, `region`, `uptime_sec`, `active_sessions`, `cpu_load`, `mem_load`, `bytes_up`, `bytes_down`, `last_error`, `timestamp`.
- Gateways и Outline агенты отправляют `/gateway/heartbeat` и `/outline/heartbeat`; backend использует `node_id` для обновления `last_heartbeat_at` и признака активности.
- Health thresholds будут расширены на следующем этапе, пока фильтрация основана на `is_active` и наличии heartbeat.

## Security of SS secrets
- Store Outline access keys securely (env/secret manager/K8s secrets); avoid logging secrets.
- Rotate access keys on a defined schedule; propagate updates to gateways via secure config channels.
- Limit scope of credentials per region/pool; maintain audit trail for key access and rotation events.
