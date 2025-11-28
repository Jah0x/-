import json
import logging

from app.core.tracing import get_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            message["request_id"] = request_id
        message["timestamp"] = self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z")
        if record.exc_info:
            message["exception"] = self.formatException(record.exc_info)
        return json.dumps(message)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    handler.addFilter(lambda record: setattr(record, "request_id", get_request_id()) or True)
    root.handlers = [handler]
