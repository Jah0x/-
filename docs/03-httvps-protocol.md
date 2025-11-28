# HTTVPS Protocol

## Purpose
Туннель поверх HTTPS (WebSocket) с мультиплексированными потоками, маскирующийся под обычный TLS-трафик. Полная спецификация описана в `00-spec-httvps.md`.

## Handshake
1. TLS соединение и WebSocket upgrade на `/ws`.
2. Клиент отправляет `hello` JSON-фрейм c временным токеном сессии:
   ```json
   {
     "type": "hello",
     "session_token": "string",
     "version": "1",
     "client": "httvps-cli"
   }
   ```
3. Gateway вызывает backend `/internal/httvps/validate-session`. Успех возвращает идентификатор сессии, лимиты и Outline-ноду. Ошибка завершается кадром `error` и закрытием соединения.
4. При успехе gateway отправляет `ready`:
   ```json
   {"type":"ready","session_id":"uuid","max_streams":8}
   ```
   После этого принимаются кадры потоков.

## Message/frame types
- `ready` — подтверждение handshake и лимиты сессии.
- `stream_open` — `{ "type":"stream_open","stream_id":"s1","target":"host:port" }`.
- `stream_data` — `{ "type":"stream_data","stream_id":"s1","data":"base64" }`, данные кодируются base64.
- `stream_close` — `{ "type":"stream_close","stream_id":"s1","reason":"optional" }`.
- `ping` / `pong` — keepalive.
- `error` — `{ "type":"error","code":"string","message":"string" }`.

## Transport
Все кадры — JSON поверх WebSocket (text), соединение защищено TLS. Первое сообщение после `stream_open` должно содержать Shadowsocks address header перед полезной нагрузкой, чтобы Outline upstream установил TCP к целевому хосту.
