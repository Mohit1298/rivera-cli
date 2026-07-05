<div align="center">
  <h1>🌊 Mira</h1>
  <h3>Persistent memory for your AI coding agents</h3>
  <p><em>Your agents forget everything between sessions. Mira makes them remember.</em></p>
  <p>
    <a href="https://api.wirtel.ca">Rivera Cloud</a> ·
    <a href="https://api.wirtel.ca/documentation">Docs</a> ·
    <a href="https://api.wirtel.ca/console">Console</a>
  </p>
</div>

---

Every time Claude Code, Cursor, or Codex starts a fresh session, it starts from zero —
your preferences, your past decisions, and your codebase's quirks are gone. Mira is a
memory CLI that persists all of that across sessions and across tools, backed by
[Rivera](https://api.wirtel.ca), a semantic memory engine with exact (non-approximate)
vector search and zero indexing delay: store a memory and it is searchable the same
millisecond.

```
$ mira remember "cua-driver Rust build needs DEVELOPER_DIR pointing at full Xcode" --type fact
Memory stored successfully!  Type: fact | Confidence: 0.95

$ mira recall "how do I build the rust driver"
→ cua-driver Rust build needs DEVELOPER_DIR pointing at full Xcode   (score 0.39)

$ mira answer "what does the rust build need?"
→ The build requires full Xcode via DEVELOPER_DIR (Source: chunk 1).
```

## Three primitives

| Command | What it does |
|---|---|
| `mira remember` | Store a typed memory — searchable instantly, no indexing wait |
| `mira recall` | Semantic search over everything stored, with temporal filters (`--as-of`, `--changed-since`, `--recent`) |
| `mira answer` | One grounded, cited answer synthesized from your memories (RAG built in) |

Memories are **typed** (13 categories: `fact`, `preference`, `decision`, `goal`,
`instruction`, `learning`, `error`, …) and carry **confidence** and **provenance**
metadata, so an explicit user statement never gets confused with an inferred hunch.

## Quickstart

```bash
# 1. Install
pip install git+https://github.com/Mohit1298/mira.git

# 2. Get a free API key at https://api.wirtel.ca/signup
#    (free plan: 2,000 requests + 200 GenAI answers / month)
export RIVERA_API_KEY="rv_..."

# 3. Create your agent and go
mira agent create my-agent
mira remember "User prefers concise answers" --type preference
mira recall "communication style"
mira answer "what did we decide about the database schema?"
```

Configuration lives in `~/.mira/` (`.env` for credentials, `config.yaml` for settings).
Point at a different Rivera deployment with `RIVERA_BASE_URL`.

## Agent integrations

Connect Mira to your coding agent so memory works automatically — context injected at
session start, durable decisions captured as you work:

```bash
mira connect claude-code    # also: cursor, codex, windsurf, cline, continue, ...
```

## More than a CLI

- **Local REST API + Web UI** — `mira serve` / `mira ui`
- **Batch ingestion** — `mira remember --batch memories.json`, `--from-conversation` to
  extract facts from chat logs, `mira upload` for PDF/DOCX/CSV/MD files
- **Memory hygiene** — `mira conflicts` detects contradictions; `mira daily-summary`
  digests what changed; `mira edit` / `mira forget` for corrections
- **Project sync** — `mira memory sync` writes a `MEMORY.md` snapshot into your repo

## How it works

```
mira CLI ──HTTPS──▶ Rivera (api.wirtel.ca)
                      ├─ exact cosine search over pgvector (no ANN, deterministic)
                      ├─ OpenAI embeddings (text-embedding-3-small)
                      └─ grounded answers (gpt-4o-mini) with citations
```

Your memories live in your Rivera account — per-tenant isolation, API keys hashed at
rest, revocable from the [console](https://api.wirtel.ca/console). Self-hosting Rivera
is possible too: the backend is a standard FastAPI + Postgres/pgvector service.

## Acknowledgments

Mira began as a fork of [memanto](https://github.com/moorcheh-ai/memanto) (MIT, EdgeAI
Innovations Inc.) and preserves its excellent typed-memory model and CLI ergonomics.
The backend, retrieval engine, auth, and cloud service are Rivera — an independent
implementation. See [LICENSE](LICENSE).

## License

MIT
