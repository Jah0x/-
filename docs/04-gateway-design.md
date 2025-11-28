# Gateway Design

## Architecture
- **Acceptor:** TLS termination and WebSocket/HTTP/2 upgrade handling.
- **Auth layer:** processes hello frames, validates device tokens via backend `/auth/validate-device`.
- **Session manager:** tracks HTTVPS sessions and multiplexed streams, enforces limits and timeouts.
- **Outline client:** maintains connections to assigned Outline nodes (Shadowsocks), handles failover/fallback.
- **Metrics/logging:** structured JSON logs and Prometheus metrics for handshakes, streams, and Outline connectivity.

## Session lifecycle
1. Client establishes TLS and initiates hello.
2. Gateway validates device with backend, obtains or confirms Outline node assignment.
3. Session is created with stream window/configuration; metrics counters start.
4. Client opens `stream_open`; gateway maps to Outline connection; forwards `stream_data` bidirectionally.
5. On `stream_close` or errors, gateway tears down mappings, updates usage counters, and reports as needed.
6. Gateway periodically sends usage reports and heartbeats to backend.

## WebSocket/HTTP2 handling
- Initial implementation may use WebSocket framing with JSON; HTTP/2 data frames supported where deployment requires.
- Binary framing is a later optimization; message definitions stay aligned with `docs/03-httvps-protocol.md`.
- Keep-alives via ping/pong; timeouts trigger session cleanup.

## Logging and metrics
- **Logs:** JSON with `request_id`, `session_id`, `device_id`, `node_id`, result codes, byte counters, timing.
- **Metrics:** Prometheus counters/gauges/histograms for connections, auth outcomes, active streams, bytes in/out, Outline latency/errors, heartbeat status.
