"""
Context management layer for VibeCode.

This module handles intelligent context retrieval for large files and projects:
- AST-based code parsing and chunking
- Project-wide dependency tracking
- Semantic code search (find_relevant_files in FileFinder is not yet implemented)

Also loads the Context piece of the agent architecture — CLAUDE.md and
skills/ — on startup; see loader.py.
"""

from vibecode.context.ast_analyzer import ASTAnalyzer, CodeBlock
from vibecode.context.project_indexer import ProjectIndexer, ProjectGraph, FileInfo, FileType
from vibecode.context.project_db import ProjectDatabase, incremental_index
from vibecode.context.file_finder import FileFinder
from vibecode.context.loader import ProjectContext, SkillInfo, load_project_context

__all__ = [
    'ASTAnalyzer', 'CodeBlock',
    'ProjectIndexer', 'ProjectGraph', 'FileInfo', 'FileType',
    'ProjectDatabase', 'incremental_index',
    'FileFinder',
    'ProjectContext', 'SkillInfo', 'load_project_context',
]
