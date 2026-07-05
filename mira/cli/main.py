"""
MIRA CLI - Main Entry Point

Command-line interface for MIRA V2 API
"""

# Import the app instance from shared module
# Import commands package to trigger registration of all CLI commands
import mira.cli.commands  # noqa: F401
from mira.cli.commands._shared import app  # noqa: F401

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app()
