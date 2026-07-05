"""
MIRA CLI - Connect Templates

Per-agent instruction content and skill templates for MIRA integration.
"""


# Shared MIRA Sentinel markers

MIRA_SENTINEL = "<!-- MIRA-MANAGED-SECTION -->"
MIRA_SENTINEL_END = "<!-- /MIRA-MANAGED-SECTION -->"


# Shared SKILL.md content (same across all agents)

SKILL_MD_CONTENT = """---
name: mira-memory
description: Use this skill when you need to store or search MIRA persistent memories. It defines mandatory guidelines for best practices, memory types, confidence levels, tagging, and patterns for effective agent memory usage.
---

# MIRA Memory Skill

Detailed reference for using MIRA persistent memory effectively.

## Memory Types: Decision Matrix

| Type | When to Use | Confidence | Example |
|------|-------------|------------|---------|
| `fact` | Verified information, project status | 0.9-1.0 | "MIRA uses PostgreSQL for metadata" |
| `decision` | Architecture choices, approach selections | 0.9-1.0 | "Chose React over Vue for frontend" |
| `instruction` | Standing rules, preferences, guidelines | 0.9-1.0 | "Always use type hints in Python" |
| `commitment` | Promises, TODOs, obligations | 1.0 | "Will deploy monitoring by Friday" |
| `preference` | User/team preferences | 0.8-1.0 | "User prefers dark mode" |
| `goal` | Objectives, targets, milestones | 0.8-1.0 | "Launch CLI by end of March" |
| `artifact` | Tool outputs, reports, file locations | 0.9-1.0 | "Report saved at ./reports/q1.md" |
| `learning` | Knowledge acquired from experience | 0.7-0.9 | "Batch operations 100x faster" |
| `event` | Important conversations, milestones | 0.8-0.95 | "Completed Phase 1 features" |
| `relationship` | Team context, collaboration patterns | 0.85-0.95 | "Alice is lead backend engineer" |
| `observation` | Patterns noticed, behaviors | 0.6-0.85 | "User prefers short responses" |
| `error` | Failures, bugs, lessons learned | 0.95-1.0 | "Namespace format bug - use underscores" |
| `context` | Session summaries, status updates | 0.9-1.0 | "Project 70% done, API complete" |

## Confidence Levels

- **1.0** — Explicit user statement, verified fact, standing instruction
- **0.9-0.95** — Strong consensus, well-tested approach, clear team preference
- **0.8-0.85** — Observed pattern (3+ times), indirect but supported preference
- **0.7-0.75** — Emerging pattern (2 times), reasonable inference
- **0.6-0.65** — Single observation, uncertain interpretation
- **< 0.6** — Don't store. Too uncertain.

## Provenance Types

Always categorize the source of the memory. Valid options:
- `explicit_statement` — Directly stated by user
- `inferred` — Derived from behavior/context
- `observed` — Seen in action
- `corrected` — Updated after contradiction
- `validated` — Confirmed/verified
- `imported` — Brought in from an external source (file upload, sync, migration)

## Source Types

Always specify the tool or agent creating the memory.
- For AI agents: Use the agent name (e.g., `--source claude_code` or `--source cursor`)
- Valid base sources (if not using specific agent name): `user`, `agent`, `tool`, `system`

## Tagging Best Practices

Use 2-5 tags per memory. Tags make memories findable.

Good: `--tags "authentication,oauth,security"`
Good: `--tags "bug-fix,namespace,commit-3f39351"`
Bad: `--tags "important"` (too generic)
Bad: `--tags "thing"` (not descriptive)

Conventions:
- Lowercase with hyphens: `bug-fix` not `BugFix`
- Be specific: `authentication-oauth` not `auth`
- Include refs: `commit-abc123` for git references

## Patterns

### Session Start
```bash
# recall — load raw context (instructions, decisions, goals) to guide this session
mira recall "instructions decisions goals" --limit 20

# answer — get a direct synthesized summary of pending commitments
mira answer "What are my pending commitments?"
```

### After Important Work
```bash
mira remember "Implemented X using approach Y because Z. Commit abc123." --type decision --tags "feature-x" --confidence 0.95 --provenance "inferred" --source "claude_code"
mira remember "Learned that batch ops reduce API calls 100x." --type learning --tags "performance" --confidence 0.85 --provenance "observed" --source "claude_code"
```

### When User Corrects You
```bash
mira remember "User corrected: prefer pytest over unittest." --type learning --tags "correction,testing" --confidence 1.0 --provenance "corrected" --source "claude_code"
```

### Choosing Between recall and answer

These are **equal-priority tools**. Pick the right one — do NOT always default to `recall`.

| Situation | Use |
|-----------|-----|
| Need raw memory chunks to read and apply as context | `recall` |
| Need a direct synthesized answer to give (or act on) | `answer` |
| Building context before a complex multi-step task | `recall` |
| User asks "what did we decide / prefer / commit to?" | `answer` |
| Comparing multiple matching memories | `recall` |
| Need one grounded yes/no or summary response | `answer` |

**Decision rule**: If your next step is *"read these memories and act"* → `recall`. If your next step is *"answer this question directly"* → `answer`. Both save tokens equally — `answer` synthesizes so you don't have to.

```bash
# Use recall — need raw context to work from
mira recall "authentication approach" --limit 10

# Use answer — need a direct synthesized answer
mira answer "What auth approach did we decide on and why?"
```

## Pitfalls to Avoid

1. **Memory hoarding** — Ask "Will this matter in a week?" before storing
2. **Vague content** — Bad: "better performance" → Good: "API response < 200ms"
3. **No context** — Bad: "fixed bug" → Good: "Fixed OAuth expiry bug. Commit abc123."
4. **Duplicates** — Search first (`mira recall`), then store if not found
5. **Missing tags** — Always include tags for retrieval

## recall vs answer: Choose the Right Tool

**Equal priority** — do NOT always default to `recall`. Pick based on what you need next:

| Use `recall` when... | Use `answer` when... |
|---------------------|---------------------|
| You need raw memory chunks as context | You need one direct synthesized response |
| Building context before a complex task | User asks "what did we decide / prefer?" |
| Comparing or reviewing multiple memories | Getting a grounded summary or yes/no |
| Next step: *read these and act on them* | Next step: *deliver this as the answer* |

**Short rule**: need context to work from → `recall`. Need a ready answer → `answer`. Both save the agent tokens and time — `answer` synthesizes so you don't have to read and merge manually.

## Command Reference

```bash
# Store memory
mira remember "content" --type TYPE --tags "tag1,tag2" --confidence 0.9 --provenance "inferred" --source "claude_code"

# Raw memory search (use for context-building, multi-step tasks)
mira recall "query" --limit 10 --type TYPE --min-similarity 0.8

# Temporal recall variants (no query needed)
mira recall --recent --limit 10                 # newest first
mira recall --as-of "2026-01-15"                # state at a point in time
mira recall --changed-since "last 7 days"       # what changed since

# Synthesized answer (use for direct questions, "what did we decide about X?")
mira answer "question"

# Sync memories to project
mira memory sync --project-dir .
```
"""


# Per-agent instruction content


def _base_instruction_content(
    tool_phrase: str = "the terminal", note_suffix: str = ""
) -> str:
    """Generate base MIRA instruction content, adapted per agent."""
    note_line = ""
    if note_suffix:
        note_line = f"\n> **Note**: {note_suffix}"

    return f"""{MIRA_SENTINEL}
## MIRA - Your Active Memory Companion

**MIRA is not a passive store. It is an active companion agent that works alongside you.**
Don't treat MIRA like a static blob you query once and forget. It's a teammate you keep
talking to, every preference, decision, and correction flows through it. MIRA remembers,
recalls, and answers so you hold context across sessions, honor prior decisions, and avoid
repeating mistakes the user already corrected.

Every memory operation in this session goes through MIRA. There is no exception.

> **CRITICAL**: All `mira` commands are **shell commands**. Always run them using {tool_phrase}.
> Never simulate, describe, or "pretend to call" them. If you cannot run the shell, say so explicitly instead of inventing memory state.

### NON-NEGOTIABLE RULES

These are not suggestions. Follow each one on every turn.

1. **Read `MEMORY.md` before doing anything.** It is auto-synced at session start and holds
   the user's preferences, facts, goals, instructions, decisions, and commitments from every
   prior session. You MUST honor what is written there. If you act against it, you are
   breaking continuity the user is paying for.
2. **Search memory before saying you don't know.** If the user asks about past context, an
   earlier decision, a preference, or anything you are unsure about, you MUST run `recall`
   or `answer` first. Saying "I don't have context" without searching is a failure.
3. **Store proactively. Do not wait to be asked.** The moment a memory-worthy event happens
   — a preference stated, a decision made, a fact learned, an instruction given, a goal set,
   a mistake corrected — run `mira remember` immediately, in the same turn.
4. **Always pass full metadata to `remember`.** Every `mira remember` call MUST include
   `--type`, `--confidence`, `--provenance`, and `--source <your_agent_name>`. Never let
   these default. Untyped, unsourced memories pollute the agent's recall quality.
5. **One memory operation goes through MIRA. All of them do.** Do not keep mental notes,
   in-context scratch pads, or "I'll remember this for next time" promises. If it matters
   beyond this turn, it goes into MIRA. If it doesn't, drop it.

### Memory Operations — Use the Right One

MIRA gives you three primitives. They are equal-priority. Pick by intent, not by habit.

| You want to... | Use | Why |
|---|---|---|
| Read raw memory chunks and apply them as context | `mira recall "query"` | Best for context-building, multi-step work, comparing options |
| Get one synthesized, grounded answer to a direct question | `mira answer "question"` | Best for "what did we decide / prefer / commit to?" — saves you reading and merging |
| Persist something memory-worthy | `mira remember "content" --type ... --confidence ... --provenance ... --source ...` | Every preference, decision, fact, instruction, goal, lesson |
| See what changed since last time | `mira recall --changed-since "last 7 days"` | Catching up after a break |
| See the most recent memories | `mira recall --recent` | Fast context refresh |

Do NOT always default to `recall`. If the user asked a direct question, `answer` is usually
the right tool — it returns a grounded synthesis so you don't burn tokens re-reading raw
chunks.

### When to Call `remember` (Examples — Run Immediately)

- User says *"I prefer tabs over spaces"*:
  `mira remember "User prefers tabs over spaces for indentation" --type preference --confidence 1.0 --provenance explicit_statement --source <your_agent_name>`
- You decide to use Library X for reason Y:
  `mira remember "Chose Library X for reason Y; commit abc123" --type decision --confidence 0.95 --provenance inferred --source <your_agent_name>`
- User corrects an approach:
  `mira remember "User corrected: use pytest, not unittest" --type learning --confidence 1.0 --provenance corrected --source <your_agent_name>`
- A failed approach taught you something:
  `mira remember "Batch size > 100 fails with TimeoutError" --type error --confidence 0.95 --provenance observed --source <your_agent_name>`

### Command Reference

```bash
# Store — ALWAYS pass full metadata
mira remember "content" --type <type> --confidence <0.0-1.0> --provenance <provenance> --source <agent_name>

# Recall raw context
mira recall "query"                              # semantic search
mira recall "query" --type <type> --limit 10     # filtered search
mira recall --recent --limit 10                  # newest first, no query
mira recall --as-of "2026-01-15"                 # state at a point in time
mira recall --changed-since "last 7 days"        # what changed since

# Synthesized answer (grounded RAG over memories)
mira answer "question"

# Re-sync MEMORY.md (project-local cache)
mira memory sync --project-dir .
```

**Memory types** (use the closest fit, do not invent new ones):
`fact`, `preference`, `instruction`, `decision`, `event`, `goal`, `commitment`,
`observation`, `learning`, `relationship`, `context`, `artifact`, `error`.

**Provenance values**: `explicit_statement`, `inferred`, `observed`, `corrected`,
`validated`, `imported`.

**Confidence**: `1.0` for explicit user statements; `0.9-0.95` for strong consensus;
`0.8-0.85` for observed patterns (3+ times); `0.6-0.75` for emerging patterns.
{note_line}
{MIRA_SENTINEL_END}"""


def get_instruction_content(agent_name: str) -> str:
    """Get MIRA instruction section content for a specific agent."""
    templates = {
        "claude-code": _base_instruction_content(
            tool_phrase="the Bash tool",
            note_suffix="The `mira-memory` skill contains reference guidelines only (best practices, confidence levels, tagging). It is NOT executable — always use Bash for mira commands.",
        ),
        "codex": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="The `mira-memory` skill in `.agents/skills/mira/` contains detailed reference guidelines (best practices, confidence levels, tagging).",
        ),
        "cursor": _get_mdc_content(),
        "windsurf": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="The `mira-memory` skill in `.windsurf/skills/mira/` contains detailed reference guidelines.",
        ),
        "gemini-cli": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="The `mira-memory` skill in `.gemini/skills/mira/` contains detailed reference guidelines.",
        ),
        "cline": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="Run `mira memory sync --project-dir .` at the start of each session to populate MEMORY.md.",
        ),
        "continue": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="Run `mira memory sync --project-dir .` at the start of each session to populate MEMORY.md.",
        ),
        "opencode": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="The `mira-memory` skill in `.agents/skills/mira/` contains detailed reference guidelines.",
        ),
        "roo": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="Run `mira memory sync --project-dir .` at the start of each session to populate MEMORY.md.",
        ),
        "github-copilot": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="Run `mira memory sync --project-dir .` at the start of each session to populate MEMORY.md.",
        ),
        "augment": _base_instruction_content(
            tool_phrase="the terminal",
            note_suffix="The `mira-memory` skill in `.augment/skills/mira/` contains detailed reference guidelines.",
        ),
    }
    return templates.get(agent_name, _base_instruction_content())


def _get_mdc_content() -> str:
    """Get MDC-formatted rules content for Cursor."""
    return f"""---
description: MIRA — active memory companion. Mandatory rules for storing, recalling, and answering from persistent memory.
alwaysApply: true
---

{MIRA_SENTINEL}

# MIRA — Your Active Memory Companion

**MIRA is not a passive store. It is an active companion agent that works alongside you.**
Don't treat MIRA like a static blob you query once and forget. It's a teammate you keep
talking to — every preference, decision, and correction flows through it. MIRA remembers,
recalls, and answers so you hold context across sessions, honor prior decisions, and avoid
repeating mistakes the user already corrected. Every memory operation in this session goes
through MIRA.

> **CRITICAL**: All `mira` commands are **shell commands**. Always run them in the terminal.
> Never simulate or "pretend to call" them. If you cannot run the shell, say so explicitly
> instead of inventing memory state.

## NON-NEGOTIABLE RULES

1. **Sync and read `MEMORY.md` at session start.** Run `mira memory sync --project-dir .`
   then read `MEMORY.md` in the project root. It holds the user's preferences, facts,
   goals, instructions, decisions, and commitments from every prior session. You MUST
   honor what is written there.
2. **Search memory before saying you don't know.** If the user asks about past context,
   an earlier decision, a preference, or anything you are unsure about, you MUST run
   `recall` or `answer` first.
3. **Store proactively. Do not wait to be asked.** The moment a memory-worthy event
   happens — a preference stated, a decision made, a fact learned, an instruction given,
   a goal set, a mistake corrected — run `mira remember` immediately, in the same turn.
4. **Always pass full metadata to `remember`.** Every call MUST include `--type`,
   `--confidence`, `--provenance`, and `--source <your_agent_name>`. Never let these
   default.
5. **All memory operations go through MIRA.** No mental scratch pads, no "I'll
   remember this next time." If it matters beyond this turn, it goes into MIRA.

## Memory Operations — Use the Right One

```bash
mira recall "query"      # raw memory chunks — for context-building, multi-step work
mira answer "question"   # one synthesized, grounded answer — for direct questions
mira recall --recent     # newest first, no query needed
mira recall --changed-since "last 7 days"
mira remember "content" --type <type> --confidence <0.0-1.0> --provenance <provenance> --source <agent_name>
mira memory sync --project-dir .
```

Do NOT always default to `recall`. `recall` returns raw chunks (best for context-building);
`answer` returns one grounded synthesis (best for "what did we decide / prefer / commit
to?"). Equal priority — pick by intent.

**Memory types**: `fact`, `preference`, `instruction`, `decision`, `event`, `goal`,
`commitment`, `observation`, `learning`, `relationship`, `context`, `artifact`, `error`.

**Provenance**: `explicit_statement`, `inferred`, `observed`, `corrected`, `validated`,
`imported`.

**Confidence**: `1.0` for explicit user statements; `0.9-0.95` strong consensus;
`0.8-0.85` for patterns seen 3+ times; below `0.6` — do not store.

{MIRA_SENTINEL_END}"""


def get_skill_content() -> str:
    """Get the SKILL.md content (shared across all agents)."""
    return SKILL_MD_CONTENT.strip() + "\n"
