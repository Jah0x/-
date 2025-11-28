# Control Plane API

## Principles
- REST/JSON over HTTPS; versioned under `/api/v1/`.
- Auth via backend-issued tokens (JWT or equivalent) attached as Authorization headers.
- All responses include structured error codes; rate limiting and audit logging applied on sensitive endpoints.

## Public client endpoints (baseline)
- `POST /api/v1/auth/validate-device` — validate device token/subscription, return device status and allowed regions.
- `POST /api/v1/nodes/assign-outline` — request Outline node for a device/region; returns node endpoint and access parameters.
- `POST /api/v1/usage/report` — submit usage counters (bytes up/down, session info) per device/session.

## Technical endpoints (gateway/Outline heartbeats)
- `POST /api/v1/gateway/heartbeat` — gateway health payload (node_id, region, uptime, active_sessions, load, traffic counters).
- `POST /api/v1/outline/heartbeat` — Outline node health payload with similar schema; used for pool health and selection.

## Administrative endpoints (draft for Stage 8)
- User and subscription management: CRUD for users, plans, subscriptions, device bindings.
- Node and region management: CRUD for gateway nodes, Outline nodes, regions, weights, and tags.
- RBAC and audit: manage roles (`admin`, `support`, `read-only`), list audit events, rotate credentials.
- Configuration helpers: import/export settings, trigger key rotation for Outline access keys.

