"""
Rivera Client Singleton (backend-aware dispatcher).

Returns either a Rivera Cloud client (``moorcheh_sdk.MoorchehClient``) or an
on-prem client (``rivera.app.clients.onprem.OnPremClient``), based on
``settings.RIVERA_BACKEND``.

Service code keeps calling ``get_moorcheh_client()`` and uses the same
``client.namespaces.* / client.documents.* / client.answer.*`` shape - both
backends expose it.
"""

from typing import Any

from moorcheh_sdk import AsyncMoorchehClient, MoorchehClient

from rivera.app.clients.backend import Backend, parse_backend
from rivera.app.config import settings

# Re-export the cloud class name for callers that still import it directly.
# New code should use get_moorcheh_client() so the on-prem backend is honored.
__all__ = [
    "MoorchehClient",
    "AsyncMoorchehClient",
    "MoorchehClientSingleton",
    "moorcheh_client",
    "get_moorcheh_client",
    "get_async_moorcheh_client",
]


class MoorchehClientSingleton:
    """Singleton pattern for the active Rivera client (cloud or on-prem)."""

    _instance = None
    _client: Any = None
    _async_client: Any = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _backend(self) -> Backend:
        return parse_backend(settings.RIVERA_BACKEND)

    def get_client(self, api_key: str | None = None) -> Any:
        """Get or create the active Rivera client.

        ``api_key`` is honored only on the cloud backend; ignored on on-prem.
        """
        if self._backend() == Backend.ON_PREM:
            # Self-hosted Rivera speaks the exact cloud wire protocol — same
            # client, different base_url (+ the key minted on first boot).
            if self._client is None:
                self._client = MoorchehClient(
                    api_key=api_key or settings.RIVERA_API_KEY,
                    base_url=settings.RIVERA_ONPREM_URL,
                )
            return self._client

        # Cloud path
        key_to_use = api_key or settings.RIVERA_API_KEY
        if key_to_use == settings.RIVERA_API_KEY:
            if self._client is None:
                self._client = MoorchehClient(api_key=settings.RIVERA_API_KEY, base_url=settings.RIVERA_BASE_URL)
            return self._client
        return MoorchehClient(api_key=key_to_use, base_url=settings.RIVERA_BASE_URL)

    def get_async_client(self, api_key: str | None = None) -> Any:
        """Get or create the active async Rivera client."""
        if self._backend() == Backend.ON_PREM:
            if self._async_client is None:
                self._async_client = AsyncMoorchehClient(
                    api_key=api_key or settings.RIVERA_API_KEY,
                    base_url=settings.RIVERA_ONPREM_URL,
                )
            return self._async_client

        key_to_use = api_key or settings.RIVERA_API_KEY
        if key_to_use == settings.RIVERA_API_KEY:
            if self._async_client is None:
                self._async_client = AsyncMoorchehClient(
                    api_key=settings.RIVERA_API_KEY,
                    base_url=settings.RIVERA_BASE_URL,
                )
            return self._async_client
        return AsyncMoorchehClient(api_key=key_to_use, base_url=settings.RIVERA_BASE_URL)

    def reset_client(self):
        """Reset cached clients (call after backend switch or in tests)."""
        self._client = None
        self._async_client = None


# Global client instance
moorcheh_client = MoorchehClientSingleton()


def get_moorcheh_client() -> Any:
    """Dependency injection function (cloud or on-prem)."""
    return moorcheh_client.get_client()


def get_async_moorcheh_client() -> Any:
    """Dependency injection function for async client (cloud or on-prem)."""
    return moorcheh_client.get_async_client()
