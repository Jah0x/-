# Architecture Overview

## High-level architecture
- **Backend (control plane):** manages users, devices, subscriptions, regions, gateway/Outline nodes, and exposes REST APIs for device validation, node assignment, usage reporting, and heartbeats.
- **Gateway (data plane):** terminates HTTPS (WebSocket/HTTP/2) connections, performs HTTVPS handshake, multiplexes TCP streams, and proxies traffic to Outline nodes.
- **Outline pool:** Shadowsocks servers accessed via technical access keys; unaware of end users.
- **Client (app/SDK):** initiates HTTVPS sessions, performs handshake, opens streams, and relays traffic.
- **Observability:** structured JSON logs and Prometheus metrics across backend and gateway; dashboards/alerts delivered in later stages.

## Flows
- **Device authentication:** client calls backend `/api/v1/auth/validate-device`; backend validates token/subscription and returns device status plus assignment hints.
- **Node assignment:** client/gateway requests an Outline node (region-aware) from backend; backend applies policy and returns target node plus access parameters.
- **HTTVPS tunnel establishment:** client opens HTTPS (WebSocket/HTTP/2) to gateway, performs hello/auth handshake (per `docs/03-httvps-protocol.md`), then opens multiplexed streams.
- **Traffic proxying:** gateway maps HTTVPS streams to Shadowsocks connections toward the assigned Outline node and relays data bidirectionally.
- **Usage and heartbeat reporting:** gateway reports usage to backend (`/usage/report`) and sends heartbeat payloads for gateway/Outline nodes; backend persists metrics and health data.

## Component responsibilities
- **Backend:** identity/subscription verification, node registry, assignment logic, heartbeat ingestion, usage accounting, admin/RBAC interfaces.
- **Gateway:** TLS termination, protocol handling, stream/session lifecycle, Outline connectivity, local metrics/logging.
- **Outline nodes:** provide outbound internet access via Shadowsocks, expose health data (if available) to gateway/backend.
- **Client SDK/app:** handles tokens, handshake, stream management, retries/fallbacks, and integrates with platform VPN stack if applicable.
- **Monitoring stack:** collects metrics/logs, powers dashboards and alerts for availability and performance.
