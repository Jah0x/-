import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            message["exception"] = self.formatException(record.exc_info)
        return json.dumps(message)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
