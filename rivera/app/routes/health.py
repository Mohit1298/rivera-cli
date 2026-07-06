"""
Health Check Routes
"""

import httpx
from fastapi import APIRouter
from moorcheh_sdk import MoorchehClient

from rivera.app import __version__
from rivera.app.clients.backend import Backend, parse_backend
from rivera.app.config import settings
from rivera.app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    rivera_connected = False
    backend = parse_backend(settings.RIVERA_BACKEND)

    if backend == Backend.ON_PREM:
        url = f"{settings.RIVERA_ONPREM_URL.rstrip('/')}/health"
        try:
            resp = httpx.get(url, timeout=3.0)
            rivera_connected = resp.status_code == 200
        except Exception:
            rivera_connected = False
    else:
        api_key = settings.RIVERA_API_KEY.strip()
        if api_key:
            try:
                from moorcheh_sdk.exceptions import (
                    AuthenticationError,
                    NamespaceNotFound,
                )

                client = MoorchehClient(api_key=api_key, base_url=settings.RIVERA_BASE_URL)
                try:
                    client.documents.get(
                        namespace_name="__rivera_auth_ping__", ids=["1"]
                    )
                    rivera_connected = True
                except NamespaceNotFound:
                    rivera_connected = True
                except AuthenticationError:
                    rivera_connected = False
            except Exception:
                rivera_connected = False

    return HealthResponse(
        status="healthy" if rivera_connected else "unhealthy",
        service="RIVERA",
        version=__version__,
        rivera_connected=rivera_connected,
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}
