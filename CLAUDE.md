# VibeCode

VibeCode is a terminal-based agentic coding CLI built on the Anthropic Claude API's
native tool-use loop (Claude-Code-style architecture): an Agent reasoning loop, a Tools
registry (FileRead / FileWrite / Bash / WebSearch / Task), Hooks for pre/post tool-call
interception, Sub-Agents for delegated work, Context loaded from this file plus
`skills/`, and a persistent Memory store with auto-compaction.

## Project layout
- `src/vibecode/agent/` — reasoning loop, Anthropic client, system prompt assembly
- `src/vibecode/tools/` — tool registry + built-in tools (FileRead, FileWrite, Bash;
  WebSearch is a server-side tool schema, not client code)
- `src/vibecode/hooks/` — pre/post tool-call interception (logging, bash confirmation)
- `src/vibecode/subagents/` — the Task tool, a generic sub-agent runner, and the
  large-file-editor sub-agent (AST-chunked edit/validate/refine loop)
- `src/vibecode/context/` — project indexing (AST analyzer, project graph, SQLite
  index) plus the CLAUDE.md/skills loader
- `src/vibecode/memory/` — persistent session memory with compaction
- `src/vibecode/diff/`, `src/vibecode/ui/` — diff generation and terminal display

## Conventions
- File edits only happen through the FileWrite tool, which always shows a unified diff
  and asks for approval before writing — never write files any other way.
- Files over ~200 lines should generally be delegated to the `large-file-editor`
  sub-agent via the Task tool rather than edited in one shot.
- Entry point: `python run_vibe.py "<task description>"` (or no args for the
  interactive REPL).
- Run tests with `pytest tests/`.

## Do not
- Do not reintroduce AgentFS or the `agentfs-sdk` dependency — direct filesystem tools
  with diff+approval replaced it.
- Do not add OpenAI SDK calls — this project is Anthropic-only.
- Do not bypass the FileWrite tool's diff/approval step, even for "trivial" changes.
