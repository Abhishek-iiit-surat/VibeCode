"""
Context management layer for VibeCode.

This module handles intelligent context retrieval for large files and projects:
- AST-based code parsing and chunking
- Project-wide dependency tracking
- Semantic code search
"""

from .ast_analyzer import ASTAnalyzer, CodeBlock
from .project_indexer import ProjectIndexer, ProjectGraph, FileInfo, FileType
from .project_db import ProjectDatabase, incremental_index
from .file_finder import FileFinder
from .query_processor import QueryProcessor

__all__ = [
    'ASTAnalyzer', 'CodeBlock',
    'ProjectIndexer', 'ProjectGraph', 'FileInfo', 'FileType',
    'ProjectDatabase', 'incremental_index',
    'FileFinder', 'QueryProcessor'
]
