"""
MIRA CLI - Connect commands (agent integrations).
"""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from mira.cli.commands._shared import (
    AGENT_REGISTRY,
    BOLD_PRIMARY,
    BRIGHT,
    PRIMARY,
    SUCCESS,
    _error,
    connect_app,
    console,
    detect_agents_in_project,
    detect_mira_installed,
    detect_mira_installed_global,
    install_agent,
    list_agents,
    remove_agent,
)


def _print_install_result(result: dict, scope_label: str) -> None:
    """Pretty-print the result of an install_agent call."""
    steps = result["steps"]
    errors = result["errors"]

    if errors:
        for err in errors:
            console.print(f"  [red]✗[/red] {err}")
    if steps:
        for step in steps:
            console.print(f"  [green]✓[/green] {step}")
    if not errors and not steps:
        console.print("  [dim]Nothing to do[/dim]")


def _run_connect_for_agent(agent_name: str, project_dir: str, is_global: bool) -> None:
    """Run connect for a single agent with full UI output."""
    agent = AGENT_REGISTRY.get(agent_name)
    if not agent:
        _error(
            f"Unknown agent: {agent_name}",
            hint="Run 'mira connect list' to see available agents.",
        )

    if is_global:
        scope_label = f"Global (~/{agent.config_global_dir or ''})"
    else:
        scope_label = str(Path(project_dir).resolve())

    console.print(
        Panel.fit(
            f"[{BOLD_PRIMARY}]Connect to {agent.display_name}[/{BOLD_PRIMARY}]\n"
            f"{'Scope' if is_global else 'Project'}: [bold]{scope_label}[/bold]",
            border_style=PRIMARY,
        )
    )

    result = install_agent(agent_name, project_dir, is_global)
    _print_install_result(result, scope_label)

    # Summary
    scope_info = "globally (all projects)" if is_global else f"in {scope_label}"
    steps = result["steps"]
    errors = result["errors"]

    if not errors:
        console.print()
        # Build summary lines
        summary_parts = [
            f"[bold green]{agent.display_name} integration complete![/bold green]\n"
        ]
        summary_parts.append(f"[dim]Scope:[/dim] {scope_info}")
        for step in steps:
            summary_parts.append(f"[dim]•[/dim] {step}")

        if not agent.supports_hooks:
            summary_parts.append(
                "\n[dim]Tip: Run 'mira memory sync --project-dir .' before\n"
                "starting a session to pre-populate MEMORY.md.[/dim]"
            )

        console.print(
            Panel(
                "\n".join(summary_parts), title="Setup Complete", border_style=SUCCESS
            )
        )
    else:
        console.print(f"\n[yellow]Completed with {len(errors)} error(s)[/yellow]")


# Individual agent connect commands


@connect_app.command("claude-code")
def connect_claude_code(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.claude/"
    ),
):
    """Connect MIRA to Claude Code.

    Examples:
        mira connect claude-code
        mira connect claude-code --project-dir ./my-project
        mira connect claude-code --global
    """
    _run_connect_for_agent("claude-code", project_dir, is_global)


@connect_app.command("codex")
def connect_codex(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.codex/"
    ),
):
    """Connect MIRA to OpenAI Codex CLI.

    Examples:
        mira connect codex
        mira connect codex --project-dir ./my-project
        mira connect codex --global
    """
    _run_connect_for_agent("codex", project_dir, is_global)


@connect_app.command("cursor")
def connect_cursor(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.cursor/"
    ),
):
    """Connect MIRA to Cursor IDE.

    Creates a .cursor/rules/mira.mdc rule file and deploys the skill.

    Examples:
        mira connect cursor
        mira connect cursor --global
    """
    _run_connect_for_agent("cursor", project_dir, is_global)


@connect_app.command("windsurf")
def connect_windsurf(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to Windsurf IDE.

    Appends MIRA instructions to .windsurfrules and deploys the skill.

    Examples:
        mira connect windsurf
        mira connect windsurf --global
    """
    _run_connect_for_agent("windsurf", project_dir, is_global)


@connect_app.command("antigravity")
def connect_antigravity(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to Google Antigravity.

    Deploys the mira-memory skill to .agent/skills/.

    Examples:
        mira connect antigravity
        mira connect antigravity --global
    """
    _run_connect_for_agent("antigravity", project_dir, is_global)


@connect_app.command("gemini-cli")
def connect_gemini_cli(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.gemini/"
    ),
):
    """Connect MIRA to Google Gemini CLI.

    Adds MIRA instructions to GEMINI.md and deploys the skill.

    Examples:
        mira connect gemini-cli
        mira connect gemini-cli --global
    """
    _run_connect_for_agent("gemini-cli", project_dir, is_global)


@connect_app.command("cline")
def connect_cline(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to Cline VS Code extension.

    Creates a .clinerules/mira.md instruction file and deploys the skill.

    Examples:
        mira connect cline
        mira connect cline --global
    """
    _run_connect_for_agent("cline", project_dir, is_global)


@connect_app.command("continue")
def connect_continue(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.continue/"
    ),
):
    """Connect MIRA to Continue.dev.

    Creates a .continue/rules/mira.md instruction file and deploys the skill.

    Examples:
        mira connect continue
        mira connect continue --global
    """
    _run_connect_for_agent("continue", project_dir, is_global)


@connect_app.command("opencode")
def connect_opencode(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to OpenCode CLI.

    Adds MIRA instructions to AGENTS.md and deploys the skill.

    Examples:
        mira connect opencode
        mira connect opencode --global
    """
    _run_connect_for_agent("opencode", project_dir, is_global)


@connect_app.command("goose")
def connect_goose(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to Goose AI agent.

    Deploys the mira-memory skill to .goose/skills/.

    Examples:
        mira connect goose
        mira connect goose --global
    """
    _run_connect_for_agent("goose", project_dir, is_global)


@connect_app.command("roo")
def connect_roo(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.roo/"
    ),
):
    """Connect MIRA to Roo Code.

    Creates a .roo/rules/mira.md instruction file and deploys the skill.

    Examples:
        mira connect roo
        mira connect roo --global
    """
    _run_connect_for_agent("roo", project_dir, is_global)


@connect_app.command("github-copilot")
def connect_github_copilot(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Connect MIRA to GitHub Copilot.

    Adds MIRA instructions to .github/copilot-instructions.md and deploys the skill.

    Examples:
        mira connect github-copilot
        mira connect github-copilot --global
    """
    _run_connect_for_agent("github-copilot", project_dir, is_global)


@connect_app.command("augment")
def connect_augment(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.augment/"
    ),
):
    """Connect MIRA to Augment Code.

    Creates an .augment/rules/mira.md instruction file and deploys the skill.

    Examples:
        mira connect augment
        mira connect augment --global
    """
    _run_connect_for_agent("augment", project_dir, is_global)


# Connect List


@connect_app.command("list")
def connect_list(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Project directory to check"
    ),
):
    """List all supported agents and their MIRA installation status.

    Shows which agents are available, detected in the project, and which
    have MIRA installed (locally and globally).

    Examples:
        mira connect list
        mira connect list --project-dir ./my-project
    """
    project_path = Path(project_dir).resolve()

    console.print(
        Panel.fit(
            f"[{BOLD_PRIMARY}]MIRA Agent Integrations[/{BOLD_PRIMARY}]\n"
            f"Project: [bold]{project_path}[/bold]",
            border_style=PRIMARY,
        )
    )
    console.print()

    detected = {a.name for a in detect_agents_in_project(project_path)}
    installed_local = {a.name for a in detect_mira_installed(project_path)}
    installed_global = {a.name for a in detect_mira_installed_global()}

    table = Table(show_header=True, header_style=BOLD_PRIMARY)
    table.add_column("Agent Name", style=PRIMARY)
    table.add_column("Detected", justify="center", width=10)
    table.add_column("Local", justify="center", width=10)
    table.add_column("Global", justify="center", width=10)
    table.add_column("Instruction File", style="dim")

    for agent in list_agents():
        is_detected = agent.name in detected
        is_local = agent.name in installed_local
        is_global = agent.name in installed_global

        det_icon = "[green]●[/green]" if is_detected else "[dim]○[/dim]"
        local_icon = "[green]●[/green]" if is_local else "[dim]○[/dim]"
        global_icon = "[green]●[/green]" if is_global else "[dim]○[/dim]"

        table.add_row(
            agent.name,
            det_icon,
            local_icon,
            global_icon,
            agent.instruction_file or "[dim]skills only[/dim]",
        )

    console.print(table)
    console.print()

    total_local = len(installed_local)
    total_global = len(installed_global)
    console.print(
        f"[dim]Local installs: {total_local} | Global installs: {total_global}[/dim]"
    )
    console.print("[dim]Connect an agent: mira connect <agent-name>[/dim]")
    console.print("[dim]Interactive mode: mira connect multi[/dim]")


# Connect Remove


@connect_app.command("remove")
def connect_remove(
    agent_name: str | None = typer.Argument(
        None, help="Agent to disconnect (e.g. claude-code, cursor)"
    ),
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Project directory"
    ),
    is_global: bool = typer.Option(
        False, "--global", "-g", help="Remove from global scope"
    ),
    all_agents: bool = typer.Option(
        False, "--all", help="Remove MIRA from all agents"
    ),
):
    """Remove MIRA integration from an agent.

    Examples:
        mira connect remove claude-code
        mira connect remove cursor --global
        mira connect remove --all
    """
    if all_agents:
        "globally" if is_global else f"in {Path(project_dir).resolve()}"
        agents_to_remove = [a.name for a in list_agents()]
    elif agent_name:
        if agent_name not in AGENT_REGISTRY:
            _error(
                f"Unknown agent: {agent_name}",
                hint="Run 'mira connect list' for available agents.",
            )
        agents_to_remove = [agent_name]
    else:
        _error(
            "Specify an agent name or use --all.",
            hint="Run 'mira connect remove <agent>' or 'mira connect remove --all'.",
        )

    removed_count = 0
    for name in agents_to_remove:
        result = remove_agent(name, project_dir, is_global)
        steps = result["steps"]
        errors = result["errors"]
        if steps:
            display_name = AGENT_REGISTRY[name].display_name
            console.print(f"[green]✓[/green] {display_name}")
            for step in steps:
                console.print(f"  [dim]{step}[/dim]")
            removed_count += 1
        for err in errors:
            console.print(f"[red]✗[/red] {err}")

    if removed_count == 0:
        console.print("[dim]No MIRA installations found to remove.[/dim]")
    else:
        console.print(f"\n[green]Removed MIRA from {removed_count} agent(s)[/green]")


# Interactive Connect Setup


@connect_app.command("multi")
def connect_multi(
    project_dir: str = typer.Option(
        ".", "--project-dir", "-p", help="Target project directory"
    ),
    is_global: bool = typer.Option(False, "--global", "-g", help="Install globally"),
):
    """Interactive setup — select multiple agents to connect.

    Auto-detects which agents are present in your project and lets you
    choose which ones to connect MIRA to.

    Examples:
        mira connect setup
        mira connect setup --global
        mira connect setup --project-dir ./my-project
    """
    project_path = Path(project_dir).resolve()

    console.print(
        Panel.fit(
            f"[{BOLD_PRIMARY}]MIRA Connect — Interactive Setup[/{BOLD_PRIMARY}]\n"
            f"{'Scope: Global' if is_global else f'Project: {project_path}'}",
            border_style=PRIMARY,
        )
    )
    console.print()

    all_agents = list_agents()
    detected = {a.name for a in detect_agents_in_project(project_path)}

    if is_global:
        installed = {a.name for a in detect_mira_installed_global()}
    else:
        installed = {a.name for a in detect_mira_installed(project_path)}

    # Show menu
    console.print(f"[{BOLD_PRIMARY}]Available Agents:[/{BOLD_PRIMARY}]")
    console.print()

    for i, agent in enumerate(all_agents, 1):
        status_parts = []
        if agent.name in detected:
            status_parts.append("[green]detected[/green]")
        if agent.name in installed:
            status_parts.append("[cyan]installed[/cyan]")
        status = f" ({', '.join(status_parts)})" if status_parts else ""
        console.print(
            f"  [{BRIGHT}]{i:2d}[/{BRIGHT}]. {agent.display_name:<22s}{status}"
        )

    console.print()
    console.print("[dim]Enter agent numbers separated by commas (e.g. 1,3,5)[/dim]")
    console.print(
        "[dim]Or type 'all' to install all, 'detected' for detected only[/dim]"
    )
    console.print()

    choice = typer.prompt("Select agents").strip().lower()

    if choice == "all":
        selected = [a.name for a in all_agents]
    elif choice == "detected":
        selected = list(detected)
        if not selected:
            console.print("[yellow]No agents detected in this project.[/yellow]")
            raise typer.Exit(0)
    elif choice == "q" or choice == "quit":
        raise typer.Exit(0)
    else:
        # Parse comma-separated numbers
        selected = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(all_agents):
                    selected.append(all_agents[idx].name)
                else:
                    console.print(f"[yellow]Skipping invalid number: {part}[/yellow]")
            elif part in AGENT_REGISTRY:
                selected.append(part)
            else:
                console.print(f"[yellow]Skipping unknown: {part}[/yellow]")

    if not selected:
        console.print("[yellow]No agents selected.[/yellow]")
        raise typer.Exit(0)

    console.print()
    console.print(
        f"[{BOLD_PRIMARY}]Installing to {len(selected)} agent(s)...[/{BOLD_PRIMARY}]"
    )
    console.print()

    success_count = 0
    error_count = 0

    for name in selected:
        agent = AGENT_REGISTRY[name]
        result = install_agent(name, project_dir, is_global)
        steps = result["steps"]
        errors = result["errors"]

        if errors:
            console.print(f"  [red]✗[/red] {agent.display_name}")
            for err in errors:
                console.print(f"    [red]{err}[/red]")
            error_count += 1
        else:
            step_summary = ", ".join(steps) if steps else "no changes needed"
            console.print(f"  [green]✓[/green] {agent.display_name} — {step_summary}")
            success_count += 1

    console.print()
    scope_label = "globally" if is_global else f"in {project_path}"
    console.print(
        Panel(
            f"[bold green]Connected {success_count} agent(s) {scope_label}![/bold green]"
            + (f"\n[yellow]{error_count} error(s)[/yellow]" if error_count else "")
            + "\n\n[dim]Run 'mira connect list' to see all installations[/dim]"
            + "\n[dim]Run 'mira memory sync --project-dir .' to populate MEMORY.md[/dim]",
            title="Done",
            border_style=SUCCESS,
        )
    )
