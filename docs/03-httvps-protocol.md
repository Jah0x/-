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

## SDK handshake
- SDK открывает WebSocket и сразу отправляет `hello` с `session_token`, `version` и произвольным `client`.
- Успешный `ready` сохраняет `session_id` и `max_streams`, после чего запускается приём событий с автоматическим ответом `pong`.
- Если `ready` не приходит, соединение завершается с ошибкой `handshake_failed`.

## SDK управление потоками
- Клиент автоматически нумерует потоки `s1`, `s2`, ... если идентификатор не передан явно.
- При превышении `max_streams` выбрасывается ошибка `stream_limit` без отправки `stream_open`.
- Все вызовы `send_data` кодируют байты в base64 и отправляют `stream_data` только для активных потоков, иначе ошибка `unknown_stream`.
- `next_event(timeout)` возвращает любые входящие кадры (включая `stream_close` и `error`); для `ping` отправляется `pong` и событие не возвращается пользователю.

## Transport
Все кадры — JSON поверх WebSocket (text), соединение защищено TLS. Первое сообщение после `stream_open` должно содержать Shadowsocks address header перед полезной нагрузкой, чтобы Outline upstream установил TCP к целевому хосту.
