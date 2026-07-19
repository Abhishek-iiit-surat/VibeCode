# VibeCode

A terminal-based agentic coding assistant built on the Anthropic Claude API's native
tool-use loop — the same shape as Claude Code itself: an Agent reasoning loop that
calls Tools (FileRead, FileWrite, Bash, WebSearch) through Hooks, can delegate to
Sub-Agents, loads Context (`CLAUDE.md` + `skills/`) on startup, and reads/writes a
persistent Memory store that auto-compacts.

**Key Features:**
- 🤖 Free-form task descriptions (e.g., "add type hints to this function") — the
  agent decides which tools to use, not you
- 🔒 Safe by construction — the FileWrite tool always shows a unified diff and asks
  for approval before anything touches disk
- 🧩 Sub-agent delegation for large files — a specialized AST-chunked editor handles
  files over ~200 lines instead of rewriting them whole
- 🪝 Hooks around every tool call — a bash-confirmation gate and a JSONL audit log
  are wired in by default
- 🧠 Persistent memory across turns, with automatic summarize-and-trim compaction
- 🔄 Anthropic Claude only (`claude-sonnet-4-6` by default, override with `--model`)

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
```

## Usage

```bash
python run_vibe.py "add a docstring to utils.py"   # single task
python run_vibe.py                                  # interactive REPL
```

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for the full architecture overview and
walkthrough.
