"""
Health Check Routes
"""

import httpx
from fastapi import APIRouter
from moorcheh_sdk import MoorchehClient

from mira.app import __version__
from mira.app.clients.backend import Backend, parse_backend
from mira.app.config import settings
from mira.app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    moorcheh_connected = False
    backend = parse_backend(settings.MIRA_BACKEND)

    if backend == Backend.ON_PREM:
        url = f"{settings.RIVERA_ONPREM_URL.rstrip('/')}/health"
        try:
            resp = httpx.get(url, timeout=3.0)
            moorcheh_connected = resp.status_code == 200
        except Exception:
            moorcheh_connected = False
    else:
        api_key = settings.RIVERA_API_KEY.strip()
        if api_key:
            try:
                from moorcheh_sdk.exceptions import (
                    AuthenticationError,
                    NamespaceNotFound,
                )

                client = MoorchehClient(api_key=api_key)
                try:
                    client.documents.get(
                        namespace_name="__mira_auth_ping__", ids=["1"]
                    )
                    moorcheh_connected = True
                except NamespaceNotFound:
                    moorcheh_connected = True
                except AuthenticationError:
                    moorcheh_connected = False
            except Exception:
                moorcheh_connected = False

    return HealthResponse(
        status="healthy" if moorcheh_connected else "unhealthy",
        service="MIRA",
        version=__version__,
        moorcheh_connected=moorcheh_connected,
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}
