"""
Loads the Context piece of the agent architecture on startup: the project's
CLAUDE.md instructions file and any skills/*/SKILL.md files, folded into the
system prompt by vibecode.agent.system_prompt.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SkillInfo:
    name: str
    content: str


@dataclass
class ProjectContext:
    claude_md: Optional[str] = None
    skills: list = field(default_factory=list)


def _read_text(path: Path) -> str:
    # Force UTF-8 instead of the platform default (cp1252 on Windows),
    # which raises on bytes outside it; fall back to latin-1 (never raises).
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def load_project_context(project_root: Path) -> ProjectContext:
    claude_md_path = project_root / "CLAUDE.md"
    claude_md = _read_text(claude_md_path) if claude_md_path.exists() else None

    skills = []
    skills_dir = project_root / "skills"
    if skills_dir.exists():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            skills.append(SkillInfo(name=skill_md.parent.name, content=_read_text(skill_md)))

    return ProjectContext(claude_md=claude_md, skills=skills)
