"""
Context management layer for VibeCode.

This module handles intelligent context retrieval for large files and projects:
- AST-based code parsing and chunking
- Project-wide dependency tracking
- Semantic code search
"""

from .ast_analyzer import ASTAnalyzer, CodeBlock

__all__ = ['ASTAnalyzer', 'CodeBlock']
