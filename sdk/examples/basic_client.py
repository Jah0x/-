import asyncio
import json
import websockets
from httvps import HTTVPSClient


class ExampleGateway:
    def __init__(self):
        self.ready = {"type": "ready", "session_id": "example-session", "max_streams": 2}

    async def handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        await websocket.recv()
        await websocket.send(json.dumps(self.ready))
        async for raw in websocket:
            frame = json.loads(raw)
            if frame.get("type") == "stream_data":
                await websocket.send(json.dumps({"type": "stream_data", "stream_id": frame["stream_id"], "data": frame["data"]}))
            if frame.get("type") == "ping":
                await websocket.send(json.dumps({"type": "pong"}))


async def main() -> None:
    gateway = ExampleGateway()
    server = await websockets.serve(gateway.handler, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    client = HTTVPSClient(f"ws://localhost:{port}/ws", "example-token", client_name="example")
    await client.connect()
    stream_id = await client.open_stream("example.com:443")
    await client.send_data(stream_id, b"hello")
    event = await client.next_event(1)
    print(event)
    await client.close_stream(stream_id)
    await client.close()
    server.close()
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
