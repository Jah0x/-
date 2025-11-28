import asyncio
import base64
import json
import websockets


class HTTVPSError(Exception):
    pass


class HTTVPSClient:
    def __init__(self, url: str, session_token: str, version: str = "1", client_name: str | None = None):
        self.url = url
        self.session_token = session_token
        self.version = version
        self.client_name = client_name
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self.session_id: str | None = None
        self.max_streams: int | None = None
        self._receiver_task: asyncio.Task | None = None
        self._events: asyncio.Queue = asyncio.Queue()
        self._streams: set[str] = set()
        self._counter = 0
        self._closed = False

    async def connect(self) -> None:
        if self.websocket:
            return
        self.websocket = await websockets.connect(self.url)
        await self._send_json(self._hello_frame())
        ready = await self._recv_json()
        if ready.get("type") != "ready":
            raise HTTVPSError("handshake_failed")
        self.session_id = ready.get("session_id")
        self.max_streams = ready.get("max_streams")
        self._receiver_task = asyncio.create_task(self._receiver())

    async def _receiver(self) -> None:
        assert self.websocket is not None
        try:
            async for raw in self.websocket:
                frame = json.loads(raw)
                if frame.get("type") == "ping":
                    await self._send_json({"type": "pong"})
                    continue
                if frame.get("type") == "stream_close":
                    self._streams.discard(frame.get("stream_id"))
                await self._events.put(frame)
        except websockets.ConnectionClosed as exc:
            await self._events.put({"type": "closed", "code": exc.code, "reason": exc.reason})
        except Exception as exc:
            await self._events.put({"type": "closed", "reason": str(exc)})
        finally:
            self._closed = True

    async def open_stream(self, target: str, stream_id: str | None = None) -> str:
        if self.websocket is None:
            raise HTTVPSError("not_connected")
        if stream_id is None:
            self._counter += 1
            stream_id = f"s{self._counter}"
        if self.max_streams is not None and stream_id not in self._streams and len(self._streams) >= self.max_streams:
            raise HTTVPSError("stream_limit")
        self._streams.add(stream_id)
        await self._send_json({"type": "stream_open", "stream_id": stream_id, "target": target})
        return stream_id

    async def send_data(self, stream_id: str, payload: bytes) -> None:
        if self.websocket is None:
            raise HTTVPSError("not_connected")
        if stream_id not in self._streams:
            raise HTTVPSError("unknown_stream")
        encoded = base64.b64encode(payload).decode()
        await self._send_json({"type": "stream_data", "stream_id": stream_id, "data": encoded})

    async def close_stream(self, stream_id: str, reason: str | None = None) -> None:
        if self.websocket is None:
            raise HTTVPSError("not_connected")
        if stream_id in self._streams:
            await self._send_json({"type": "stream_close", "stream_id": stream_id, "reason": reason})
            self._streams.discard(stream_id)

    async def next_event(self, timeout: float | None = None) -> dict:
        return await asyncio.wait_for(self._events.get(), timeout=timeout)

    async def send_ping(self) -> None:
        if self.websocket is None:
            raise HTTVPSError("not_connected")
        await self._send_json({"type": "ping"})

    async def close(self) -> None:
        if self.websocket is not None and not self._closed:
            await self.websocket.close()
        if self._receiver_task:
            await asyncio.gather(self._receiver_task, return_exceptions=True)

    def _hello_frame(self) -> dict:
        frame = {
            "type": "hello",
            "session_token": self.session_token,
            "version": self.version,
        }
        if self.client_name:
            frame["client"] = self.client_name
        return frame

    async def _send_json(self, payload: dict) -> None:
        assert self.websocket is not None
        await self.websocket.send(json.dumps(payload))

    async def _recv_json(self) -> dict:
        assert self.websocket is not None
        raw = await self.websocket.recv()
        return json.loads(raw)
