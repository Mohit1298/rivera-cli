<div align="center">
  <h1>🌊 Rivera</h1>
  <h3>Persistent memory for your AI coding agents</h3>
  <p><em>Your agents forget everything between sessions. Rivera makes them remember.</em></p>
  <p>
    <a href="https://api.wirtel.ca">Rivera Cloud</a> ·
    <a href="https://api.wirtel.ca/documentation">Docs</a> ·
    <a href="https://api.wirtel.ca/console">Console</a>
  </p>
</div>

---

Every time Claude Code, Cursor, or Codex starts a fresh session, it starts from zero —
your preferences, your past decisions, and your codebase's quirks are gone. Rivera is a
memory CLI that persists all of that across sessions and across tools, backed by
[Rivera](https://api.wirtel.ca), a semantic memory engine with exact (non-approximate)
vector search and zero indexing delay: store a memory and it is searchable the same
millisecond.

```
$ rivera remember "cua-driver Rust build needs DEVELOPER_DIR pointing at full Xcode" --type fact
Memory stored successfully!  Type: fact | Confidence: 0.95

$ rivera recall "how do I build the rust driver"
→ cua-driver Rust build needs DEVELOPER_DIR pointing at full Xcode   (score 0.39)

$ rivera answer "what does the rust build need?"
→ The build requires full Xcode via DEVELOPER_DIR (Source: chunk 1).
```

## Three primitives

| Command | What it does |
|---|---|
| `rivera remember` | Store a typed memory — searchable instantly, no indexing wait |
| `rivera recall` | Semantic search over everything stored, with temporal filters (`--as-of`, `--changed-since`, `--recent`) |
| `rivera answer` | One grounded, cited answer synthesized from your memories (RAG built in) |

Memories are **typed** (13 categories: `fact`, `preference`, `decision`, `goal`,
`instruction`, `learning`, `error`, …) and carry **confidence** and **provenance**
metadata, so an explicit user statement never gets confused with an inferred hunch.

## Quickstart

```bash
# 1. Install
pip install rivera-cli

# 2. Get a free API key at https://api.wirtel.ca/signup
#    (free plan: 2,000 requests + 200 GenAI answers / month)
export RIVERA_API_KEY="rv_..."

# 3. Create your agent and go
rivera agent create my-agent
rivera remember "User prefers concise answers" --type preference
rivera recall "communication style"
rivera answer "what did we decide about the database schema?"
```

Configuration lives in `~/.rivera/` (`.env` for credentials, `config.yaml` for settings).
Point at a different Rivera deployment with `RIVERA_BASE_URL`.

## Agent integrations

Connect Rivera to your coding agent so memory works automatically — context injected at
session start, durable decisions captured as you work:

```bash
rivera connect claude-code    # also: cursor, codex, windsurf, cline, continue, ...
```

## More than a CLI

- **Local REST API + Web UI** — `rivera serve` / `rivera ui`
- **Batch ingestion** — `rivera remember --batch memories.json`, `--from-conversation` to
  extract facts from chat logs, `rivera upload` for PDF/DOCX/CSV/MD files
- **Memory hygiene** — `rivera conflicts` detects contradictions; `rivera daily-summary`
  digests what changed; `rivera edit` / `rivera forget` for corrections
- **Project sync** — `rivera memory sync` writes a `MEMORY.md` snapshot into your repo

## How it works

```
rivera CLI ──HTTPS──▶ Rivera (api.wirtel.ca)
                      ├─ exact cosine search over pgvector (no ANN, deterministic)
                      ├─ OpenAI embeddings (text-embedding-3-small)
                      └─ grounded answers (gpt-4o-mini) with citations
```

Your memories live in your Rivera account — per-tenant isolation, API keys hashed at
rest, revocable from the [console](https://api.wirtel.ca/console). Self-hosting Rivera
is possible too: the backend is a standard FastAPI + Postgres/pgvector service.

## Acknowledgments

Rivera began as a fork of [memanto](https://github.com/moorcheh-ai/memanto) (MIT, EdgeAI
Innovations Inc.) and preserves its excellent typed-memory model and CLI ergonomics.
The backend, retrieval engine, auth, and cloud service are Rivera — an independent
implementation. See [LICENSE](LICENSE).

## License

MIT
