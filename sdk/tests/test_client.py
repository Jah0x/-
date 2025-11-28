import asyncio
import base64
import pytest
from httvps.client import HTTVPSClient, HTTVPSError


async def wait_for_messages(stub, count: int) -> None:
    for _ in range(100):
        if len(stub.received) >= count:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("messages_not_received")


@pytest.mark.asyncio
async def test_handshake_and_ready(gateway_factory):
    stub, server, url = await gateway_factory({"type": "ready", "session_id": "s1", "max_streams": 2})
    client = HTTVPSClient(url, "token-1", client_name="sdk")
    try:
        await client.connect()
        await wait_for_messages(stub, 1)
        assert stub.received[0]["type"] == "hello"
        assert stub.received[0]["session_token"] == "token-1"
        assert stub.received[0]["version"] == "1"
        assert stub.received[0]["client"] == "sdk"
        assert client.session_id == "s1"
        assert client.max_streams == 2
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_stream_roundtrip(gateway_factory):
    stub, server, url = await gateway_factory({"type": "ready", "session_id": "s2", "max_streams": 4})
    client = HTTVPSClient(url, "token-2")
    try:
        await client.connect()
        stream_id = await client.open_stream("example.com:443")
        await client.send_data(stream_id, b"payload")
        encoded = base64.b64encode(b"payload").decode()
        await wait_for_messages(stub, 3)
        assert stub.received[1] == {"type": "stream_open", "stream_id": stream_id, "target": "example.com:443"}
        assert stub.received[2] == {"type": "stream_data", "stream_id": stream_id, "data": encoded}
        await stub.outgoing.put({"type": "stream_data", "stream_id": stream_id, "data": encoded})
        response = await client.next_event(1)
        assert response["type"] == "stream_data"
        assert base64.b64decode(response["data"]) == b"payload"
        await client.close_stream(stream_id, "done")
        await wait_for_messages(stub, 4)
        assert stub.received[-1]["type"] == "stream_close"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_stream_limit_respected(gateway_factory):
    stub, server, url = await gateway_factory({"type": "ready", "session_id": "s3", "max_streams": 1})
    client = HTTVPSClient(url, "token-3")
    try:
        await client.connect()
        await client.open_stream("first:80", "s-first")
        await wait_for_messages(stub, 2)
        with pytest.raises(HTTVPSError):
            await client.open_stream("second:81", "s-second")
        assert stub.received[1]["stream_id"] == "s-first"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()
