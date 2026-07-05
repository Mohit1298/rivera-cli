# MIRA CLI Installation & Usage Guide

**Status**: Production Ready
**Last Updated**: March 2025

---

## Table of Contents

1. [Installation](#installation)
2. [First-Time Setup](#first-time-setup)
3. [Server Management](#server-management)
4. [Basic Usage](#basic-usage)
5. [Architecture](#architecture)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Option 1: Install from PyPI (Future - After Publishing)

```bash
pip install mira
```

### Option 2: Install from Source (Current)

```bash
# Clone the repository
git clone https://github.com/your-org/mira.git
cd mira

# Install in development mode
pip install -e .

# Verify installation
mira --help
```

**What gets installed:**
- `mira` command-line tool
- MIRA API server (`app/` package)
- CLI interface (`cli/` package)
- All dependencies (typer, rich, httpx, cryptography, fastapi, moorcheh-sdk, etc.)

---

## First-Time Setup

### Quick Start (Recommended - 2 Steps!)

#### Step 1: Get Moorcheh API Key

1. Go to [Moorcheh Dashboard](https://moorcheh.ai)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

#### Step 2: Initialize & Setup

```bash
# Initialize MIRA (Sets up your API key)
mira
```

**That's it!** You are ready to use the CLI. No local server is required for CLI commands.

### Optional: Start the REST API Server

If you want to use the MIRA REST API from other applications or via `curl`:

```bash
# Start the local FastAPI server
mira serve
```

### Alternative: Manual Server Management

If you prefer to manage the server separately:

```bash
# Terminal 1: Start the server manually
python -m app.main

# Terminal 2: Initialize CLI
mira

# Terminal 2: Use CLI commands
mira agent create my-agent
```

**Output:**
```
+----------------------------------------+
| MIRA CLI Initialization               |
| Setting up your MIRA configuration... |
+----------------------------------------+

Enter your Moorcheh API key: ********

Testing connection to MIRA server...
OK Connection successful!
Server version: 1.0.0

Configuration saved to: ~/.mira/config.yaml

Next steps:
  1. Create and activate an agent: mira agent create my-agent
  2. Start storing memories: mira remember "Hello"

Optional:
  mira serve (starts local REST API server)
```

**What happens:**
- API key is encrypted with Fernet and saved to `~/.mira/config.yaml`
- Connection to server is tested
- CLI is ready to use!

---

## REST API Management

### Recommended: Embedded API Mode (`mira serve`)

**Basic CLI Usage (No server required):**
```bash
mira agent create my-agent
mira remember "First memory"
```

**Using the REST API (requires `mira serve`):**
If you need to access MIRA via HTTP (e.g., from a web app), start the server:

```bash
# Terminal 1
mira serve

# Terminal 2 (or from your app)
curl -X POST "http://localhost:8000/api/v2/agents/my-agent/recall" \
  -H "X-Session-Token: YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"memory","limit":5}'
```

**Pros:**
- ✅ Single command to start the API and CLI together
- ✅ Beautiful terminal UI
- ✅ Built-in port conflict detection
- ✅ Clean shutdown with CTRL+C

**Options:**
```bash
mira serve --port 8080        # Use different port
mira serve --reload           # Auto-reload for development
mira serve --host 127.0.0.1   # Localhost only
```

### Alternative: Manual Server Management

If you prefer to manage the server separately:

**Terminal 1 - Server:**
```bash
python -m app.main
```

**Terminal 2 - CLI:**
```bash
mira agent create my-agent
mira remember "First memory"
```

**Use when:**
- You want direct control over uvicorn parameters
- You're debugging server issues
- You're running in production with supervisord/systemd

---

## Basic Usage

### Complete Workflow Example

```bash
# 1. Create and activate an agent (one-time)
mira agent create my-assistant --pattern tool --description "My AI assistant"

# Output:
# OK Agent 'my-assistant' created successfully!
# Pattern: tool
# Description: My AI assistant
# OK Session started automatically for this agent.
# Session expires: 2025-12-28T16:30:00

# 2. (Optional) Reactivate or change duration
mira agent activate my-assistant --duration-hours 8

# Output:
# OK Agent 'my-assistant' activated!
# Session duration: 6 hours
# Session expires: 2025-12-28T18:30:00

# 3. Store memories
mira remember "User prefers dark mode" --type preference --tags "ui,settings"
mira remember "Implemented login feature" --type decision --tags "auth,feature"

# Output for each:
# OK Memory stored successfully!
# Memory ID: abc-123-def-456
# Type: preference | Confidence: 0.8

# 4. Search memories
mira recall "dark mode" --limit 5

# Output:
# Found 1 memories:
#
# +--------------------------------- Memory 1 ----------------------------------+
# | User prefers dark mode                                                      |
# |                                                                             |
# | User prefers dark mode                                                      |
# |                                                                             |
# | Type: preference | Confidence: 0.80 | Score: 0.923                          |
# +-----------------------------------------------------------------------------+

# 5. Ask questions (RAG)
mira answer "What UI preferences does the user have?"

# Output:
# +------------------------------- RAG Response --------------------------------+
# | Question: What UI preferences does the user have?                           |
# |                                                                             |
# | Answer:                                                                     |
# | Based on stored memories:                                                   |
# | - User prefers dark mode                                                    |
# +-----------------------------------------------------------------------------+

# 6. Check session status
mira session info

# Output:
# Active Session
# +-----------------------------------------+
# | Agent ID      | my-assistant            |
# | Session Token | eyJhbGciOiJIUzI1NiI...  |
# +-----------------------------------------+

# 7. When done
mira agent deactivate

# Output:
# OK Agent 'my-assistant' deactivated
```

### All Available Commands

```bash
# Setup
mira                                   # Setup CLI with API key

# Agent Management
mira agent create AGENT_ID             # Create and activate new agent
mira agent list                        # List all agents
mira agent activate AGENT_ID           # Activate (or reactivate) session
mira agent deactivate                  # End session
mira agent delete AGENT_ID            # Delete agent (prompts to keep/purge cloud memories)

# Memory Operations
mira remember "content"                # Store memory (fact)
mira remember "content" --type TYPE    # Store with type
mira remember "content" --tags "a,b"   # Store with tags
mira recall "query"                    # Search memories
mira answer "question"                    # RAG question answering

# Session Management
mira session info                      # Show session details

# Configuration
mira config show                       # Display config

# Help
mira --help                            # Show all commands
mira COMMAND --help                    # Show command help
```

---

## Architecture

### How It Works

```
┌─────────────────┐
│   User Types    │
│  mira          │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  CLI (cli/main.py)                  │
│  - Typer framework                  │
│  - Rich terminal UI                 │
│  - Config management                │
│  - API client wrapper               │
└────────┬────────────────────────────┘
         │ HTTP Requests
         │ (Authorization: Bearer API_KEY)
         │ (X-Session-Token: JWT)
         ▼
┌─────────────────────────────────────┐
│  MIRA Server (app/main.py)         │
│  - FastAPI application              │
│  - Session-based API                │
│  - JWT token management             │
│  - Agent & memory services          │
└────────┬────────────────────────────┘
         │ moorcheh-sdk
         │ (Semantic operations)
         ▼
┌─────────────────────────────────────┐
│  Moorcheh Cloud                     │
│  - No-indexing semantic database    │
│  - Instant write-to-search          │
│  - Namespace: mira_agent_{id}      │
└─────────────────────────────────────┘
```

### File Structure

```
mira/
├── pyproject.toml          # Package definition, entry point
├── app/                    # MIRA Server
│   ├── main.py            # FastAPI app
│   ├── routes/            # API endpoints
│   └── services/          # Business logic
├── cli/                    # CLI Package
│   ├── main.py            # CLI entry point (Typer app)
│   ├── client/            # API client wrapper
│   │   └── api_client.py
│   └── config/            # Config management
│       ├── models.py      # Pydantic models
│       └── manager.py     # Encryption, persistence
└── ~/.mira/               # User config (created at runtime)
    ├── config.yaml        # User configuration
    └── .key               # Encryption key (0600 permissions)
```

### Entry Point

**[pyproject.toml:25](pyproject.toml#L25)**
```toml
[project.scripts]
mira = "cli.main:app"
```

This creates the `mira` command that runs the Typer app in `cli/main.py`.

### Configuration File

**Location:** `~/.mira/config.yaml` (Linux/Mac) or `C:\Users\<user>\.mira\config.yaml` (Windows)

**Contents:**
```yaml
version: "2.0"

server:
  url: "localhost"
  port: 8000
  auto_start: false

moorcheh:
  api_key_encrypted: "gAAAAABf..."  # Fernet encrypted Moorcheh API key

session:
  default_duration_hours: 6
  auto_extend: true

cli:
  interactive_mode: true
  smart_parse: true
  color_output: true

# Answer configuration (all optional — defaults shown)
answer:
  model: "anthropic.claude-sonnet-4-6"  # LLM used for answer
  temperature: 0.7        # LLM temperature (0.0–1.0)
  answer_limit: 5         # context memories passed to LLM for `answer`
  threshold: 0.15         # similarity floor applied only when kiosk_mode is true
  kiosk_mode: false       # set true to filter low-relevance results using threshold

# Recall configuration
recall:
  limit: 10               # top-N results returned by `recall`

active_agent_id: "code-assistant"
active_session_token: "eyJhbGciOiJIUzI1NiI..."
```


**Security:**
- API key encrypted with Fernet (symmetric encryption)
- Encryption key in `~/.mira/.key` with 0600 permissions
- Never commit config files to version control

---

## Troubleshooting

### "mira: command not found"

**Cause:** Package not installed or not in PATH

**Solution:**
```bash
# If installed with pip:
pip install mira

# If installed from source:
cd mira
pip install -e .

# Verify:
which mira  # Should show path to command
mira --help # Should work
```

### "Connection failed" Error

**Cause:** MIRA server not running

**Check:**
```bash
# Is server running?
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"MIRA","version":"1.0.0"}
```

**Solution:**
```bash
# Start server in a separate terminal
cd mira
python -m app.main
```

### "No active agent" Error

**Cause:** Trying to use memory commands without an active session

**Solution:**
```bash
# List available agents
mira agent list

# Activate one
mira agent activate AGENT_ID
```

### "MIRA not configured" Error

**Cause:** CLI not configured

**Solution:**
```bash
mira
# Follow the prompts
```

### Session Expired

**Cause:** JWT token expired (default: 4 hours)

**Solution:**
```bash
# Reactivate
mira agent activate AGENT_ID
```

### Windows Unicode Errors

All Unicode symbols (✓ ✗ ⚠ 🟢) replaced with ASCII equivalents (OK, ERROR, Warning, [Active]).

If you still see encoding errors, ensure your terminal uses UTF-8:
```bash
# PowerShell
chcp 65001

# CMD
chcp 65001
```

---

## Next Steps

1. **Try the Quick Start workflow** (5 minutes)
2. **Read the [CLI User Guide](CLI_USER_GUIDE.md)** for detailed examples
3. **Explore memory types** - fact, decision, instruction, etc.
4. **Set up automation** - Use CLI in scripts

---

## Support

- **Documentation:** [CLI_USER_GUIDE.md](CLI_USER_GUIDE.md)
- **API Reference:** [V2_QUICK_START.md](V2_QUICK_START.md)
- **Issues:** GitHub Issues
- **Moorcheh:** [moorcheh.ai/docs](https://moorcheh.ai/docs)

---

**License**: MIT
**Last Updated**: December 2025

