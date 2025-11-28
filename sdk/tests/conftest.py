import asyncio
import json
import pathlib
import sys
from contextlib import suppress

import pytest_asyncio
import websockets

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


class GatewayStub:
    def __init__(self, ready_payload: dict):
        self.ready_payload = ready_payload
        self.received: list[dict] = []
        self.outgoing: asyncio.Queue = asyncio.Queue()

    async def handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        hello = json.loads(await websocket.recv())
        self.received.append(hello)
        await websocket.send(json.dumps(self.ready_payload))
        sender = asyncio.create_task(self._push_outgoing(websocket))
        try:
            async for raw in websocket:
                frame = json.loads(raw)
                self.received.append(frame)
        finally:
            sender.cancel()
            with suppress(asyncio.CancelledError):
                await sender

    async def _push_outgoing(self, websocket: websockets.WebSocketServerProtocol) -> None:
        while True:
            frame = await self.outgoing.get()
            await websocket.send(json.dumps(frame))


@pytest_asyncio.fixture
async def gateway_factory():
    instances: list[tuple[GatewayStub, object]] = []

    async def _start(ready_payload: dict) -> tuple[GatewayStub, object, str]:
        stub = GatewayStub(ready_payload)
        server = await websockets.serve(stub.handler, "localhost", 0)
        instances.append((stub, server))
        port = server.sockets[0].getsockname()[1]
        return stub, server, f"ws://localhost:{port}/ws"

    yield _start

    for stub, server in instances:
        server.close()
        await server.wait_closed()
        while not stub.outgoing.empty():
            stub.outgoing.get_nowait()
