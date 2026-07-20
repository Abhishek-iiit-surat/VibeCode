"""
Assembles the system prompt sent to Claude from the fixed base instructions,
the loaded Context (CLAUDE.md + skills), and the available tool names.
"""

from vibecode.context.loader import ProjectContext

# Tool names referenced by name in BASE_SYSTEM_PROMPT's prose. Checked against
# the live registry in build_system_prompt so a rename/removal fails loudly
# at startup instead of leaving the prompt silently referring to a tool that
# no longer exists.
PROMPT_REFERENCED_TOOLS = ["file_read", "file_write", "bash", "search"]

BASE_SYSTEM_PROMPT = (
    "You are VibeCode, an agentic coding assistant running in a terminal. "
    "Read each tool's description before calling it — approval, confirmation, "
    "and safety behavior for each tool lives there, not here. "
    "file_read, file_write, and search all accept absolute paths, not just "
    "paths relative to the project root — use an absolute path whenever the "
    "user references a file or directory outside the current project. "
    "Delegate to sub-agents via Task for self-contained exploration or "
    "subtasks, to keep open-ended search out of your own context — not "
    "because a file is large. "
    "In a large or unfamiliar codebase, search before you read: use the "
    "search tool (glob for filenames, pattern for content) to locate the "
    "relevant file and line range before reading whole files. "
    "After making a code change, verify it: run the project's tests or "
    "build if one exists (check CLAUDE.md or look for a test/build command) "
    "before considering the task done. "
    "If a request is ambiguous or underspecified, don't guess silently — "
    "state the assumption you're making and proceed, or ask a clarifying "
    "question if the ambiguity is high-stakes (e.g. could delete data or "
    "change behavior broadly)."
)


def build_system_prompt(context: ProjectContext, tool_names: list) -> str:
    missing = [name for name in PROMPT_REFERENCED_TOOLS if name not in tool_names]
    if missing:
        raise ValueError(
            f"BASE_SYSTEM_PROMPT references tool(s) {missing} by name, but they "
            f"aren't in the registry ({tool_names}). Update PROMPT_REFERENCED_TOOLS "
            "and the prompt text together with the tool rename/removal."
        )

    parts = [BASE_SYSTEM_PROMPT, f"Available tools: {', '.join(tool_names)}."]

    if context.claude_md:
        parts.append("# Project instructions (CLAUDE.md)\n\n" + context.claude_md)

    for skill in context.skills:
        parts.append(f"# Skill: {skill.name}\n\n{skill.content}")

    return "\n\n".join(parts)
