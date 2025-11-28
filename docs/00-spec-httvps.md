# HTTVPS Specification

## 1. Overview
HTTVPS is a VPN-like tunneling service built on top of HTTPS (WebSocket or HTTP/2) to disguise traffic as regular TLS. A dedicated gateway authenticates devices against the control-plane backend, selects an Outline (Shadowsocks) node, and proxies user traffic through that node. End users interact only with the HTTVPS brand and client application; Outline nodes stay hidden behind the gateway.

## 2. Components
- **Backend (control plane):** user/device/subscription management, region and node catalogs, Outline and gateway pools, traffic accounting, heartbeats, and assignment APIs.
- **Gateway (data plane):** terminates HTTPS/WebSocket connections from clients, authenticates via backend, multiplexes TCP streams, proxies traffic to selected Outline nodes, reports usage and health.
- **Outline pool:** set of Outline servers (Shadowsocks) accessed via technical access keys; not aware of end users directly.
- **Client SDK/app:** initiates HTTVPS sessions over HTTPS, performs handshake and framing, obtains node assignment via backend and gateway, and transports TCP streams.
- **Monitoring/observability:** structured logging and Prometheus-compatible metrics across backend and gateway; dashboards and alerting in later stages.
- **Storage:** PostgreSQL for backend state; optional Redis/message queue for shared state and rate limits in later stages.

## 3. Roadmap / План этапов
Each stage lists purpose, dependencies, key tasks, expected artifacts, and done criteria.

### Stage 0 — Repository bootstrap
- **Goal:** establish base repository layout and tooling for backend, gateway, and docs.
- **Dependencies:** none.
- **Key tasks:** create backend/ and gateway/ skeletons; add docker-compose, .env.example, Makefile; initialize docs and README.
- **Expected artifacts:** `backend/`, `gateway/`, `.gitignore`, `docker-compose.yml`, `Makefile`, `.env.example`, `docs/00-spec-httvps.md`, `docs/CHANGELOG.md`.
- **Done:** repository builds locally with docker-compose stubs; documentation describes structure and setup.

### Stage 1 — Backend MVP (control plane)
- **Goal:** deliver minimal control-plane APIs and data models for device validation and basic usage reporting.
- **Dependencies:** Stage 0.
- **Key tasks:** document architecture and APIs (`docs/01-architecture-overview.md`, `docs/02-control-plane-api.md`, `docs/05-outline-pool.md`); implement FastAPI app layers (api/schemas/models/services); add PostgreSQL models and Alembic migrations; expose `/api/v1/auth/validate-device`, stub `/nodes/assign-outline`, `/usage/report`, `/gateway/heartbeat`, `/outline/heartbeat`; add unit tests.
- **Expected artifacts:** `backend/app/core/config.py`, `backend/app/models/*.py`, `backend/app/schemas/*.py`, `backend/app/services/*.py`, `backend/app/api/v1/*.py`, `backend/alembic/`; `backend/pyproject.toml` or `backend/requirements.txt`; updated docs and changelog.
- **Done:** backend runs locally with migrations, endpoints available, tests passing, docs updated.

### Stage 2 — HTTVPS Gateway MVP
- **Goal:** create HTTPS/WebSocket gateway with initial HTTVPS protocol handshake and backend validation.
- **Dependencies:** Stages 0–1 (backend auth endpoint ready).
- **Key tasks:** define protocol in `docs/03-httvps-protocol.md` and gateway design in `docs/04-gateway-design.md`; implement Go service with TLS termination, hello/auth handshake, validation via backend; basic stream routing to stub upstream; metrics/logging hooks.
- **Expected artifacts:** `gateway/cmd/httvps-gateway/main.go`, `gateway/internal/config/`, `gateway/internal/protocol/`, `gateway/internal/auth/`, `gateway/internal/sessions/`, `gateway/internal/metrics/`, `gateway/tests/`; documentation and changelog updates.
- **Done:** gateway accepts secure connections, performs hello/auth, forwards frames to stub backend/upstream, exposes basic metrics/logs.

### Stage 3 — Outline integration
- **Goal:** enable real traffic proxying through Outline nodes via Shadowsocks.
- **Dependencies:** Stages 0–2.
- **Key tasks:** add Outline client module, secure storage of access keys; connect gateway streams to Outline; update protocol and design docs; run local end-to-end tests.
- **Expected artifacts:** `gateway/internal/outline/`, updates in `gateway/internal/protocol/` and `gateway/internal/sessions/`; revised `docs/04-gateway-design.md`, `docs/05-outline-pool.md`, changelog.
- **Done:** gateway proxies traffic to Outline nodes with validated access keys; documentation reflects integration; basic e2e verified locally.

### Stage 4 — Multi-gateway and Outline pool management
- **Goal:** support multiple gateways and Outline nodes with selection policies and health monitoring.
- **Dependencies:** Stages 0–3.
- **Key tasks:** backend services for node catalog and selection; heartbeat schemas and endpoints; database fields for health/load; gateway-side selector/fallback; enhanced metrics.
- **Expected artifacts:** `backend/app/services/nodes.py`, `backend/app/api/v1/nodes.py`, heartbeat schemas/migrations; updates to `docs/02-control-plane-api.md`, `docs/05-outline-pool.md`; `gateway/internal/outline/selector.go`; expanded metrics.
- **Done:** backend tracks node health/regions; gateway selects nodes with fallback; heartbeat endpoints operational; metrics available.

### Stage 5 — Observability (logging and metrics)
- **Goal:** establish structured logging and Prometheus metrics with baseline dashboards/alerts.
- **Dependencies:** Stages 0–4.
- **Key tasks:** JSON logging formats; Prometheus exporters for backend and gateway; monitoring manifests and dashboards; document architecture impact.
- **Expected artifacts:** `backend/app/core/logging.py`, `gateway/internal/metrics/`, `deploy/monitoring/`; updated `docs/01-architecture-overview.md`, changelog.
- **Done:** structured logs emitted; core metrics exposed; monitoring stack deployable; docs updated.

### Stage 6 — Packaging and deployment
- **Goal:** provide containerization and baseline Kubernetes deployment assets.
- **Dependencies:** Stages 0–5.
- **Key tasks:** Dockerfiles for backend and gateway; docker-compose for local setup; K8s manifests for backend/gateway/postgres/ingress; README deployment notes.
- **Expected artifacts:** `backend/Dockerfile`, `gateway/Dockerfile`, `docker-compose.yml`, `deploy/k8s/backend-deployment.yaml`, `deploy/k8s/gateway-deployment.yaml`, `deploy/k8s/postgres.yaml`, `deploy/k8s/ingress.yaml`; documentation updates.
- **Done:** images build locally; compose and K8s manifests boot services; deployment steps documented.

### Stage 7 — Client SDK (baseline)
- **Goal:** deliver reference HTTVPS client SDK and usage examples.
- **Dependencies:** Stages 0–6 (protocol stable).
- **Key tasks:** document client protocol expectations; implement minimal SDK (e.g., Go/TypeScript); publish examples; update README and protocol doc.
- **Expected artifacts:** `client-sdk/` (language-specific), sample apps; updated `docs/03-httvps-protocol.md`, `README.md`, changelog.
- **Done:** SDK connects via HTTVPS protocol, completes handshake, opens streams; examples run locally; docs reflect SDK APIs.

### Stage 8 — Management and configuration
- **Goal:** provide admin/ops capabilities for plans, users, nodes, and audits.
- **Dependencies:** Stages 0–7.
- **Key tasks:** admin REST API and optional CLI; RBAC roles; audit logging; extend docs for admin flows.
- **Expected artifacts:** `backend/app/api/v1/admin/*`, `backend/app/services/admin/*`, `backend/app/schemas/admin/*`, optional `backend/app/cli.py`; updates to `docs/02-control-plane-api.md`; changelog.
- **Done:** admin endpoints/CLI manage core entities with RBAC; audit events recorded; documentation updated.

## 4. Non-functional Requirements
- **DPI evasion:** tunnel over standard HTTPS with valid TLS; payload framing mimics regular WebSocket/HTTP/2 traffic.
- **Security:** TLS mandatory; device auth via backend-issued tokens; secure handling of Outline access keys; JSON logging without sensitive payloads.
- **Performance/availability:** scalable gateway instances; health checks and heartbeats; minimal protocol overhead; targets defined in assumptions below until finalized.
- **Logging/metrics:** structured JSON logs; Prometheus metrics exposed on backend and gateway; readiness/liveness probes for deployments.
- **Reliability:** graceful connection handling, retries/fallbacks for node selection; migrations for data integrity.

## 5. Coding and Documentation Rules
- No inline code comments or docstrings; explanations live in `docs/*.md` and `CHANGELOG.md`.
- Update relevant documentation and changelog whenever backend/gateway behavior or protocol/API contracts change.
- Architecture is modular: domain logic, transport/protocol, and infrastructure adapters separated; components include backend, gateway, client SDK, management service.
- Logging must be structured JSON with fields such as `request_id`, `user_id`/`device_id`, `node_id`, and outcome codes; avoid sensitive data.
- Metrics: expose baseline Prometheus counters/gauges/histograms for connections, auth successes/failures, stream lifecycle, Outline latency/throughput, and resource usage.

## 6. Assumptions and Open Questions
### Assumptions (defaults, overridable)
- **SLA/performance targets:** per gateway aim for 500–1,000 concurrent sessions, p95 latency <150 ms for auth/assignment, and HTTVPS framing overhead <10% of payload size.
- **Load-balancing policy:** default weighted round-robin within requested region, extensible to load/health-based selection.
- **Heartbeat payload format:** JSON including `node_id`, `region`, `uptime_sec`, `active_sessions`, `cpu_load`, `mem_load`, `bytes_up`, `bytes_down`, `last_error`, `timestamp`.
- **Client SDK languages:** start with Go and TypeScript reference SDKs.
- **RBAC baseline:** admin REST API with roles `admin`, `support`, `read-only`, plus optional CLI wrappers.

### Open Questions (need product decision)
- Final SLA/SLO metrics (TPS, latency, availability) and target regions.
- Detailed policy for storing/protecting Outline access keys and rotation cadence.
- Exact heartbeat intervals/timeouts and metric thresholds for node eviction.
- Supported platforms for client apps (desktop/mobile) and offline/auto-update requirements.
- Preferred channel for configuration delivery (UI portal vs. CLI vs. external system) and audit retention periods.

