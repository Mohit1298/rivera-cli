"""
RIVERA CLI - Main Entry Point

Command-line interface for RIVERA V2 API
"""

# Import the app instance from shared module
# Import commands package to trigger registration of all CLI commands
import rivera.cli.commands  # noqa: F401
from rivera.cli.commands._shared import app  # noqa: F401

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app()
