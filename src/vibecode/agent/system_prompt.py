"""
Assembles the system prompt sent to Claude from the fixed base instructions,
the loaded Context (CLAUDE.md + skills), and the available tool names.
"""

from vibecode.context.loader import ProjectContext

BASE_SYSTEM_PROMPT = (
    "You are VibeCode, an agentic coding assistant running in a terminal. "
    "You have tools to read files, write files, run shell commands, and "
    "delegate to sub-agents via Task (use subagent_type='large-file-editor' "
    "for files over ~200 lines). The file_write tool always shows the user a "
    "diff and asks for approval before anything is written to disk — never "
    "try to bypass that."
)


def build_system_prompt(context: ProjectContext, tool_names: list) -> str:
    parts = [BASE_SYSTEM_PROMPT, f"Available tools: {', '.join(tool_names)}."]

    if context.claude_md:
        parts.append("# Project instructions (CLAUDE.md)\n\n" + context.claude_md)

    for skill in context.skills:
        parts.append(f"# Skill: {skill.name}\n\n{skill.content}")

    return "\n\n".join(parts)
