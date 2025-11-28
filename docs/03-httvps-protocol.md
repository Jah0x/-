# HTTVPS Protocol

## Purpose
Provide a VPN-like tunnel over HTTPS (WebSocket or HTTP/2) that blends with regular TLS traffic while enabling multiplexed TCP streams to Outline nodes.

## Handshake
1. **TLS establishment** between client and gateway.
2. **Hello frame** from client with client version, device token, desired region, capabilities.
3. **Auth/validate** by gateway via backend `/auth/validate-device`; gateway responds with accept/reject and session parameters.
4. **Session setup** including node assignment (if not pre-fetched) and stream window parameters.

## Message/frame types
- `hello` — client capabilities, token, region preference.
- `auth_result` — accept/reject, assigned region/node hints.
- `stream_open` — open logical TCP stream with `stream_id` and target metadata.
- `stream_data` — payload chunks for a stream (binary/base64 framing depending on transport mode).
- `stream_close` — terminate logical stream with reason code.
- `ping` / `pong` — liveness checks.
- `error` — structured error codes (e.g., `LIMIT_REACHED`, `AUTH_FAILED`, `NODE_UNAVAILABLE`).

## Encryption and transport
- All traffic runs over TLS with standard ciphers; certificate management handled by gateway deployment.
- WebSocket text/binary frames or HTTP/2 data frames may carry JSON in early versions; binary framing is allowed in optimized iterations.
- Payload encryption beyond TLS is optional; sensitive identifiers kept out of payload where possible.
