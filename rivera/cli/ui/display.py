"""
RIVERA CLI - Welcome Banner Display

Beautiful startup display with Rivera blue-violet branding,
memory type taxonomy, and quick-start commands.
"""

import platform
import time

from rich.console import Console
from rich.live import Live
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from rivera.app.clients.backend import Backend
from rivera.cli.config.manager import ConfigManager
from rivera.cli.ui.theme import (
    BOLD_BRIGHT,
    BOLD_PRIMARY,
    PRIMARY,
)

RIVERA_VERSION = "0.1.3"

# ASCII art logo — RIVERA block letters with flowing waves
LOGO = r"""
          ██████╗  ██╗ ██╗   ██╗ ███████╗ ██████╗   █████╗ 
 ≈≈ ≈≈    ██╔══██╗ ██║ ██║   ██║ ██╔════╝ ██╔══██╗ ██╔══██╗
  ≈≈ ≈≈   ██████╔╝ ██║ ██║   ██║ █████╗   ██████╔╝ ███████║
 ≈≈ ≈≈    ██╔══██╗ ██║ ╚██╗ ██╔╝ ██╔══╝   ██╔══██╗ ██╔══██║
  ≈≈ ≈≈   ██║  ██║ ██║  ╚████╔╝  ███████╗ ██║  ██║ ██║  ██║
          ╚═╝  ╚═╝ ╚═╝   ╚═══╝   ╚══════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝
                            remember · recall · answer
""".strip("\n")

# Animation frames — waves drift back and forth
WAVE_A = " ≈≈ ≈≈  "
WAVE_B = "  ≈≈ ≈≈ "

# All 13 RIVERA memory types
MEMORY_TYPES = [
    "fact",
    "preference",
    "goal",
    "decision",
    "artifact",
    "learning",
    "event",
    "instruction",
    "context",
    "observation",
    "commitment",
    "relationship",
    "error",
]


def print_logo() -> None:
    """Print the RIVERA ASCII logo and tagline."""
    console = Console()
    console.print()

    # ── Logo ────────────────────────────────────────────────────────
    lines = LOGO.split("\n")

    with Live(console=console, refresh_per_second=10, transient=False) as live:
        # Quick 1-second animation: waves flow left/right
        for i in range(20):
            anim_lines = list(lines)
            if i % 2 == 0:
                anim_lines = [
                    ln.replace(WAVE_A, "\x00").replace(WAVE_B, WAVE_A).replace("\x00", WAVE_B)
                    for ln in anim_lines
                ]
            logo_text = Text("\n".join(anim_lines), style=BOLD_PRIMARY)
            live.update(logo_text)
            time.sleep(0.1)

    # Tagline
    console.print()
    tagline = Text()
    tagline.append("  Memory your AI agents never lose.\n", style="bold white")
    tagline.append("  ", style="dim")
    tagline.append("api.wirtel.ca", style=BOLD_PRIMARY)
    console.print(tagline)
    console.print()


def show_welcome_banner(config_manager: ConfigManager) -> None:
    """Render the full RIVERA welcome banner to the console."""
    console = Console()

    # ── System ──────────────────────────────────────────────────────
    console.print(Rule("System", style=PRIMARY))
    py_ver = platform.python_version()
    os_name = platform.system()
    sys_line = Text()
    sys_line.append(f"  v{RIVERA_VERSION}", style=BOLD_BRIGHT)
    sys_line.append("  ·  ", style="dim")
    sys_line.append(f"Python {py_ver}", style="white")
    sys_line.append("  ·  ", style="dim")
    sys_line.append(os_name, style="white")
    console.print(sys_line)
    console.print()

    # ── Status ──────────────────────────────────────────────────────
    console.print(Rule("Status", style=PRIMARY))

    has_key = config_manager.is_configured()
    config_manager.get_api_key()
    backend = config_manager.get_backend()

    status_table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
    status_table.add_column("Label", style="dim", min_width=14)
    status_table.add_column("Value")

    # Backend
    status_table.add_row("  Backend", backend.value)
    if backend == Backend.ON_PREM:
        op = config_manager.get_onprem_config()
        status_table.add_row("  On-Prem URL", op.get("url", ""))
        status_table.add_row(
            "  Embedding", op.get("embedding_provider") or "[dim]—[/dim]"
        )
    elif has_key:
        status_table.add_row("  API Key", "[green]●[/green] configured")
    else:
        status_table.add_row("  API Key", "[red]●[/red] not configured")

    # Active Agent
    active_agent, _ = config_manager.get_active_session()
    if active_agent:
        status_table.add_row("  Agent", f"[green]●[/green] {active_agent} (active)")
    else:
        status_table.add_row("  Agent", "[dim]○[/dim] none")

    console.print(status_table)
    console.print()

    # ── Memory Types ────────────────────────────────────────────────
    console.print(Rule("Memory Types", style=PRIMARY))

    # Build 4-column rows of memory types
    cols = 4
    rows_text = []
    for i in range(0, len(MEMORY_TYPES), cols):
        chunk = MEMORY_TYPES[i : i + cols]
        row = Text("  ")
        for _j, mt in enumerate(chunk):
            row.append("◆ ", style=BOLD_PRIMARY)
            row.append(f"{mt:<14}", style="white")
        rows_text.append(row)

    for row in rows_text:
        console.print(row)
    console.print()

    # ── Quick Start ─────────────────────────────────────────────────
    console.print(Rule("Quick Start", style=PRIMARY))

    commands = [
        ("rivera agent create <agent_name_or_id>", "Create a new rivera agent"),
        ('rivera remember "..."', "Store a memory"),
        ('rivera recall "..."', "Search memories"),
        ('rivera answer "..."', "Ask a question (RAG)"),
        ("rivera connect list", "See agent integrations"),
        ("rivera connect <agent>", "Connect to an AI agent"),
        ("rivera ui", "Open the web dashboard UI"),
        ("rivera status", "Full dashboard"),
        ("rivera serve", "Start local REST API server"),
    ]

    cmd_table = Table(show_header=False, box=None, padding=(0, 1), show_edge=False)
    cmd_table.add_column("Cmd", style=BOLD_BRIGHT, min_width=28)
    cmd_table.add_column("Desc", style="dim")

    for cmd, desc in commands:
        cmd_table.add_row(f"  {cmd}", desc)

    console.print(cmd_table)
    console.print()

    # Note about server
    console.print("  [dim]Server is only needed for REST API endpoints.[/dim]")
    console.print(
        "  [dim]All CLI commands work directly without a running server.[/dim]"
    )
    console.print()

    # Footer
    console.print(
        f"  Run [{BOLD_PRIMARY}]rivera --help[/{BOLD_PRIMARY}] for all commands\n",
        style="dim",
    )
