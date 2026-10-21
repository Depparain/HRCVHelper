from __future__ import annotations

import pytest
from services.api_gateway.app.logger_collector import log_event, get_system_logs
from services.api_gateway.app.schemas import AdminLogsResponse


def test_logger_collector():
    log_event("test_service", "INFO", "Тестовое событие")
    log_event("test_service", "ERROR", "Тестовая ошибка")

    logs = get_system_logs(limit=10)
    assert len(logs) >= 2
    messages = [l.message for l in logs]
    assert any("Тестовая ошибка" in m for m in messages)
    assert any("Тестовое событие" in m for m in messages)
