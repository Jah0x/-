import time
from prometheus_client import Counter, Histogram, Gauge, CONTENT_TYPE_LATEST, generate_latest
from fastapi import APIRouter
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

REQUESTS_TOTAL = Counter(
    "backend_http_requests_total",
    "Total HTTP requests processed by backend",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "backend_http_request_duration_seconds",
    "Backend HTTP request latency in seconds",
    ["method", "path"],
)
IN_PROGRESS = Gauge(
    "backend_http_requests_in_progress",
    "Number of backend HTTP requests currently in progress",
)
REQUEST_EXCEPTIONS = Counter(
    "backend_http_request_exceptions_total",
    "Exceptions raised while handling backend HTTP requests",
    ["path"],
)


class MetricsMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "")
        path = scope.get("path", "")
        start = time.perf_counter()
        status_code: dict[str, int] = {}
        IN_PROGRESS.inc()

        async def send_wrapper(message: dict):
            if message["type"] == "http.response.start":
                status_code["value"] = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            REQUEST_EXCEPTIONS.labels(path=path).inc()
            status_code["value"] = status_code.get("value", 500)
            raise
        finally:
            duration = time.perf_counter() - start
            code = str(status_code.get("value", 500))
            REQUESTS_TOTAL.labels(method=method, path=path, status=code).inc()
            REQUEST_DURATION.labels(method=method, path=path).observe(duration)
            IN_PROGRESS.dec()


def setup_metrics_router() -> APIRouter:
    router = APIRouter()

    @router.get("/metrics")
    async def metrics() -> Response:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return router
