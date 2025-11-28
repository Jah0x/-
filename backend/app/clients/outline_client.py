import httpx
from dataclasses import dataclass


class OutlineClientError(Exception):
    pass


@dataclass
class OutlineKeyData:
    key_id: str
    password: str
    port: int
    method: str | None = None
    access_url: str | None = None


class OutlineClient:
    def __init__(self, api_url: str, api_key: str, timeout: float = 5.0, transport: httpx.AsyncBaseTransport | None = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    async def create_key(self, name: str | None = None) -> OutlineKeyData:
        payload = {}
        if name:
            payload["name"] = name
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.api_url, timeout=self.timeout, headers=headers, transport=self.transport) as client:
            response = await client.post("/access-keys", json=payload)
        if response.status_code not in (200, 201):
            raise OutlineClientError(f"create_key_failed:{response.status_code}")
        data = response.json()
        key_id = str(data.get("id"))
        password = data.get("password") or ""
        port = int(data.get("port")) if data.get("port") is not None else 0
        method = data.get("method")
        access_url = data.get("accessUrl")
        if not key_id:
            raise OutlineClientError("empty_key_id")
        return OutlineKeyData(key_id=key_id, password=password, port=port, method=method, access_url=access_url)

    async def delete_key(self, key_id: str) -> None:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.api_url, timeout=self.timeout, headers=headers, transport=self.transport) as client:
            response = await client.delete(f"/access-keys/{key_id}")
        if response.status_code not in (200, 204, 404):
            raise OutlineClientError(f"delete_key_failed:{response.status_code}")

    async def health_check(self) -> None:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.api_url, timeout=self.timeout, headers=headers, transport=self.transport) as client:
            response = await client.get("/access-keys")
        if response.status_code != 200:
            raise OutlineClientError(f"health_check_failed:{response.status_code}")
