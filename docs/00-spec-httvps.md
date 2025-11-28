# HTTVPS Specification

## Overview
HTTVPS is a multiplexed tunneling protocol running inside a TLS protected WebSocket session (`/ws`). Clients obtain a short-lived session token from the backend, present it during the gateway handshake, and exchange framed messages to open and relay multiple TCP streams. The gateway validates every session via the backend and forwards traffic to a selected Outline upstream node.

## Transport
- TLS is mandatory. Clients connect to the configured HTTPS endpoint and upgrade to WebSocket on `/ws`.
- All frames are UTF-8 JSON messages. Binary frames are not used in this prototype.
- A single WebSocket connection represents one HTTVPS session and can host multiple logical TCP streams.

## Handshake
1. Client establishes TLS and WebSocket to the gateway URL provided by the backend.
2. Client sends `hello` frame:
   ```json
   {
     "type": "hello",
     "session_token": "string",
     "version": "1",
     "client": "optional string"
   }
   ```
3. Gateway calls backend `/internal/httvps/validate-session` with the token. On success backend returns Outline node parameters, device identifier, maximum streams, and a stable session id.
4. Gateway replies with `ready` frame and enters streaming mode:
   ```json
   {
     "type": "ready",
     "session_id": "string",
     "max_streams": 8
   }
   ```
5. On failure gateway replies with `error` frame and closes the socket.

## Frames
- `hello`: handshake request as above.
- `ready`: handshake success with session id and stream limit.
- `stream_open`: `{ "type": "stream_open", "stream_id": "s1", "target": "host:port" }`
- `stream_data`: `{ "type": "stream_data", "stream_id": "s1", "data": "base64" }`
- `stream_close`: `{ "type": "stream_close", "stream_id": "s1", "reason": "optional" }`
- `ping` / `pong`: keepalive.
- `error`: `{ "type": "error", "code": "string", "message": "string" }`

`stream_data` payloads carry raw TCP bytes encoded as base64. Clients should prepend Shadowsocks address headers before application data when targeting Outline.

## Stream lifecycle
1. Client sends `stream_open` with a unique `stream_id`.
2. Gateway allocates upstream connection to the Outline node associated with the session. Duplicate ids or exceeding `max_streams` return an `error` frame.
3. Data moves via paired `stream_data` frames. Gateway echoes upstream responses to the same `stream_id`.
4. Either side may send `stream_close` to release resources. Gateway also closes streams on socket close or protocol violations.

## Error model
Common `error.code` values:
- `bad_hello`: malformed handshake frame.
- `bad_version`: unsupported protocol version.
- `auth_failed`: backend rejected or could not validate session token.
- `session_error`: gateway failed to create/bind session.
- `stream_error`: upstream reported a stream problem (limit, missing stream, or upstream failure).
- `bad_stream`: malformed stream frame or invalid base64.
- `unsupported`: unknown frame type.

Gateway closes the WebSocket after handshake errors. For stream errors, only the offending stream is terminated when possible.

## Limits
- `max_streams` is provided in the `ready` frame (backend may override gateway default).
- Each frame must not exceed 256 KiB encoded size in this prototype.
- Idle sessions may be closed by gateway policy; clients should send `ping` periodically.

## Backend integration
- Clients call `POST /api/v1/httvps/session` with device credentials. Response includes `session_token`, `expires_at`, `gateway_url`, and `max_streams`.
- Gateway validates tokens via `POST /internal/httvps/validate-session` using internal secret authentication. Response carries the session id, device id, max streams, and Outline node descriptor (`host`, `port`, `method`, `password`, `region`, `access_key_id`, `access_url`).
- Tokens are short-lived and single-use for handshake; no raw user credentials traverse the gateway.

## Outline interaction
Gateway binds each validated session to the Outline node returned by the backend and opens Shadowsocks TCP connections per stream. Clients must send a full Shadowsocks address header followed by application bytes in the first `stream_data` payload for each stream.

## Non-compliance handling
Invalid frames, repeated stream ids, or frames referencing unknown streams produce `error` responses. Repeated violations or oversized frames lead to session termination.

## Reference flow
1. Client requests token from backend and receives gateway URL.
2. Client connects to gateway, sends `hello` with token and version `1`.
3. Gateway validates token, responds `ready`.
4. Client sends `stream_open` + `stream_data` with address header + payload.
5. Gateway forwards data to Outline; responses return as `stream_data` frames.
6. Client closes stream and optionally terminates session.
