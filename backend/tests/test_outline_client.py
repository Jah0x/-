import pytest
import httpx
from app.clients.outline_client import OutlineClient, OutlineClientError


@pytest.mark.asyncio
async def test_outline_client_create_key_success():
    async def handler(request):
        assert request.headers.get("Authorization") == "Bearer secret"
        return httpx.Response(201, json={"id": "k1", "password": "pwd", "port": 1234, "method": "aes-256-gcm", "accessUrl": "ss://"})

    transport = httpx.MockTransport(handler)
    client = OutlineClient("https://outline", "secret", transport=transport)
    key = await client.create_key("name")
    assert key.key_id == "k1"
    assert key.password == "pwd"
    assert key.port == 1234
    assert key.method == "aes-256-gcm"
    assert key.access_url == "ss://"


@pytest.mark.asyncio
async def test_outline_client_create_key_failure():
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    client = OutlineClient("https://outline", "secret", transport=transport)
    with pytest.raises(OutlineClientError):
        await client.create_key("name")
