"""
Backend selection and protocol for Mira's Rivera client.

Mira can talk to two backends:
- ``cloud``   - Rivera Cloud via the ``moorcheh_sdk`` package (API key).
- ``on-prem`` - A local ``moorcheh`` server (Docker) via the ``moorcheh-client``
  package. No Rivera API key needed.

Both clients expose the same ``namespaces / documents / similarity_search /
answer / files / vectors`` shape, so service code never branches on backend.
"""

import json
from enum import Enum
from pathlib import Path


class Backend(str, Enum):
    CLOUD = "cloud"
    ON_PREM = "on-prem"


def parse_backend(value: str | None) -> Backend:
    """Coerce a string (env / yaml) into a Backend, defaulting to cloud."""
    if not value:
        return Backend.CLOUD
    try:
        return Backend(value.strip().lower())
    except ValueError:
        return Backend.CLOUD


def get_active_llm_model(cloud_default: str) -> str | None:
    """Active LLM model identifier for ``answer.generate`` / summary.

    Cloud: returns ``cloud_default`` (i.e. ``settings.ANSWER_MODEL`` or
    ``settings.SUMMARY_MODEL`` — caller picks the right one).

    On-prem: returns ``llm_model`` from ``~/.mira/on-prem/state.json`` (set
    during onboarding). Returns ``None`` when state is missing/empty so the
    caller can omit ``ai_model`` and let the on-prem server fall back to its
    ``~/.moorcheh/config.json`` LLM. No coercion magic happens elsewhere in
    the stack — what this returns is what gets sent.
    """
    # Local import to avoid circular dependency with ``app.config``.
    from mira.app.config import settings

    if parse_backend(settings.MIRA_BACKEND) == Backend.CLOUD:
        return cloud_default

    state_path = Path.home() / ".mira" / "on-prem" / "state.json"
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text())
    except Exception:
        return None
    return state.get("llm_model") or None
