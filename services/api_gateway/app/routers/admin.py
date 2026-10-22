from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
import httpx
from fastapi import APIRouter, Depends

from ..config import settings
from ..dependencies import require_admin_user
from ..logger_collector import get_system_logs
from ..schemas import AdminLogsResponse, HealthReportResponse, LogEntry, ServiceHealthStatus

logger = logging.getLogger("api_gateway.routers.admin")
router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/logs", response_model=AdminLogsResponse)
async def get_logs(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(require_admin_user),
):
    """
    ФТ-АДМ.1: Агрегация системных логов со всех микросервисов системы (TASK-3.4).
    """
    all_logs = list(get_system_logs(limit=limit))

    targets = [
        ("auth_system", f"{settings.auth_system_url}/internal/logs"),
        ("md_convertor", f"{settings.md_convertor_url}/internal/logs"),
        ("llm_convertor", f"{settings.llm_convertor_url}/internal/logs"),
        ("json_to_word", f"{settings.json_to_word_url}/internal/logs"),
        ("db_connector", f"{settings.db_connector_url}/internal/logs"),
    ]

    async with httpx.AsyncClient(timeout=2.0) as client:
        for s_name, url in targets:
            try:
                resp = await client.get(url, params={"limit": limit})
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("logs", []):
                        all_logs.append(LogEntry(**item))
            except Exception as e:
                logger.debug("Не удалось получить логи от %s: %s", s_name, e)

    all_logs.sort(key=lambda x: x.timestamp, reverse=True)
    selected = all_logs[:limit]
    return AdminLogsResponse(total=len(selected), logs=selected)


@router.get("/health", response_model=HealthReportResponse)
async def get_health_report(
    current_user: Dict[str, Any] = Depends(require_admin_user),
):
    """
    ФТ-АДМ.2: Сводный отчет о состоянии всех микросервисов и хранилищ системы (health report).
    """
    services_status: Dict[str, ServiceHealthStatus] = {}
    overall_ok = True

    targets = [
        ("auth_system", f"{settings.auth_system_url}/health"),
        ("md_convertor", f"{settings.md_convertor_url}/health"),
        ("llm_convertor", f"{settings.llm_convertor_url}/health"),
        ("json_to_word", f"{settings.json_to_word_url}/health"),
        ("db_connector", f"{settings.db_connector_url}/health"),
    ]

    async with httpx.AsyncClient(timeout=3.0) as client:
        for s_name, url in targets:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    services_status[s_name] = ServiceHealthStatus(
                        service=s_name,
                        status="healthy",
                        details=r.json(),
                    )
                else:
                    overall_ok = False
                    services_status[s_name] = ServiceHealthStatus(
                        service=s_name,
                        status="degraded",
                        details={"status_code": r.status_code, "text": r.text},
                    )
            except Exception as e:
                overall_ok = False
                services_status[s_name] = ServiceHealthStatus(
                    service=s_name,
                    status="unreachable",
                    details={"error": str(e)},
                )

    services_status["api_gateway"] = ServiceHealthStatus(
        service="api_gateway",
        status="healthy",
        details={"version": "1.0.0"},
    )

    return HealthReportResponse(
        status="healthy" if overall_ok else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services_status,
    )
