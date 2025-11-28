# Outline Pool and Node Management

## Node models
- **Outline node:** region, endpoint, access key/credentials, capacity weights, health status, last heartbeat, tags.
- **Gateway node:** region, public endpoint, TLS settings, capacity weights, health status, last heartbeat, tags.
- Backend tracks both types, linking assignments and health data.

## Selection policies
- Default: weighted round-robin within requested region.
- Extensible: prefer nodes with lower load/latency based on heartbeat metrics; support geo and tag filters.
- Fallback: if primary node unhealthy or overloaded, select next candidate and notify usage/audit logs.

## Heartbeat and healthcheck
- Heartbeat payload (JSON): `node_id`, `region`, `uptime_sec`, `active_sessions`, `cpu_load`, `mem_load`, `bytes_up`, `bytes_down`, `last_error`, `timestamp`.
- Gateways and Outline agents post to backend (`/gateway/heartbeat`, `/outline/heartbeat`); backend updates health tables and metrics.
- Health thresholds configurable (timeouts, max load) and drive node availability in selection logic.

## Security of SS secrets
- Store Outline access keys securely (env/secret manager/K8s secrets); avoid logging secrets.
- Rotate access keys on a defined schedule; propagate updates to gateways via secure config channels.
- Limit scope of credentials per region/pool; maintain audit trail for key access and rotation events.
