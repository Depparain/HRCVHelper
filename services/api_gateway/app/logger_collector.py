from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import List
from .schemas import LogEntry

_LOG_BUFFER: deque[LogEntry] = deque(maxlen=500)


class InMemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                level=record.levelname,
                service=record.name,
                message=self.format(record),
            )
            _LOG_BUFFER.appendleft(entry)
        except Exception:
            self.handleError(record)


def setup_in_memory_logging():
    handler = InMemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)


def get_system_logs(limit: int = 100) -> List[LogEntry]:
    return list(_LOG_BUFFER)[:limit]


def log_event(service: str, level: str, message: str):
    entry = LogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        level=level.upper(),
        service=service,
        message=message,
    )
    _LOG_BUFFER.appendleft(entry)
