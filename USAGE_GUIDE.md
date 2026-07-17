# VibeCode Usage Guide

VibeCode is an agentic coding CLI: you give it a free-form task, and its reasoning
loop decides which tools to call — reading files, writing files (with your approval),
running shell commands, searching the web, or delegating a subtask to a sub-agent —
until the task is done.

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set ANTHROPIC_API_KEY
```

## Two Usage Modes

### Mode 1: Single Task

For a one-off task:

```bash
python run_vibe.py "add error handling to src/utils.py"
```

**What happens:**
1. 🧠 Context loads (`CLAUDE.md` + any `skills/*/SKILL.md`) into the system prompt
2. 🔄 The agent reasons and calls tools as needed (file_read, file_write, bash,
   web_search, or Task to delegate)
3. 📝 Any file write shows a diff and asks for approval before it lands on disk
4. ✅ The agent reports back when the task is done

**Best for:** A single well-scoped task.

---

### Mode 2: Interactive REPL

For working across multiple tasks in one session, with context and memory shared:

```bash
python run_vibe.py
```

**What happens:**
1. 🧠 Context and Memory load once for the whole process
2. 📝 Prompts: `›` — type a task, or `quit`/`exit` to leave
3. 🔄 The agent runs its reasoning loop for that task
4. 🔁 Repeat — memory persists across tasks in the same run

**Best for:** Iterating on a project across several requests without losing context.

---

## Interactive Session Example

```
VibeCode — describe a task, or 'quit' to exit.
› add a docstring to src/utils.py

-> file_read({'path': 'src/utils.py'})
--- src/utils.py (original)
+++ src/utils.py (edited)
@@ -1,3 +1,4 @@
+"""Utility helpers for the project."""
 def helper():
     return 42
Apply changes? (y)es / (n)o / (e)dit: y
Wrote src/utils.py.

Done — added a module docstring to src/utils.py.

› quit
```

---

## The FileWrite Diff/Approval Gate

Every write goes through the `file_write` tool, which is intrinsic to the tool
itself — not something that can be turned off by removing a hook:

- **(y)es** — writes the file, applying the shown diff.
- **(n)o** — declines; the file is left untouched and the agent is told the write
  was declined so it doesn't retry blindly.
- **(e)dit** — tells the agent you'll edit the file yourself instead.

## Hooks

Two hooks are wired in by default around every tool call:

- **LoggingHook** — appends a JSON line per tool call to
  `.vibecode/logs/tool_calls.jsonl` (never blocks).
- **BashConfirmationHook** — before running any `bash` command, shows it and asks
  for confirmation; declining blocks the call.

## Sub-Agents and the Task Tool

The agent can delegate work via the `Task` tool:
- `subagent_type="large-file-editor"` — for a single file over ~200 lines. Instead
  of rewriting the whole file, it parses the file into AST blocks, edits just the
  relevant chunk, merges it back, and validates the merge against a temporary copy
  before the usual diff+approval gate.
- `subagent_type="general-purpose"` — a nested reasoning loop with a restricted tool
  set (`file_read`, `file_write`, `bash`, `web_search` — no further delegation, no
  shared memory) for any other self-contained subtask.

## Memory

`.vibecode/memory.json` holds the conversation across turns in a session. Once the
serialized history passes a size threshold, the oldest messages are summarized in
one extra Claude call and replaced with a single summary entry, keeping the most
recent messages verbatim — so long-running sessions don't grow unbounded.

## Configuration

### API Key

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Model

Default is `claude-opus-4-8`. Override per-invocation:

```bash
python run_vibe.py --model claude-sonnet-5 "summarize the README"
```

---

## Architecture Overview

```
You ──task──▶ Agent (Reasoning Loop) ──call──▶ Hooks ──▶ Tools
                  │      ▲                              (FileRead, FileWrite,
        delegate  │      │ results                       Bash, WebSearch)
      subtasks    ▼      │
              Sub-Agents ┘
                  │
      on startup  │             read/write
                  ▼             context
              Context ◀──────────────────────▶ Memory
          (CLAUDE.md, skills/)          (.vibecode/memory.json,
                                          auto-compacts when full)
```

- `src/vibecode/agent/` — reasoning loop, Anthropic client, system prompt assembly
- `src/vibecode/tools/` — FileRead, FileWrite, Bash (client-side) + WebSearch
  (Anthropic server-side tool)
- `src/vibecode/hooks/` — pre/post tool-call interception
- `src/vibecode/subagents/` — Task tool, generic sub-agent runner, large-file-editor
- `src/vibecode/context/` — CLAUDE.md/skills loader, plus project indexing utilities
  (AST analyzer, project graph, SQLite index)
- `src/vibecode/memory/` — persistent session memory with compaction
- `src/vibecode/diff/`, `src/vibecode/ui/` — diff generation and terminal display

## Troubleshooting

### `ANTHROPIC_API_KEY is not set`
Copy `.env.example` to `.env` and add your key.

### FileNotFoundError from `file_read`
The agent will report the missing path back to itself and usually recover by
asking you or trying a different path — check the path you gave it in your task.

### Declined a write by mistake
Just describe the task again; nothing was written to disk.

## Running Tests

```bash
pip install pytest
pytest tests/
```
