import contextvars
import uuid
from starlette.types import ASGIApp, Scope, Receive, Send

request_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> None:
    request_id_ctx_var.set(request_id)


def get_request_id() -> str | None:
    return request_id_ctx_var.get()


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid.uuid4())
        token = request_id_ctx_var.set(request_id)

        async def send_wrapper(message: dict):
            if message["type"] == "http.response.start":
                headers = message.get("headers") or []
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_ctx_var.reset(token)
