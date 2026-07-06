"""
RIVERA FastAPI Application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from moorcheh_sdk import MoorchehClient
from moorcheh_sdk.exceptions import AuthenticationError, NamespaceNotFound

from rivera.app import __version__
from rivera.app.clients.backend import Backend, parse_backend
from rivera.app.config import settings
from rivera.app.routes import health, sessions
from rivera.app.ui.routes.ui_router import mount_ui_static
from rivera.app.ui.routes.ui_router import router as ui_router


def _validate_startup_dependencies() -> None:
    """Fail fast when mandatory external dependencies are misconfigured."""
    backend = parse_backend(settings.RIVERA_BACKEND)

    if backend == Backend.ON_PREM:
        import httpx

        url = f"{settings.RIVERA_ONPREM_URL.rstrip('/')}/health"
        try:
            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"Rivera on-prem server not reachable at {url}. "
                f"Start it with: moorcheh up"
            ) from exc
        return

    api_key = settings.RIVERA_API_KEY.strip()
    if not api_key:
        raise RuntimeError(
            "RIVERA_API_KEY is not configured. Set it before starting RIVERA."
        )

    try:
        client = MoorchehClient(api_key=api_key, base_url=settings.RIVERA_BASE_URL)
        try:
            client.documents.get(namespace_name="__rivera_auth_ping__", ids=["1"])
        except NamespaceNotFound:
            # Auth succeeded; ping namespace intentionally does not exist.
            pass
    except AuthenticationError as exc:
        raise RuntimeError(
            "RIVERA_API_KEY is invalid. Update it and restart RIVERA."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to validate Rivera connectivity: {exc}") from exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_startup_dependencies()
    yield


# Create FastAPI app
app = FastAPI(
    title="Rivera - Memory your AI agents never lose.",
    description="A memory layer service for agentic AI systems using Rivera SDK",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])

# Session-Based API (Primary)
app.include_router(sessions.router, prefix="/api/v2", tags=["Sessions & Agents"])


# Web UI Dashboard
app.include_router(ui_router, tags=["Web UI"])
mount_ui_static(app)


@app.get("/")
async def root():
    return {
        "service": "RIVERA",
        "description": "A companion memory agent that lets your agents focus and improve while you keep ownership of everything they learn.",
        "version": __version__,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
