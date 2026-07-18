"""
Context management layer for VibeCode.

Loads the Context piece of the agent architecture — CLAUDE.md and skills/ —
on startup; see loader.py.
"""

from vibecode.context.loader import ProjectContext, SkillInfo, load_project_context

__all__ = [
    'ProjectContext', 'SkillInfo', 'load_project_context',
]
