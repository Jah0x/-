# HTTVPS Protocol

## Purpose
Туннель поверх HTTPS (WebSocket/HTTP/2) с мультиплексированными потоками, маскирующийся под обычный TLS-трафик.

## Handshake
1. TLS соединение между клиентом и gateway.
2. WebSocket upgrade на `/ws`.
3. Клиент отправляет `hello` JSON-фрейм:
   ```json
   {
     "type": "hello",
     "device_id": "string",
     "token": "jwt",
     "client_version": "string",
     "capabilities": ["string"],
     "region": "string"
   }
   ```
4. Gateway вызывает backend `/api/v1/auth/validate-device` и возвращает `auth_result`:
   ```json
   {"type":"auth_result","allowed":true,"session_id":"uuid","subscription_status":"active"}
   ```
   При отказе: `{ "type":"auth_result","allowed":false,"reason":"invalid_token" }` и соединение закрывается.
5. После успеха клиент открывает потоки.

## Message/frame types
- `hello` — стартовый кадр handshake.
- `auth_result` — подтверждение/отказ сессии, `session_id` выдаётся gateway.
- `stream_open` — `{ "type":"stream_open","stream_id":"s1","target":"optional" }`.
- `stream_data` — `{ "type":"stream_data","stream_id":"s1","data":"base64" }`, данные кодируются base64.
- `stream_close` — `{ "type":"stream_close","stream_id":"s1","reason":"optional" }`.
- `ping` / `pong` — keepalive.
- `error` — `{ "type":"error","code":"string","message":"string" }`.

## Transport
- Все кадры — JSON поверх WebSocket (text), соединение защищено TLS.
- В версии MVP payload передаётся в base64, binary-фреймы будут добавлены в оптимизациях.

