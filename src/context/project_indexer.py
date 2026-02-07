"""
Project-wide AST scanner and dependency graph builder.

This module walks a Python project directory, parses each .py file,
extracts import statements and top-level definitions (functions, classes),
and builds a bidirectional dependency graph.

Key classes:
- FileInfo: Metadata for a single Python file
- ProjectGraph: The full dependency graph with forward and reverse edges
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional
from enum import Enum


class FileType(Enum):
    """Classification of Python files by their role."""
    MODULE = "module"          # Regular Python module
    SCRIPT = "script"          # Has __main__ block
    TEST = "test"              # Test file (test_*.py or *_test.py)
    CONFIG = "config"          # Config file (settings.py, config.py, etc.)
    INIT = "init"              # __init__.py


@dataclass
class FileInfo:
    """Metadata for a single Python file in the project."""
    filepath: str                          # Absolute path
    relative_path: str                     # Relative to project root
    imports: List[str] = field(default_factory=list)      # ['os', 'src.utils', 'json']
    exports: List[str] = field(default_factory=list)      # ['MyClass', 'helper_function']
    file_type: FileType = FileType.MODULE
    line_count: int = 0
    mtime: float = 0.0                     # Last modification timestamp


@dataclass
class ProjectGraph:
    """
    Dependency graph for the entire project.

    Attributes:
        files: Maps relative_path -> FileInfo
        dependencies: Maps file -> list of files it imports from
        reverse_dependencies: Maps file -> list of files that import it
    """
    files: Dict[str, FileInfo] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    reverse_dependencies: Dict[str, List[str]] = field(default_factory=dict)

    def add_file(self, file_info: FileInfo):
        """Add a file to the graph."""
        self.files[file_info.relative_path] = file_info

    def add_dependency(self, from_file: str, to_file: str):
        """Add a dependency edge: from_file imports to_file."""
        if from_file not in self.dependencies:
            self.dependencies[from_file] = []
        if to_file not in self.dependencies[from_file]:
            self.dependencies[from_file].append(to_file)

        # Add reverse edge
        if to_file not in self.reverse_dependencies:
            self.reverse_dependencies[to_file] = []
        if from_file not in self.reverse_dependencies[to_file]:
            self.reverse_dependencies[to_file].append(from_file)

    def get_dependencies(self, filepath: str) -> List[str]:
        """Get all files that this file imports from."""
        return self.dependencies.get(filepath, [])

    def get_dependents(self, filepath: str) -> List[str]:
        """Get all files that import this file."""
        return self.reverse_dependencies.get(filepath, [])


class ProjectIndexer:
    """
    Scans a Python project and builds a dependency graph.
    """

    def __init__(self, project_root: str, exclude_dirs: Optional[Set[str]] = None):
        """
        Initialize the indexer.

        Args:
            project_root: Absolute path to the project root
            exclude_dirs: Directory names to skip (e.g., {'venv', '__pycache__', '.git'})
        """
        self.project_root = Path(project_root).resolve()
        self.exclude_dirs = exclude_dirs or {
            'venv', 'env', '.venv', '__pycache__', '.git',
            'node_modules', '.pytest_cache', '.agentfs', 'vibe'
        }

    def scan_project(self) -> ProjectGraph:
        """
        Scan the entire project and build the dependency graph.

        Returns:
            ProjectGraph with all files and dependencies
        """
        graph = ProjectGraph()

        # Walk the project directory
        for py_file in self._find_python_files():
            file_info = self._analyze_file(py_file)
            if file_info:
                graph.add_file(file_info)

        # Build dependency edges
        self._build_dependency_edges(graph)

        return graph

    def _find_python_files(self) -> List[Path]:
        """
        Find all .py files in the project, excluding specified directories.

        Returns:
            List of Path objects for Python files
        """
        valid_python_files = []
        # TODO(human): Implement this function
        # Walk through self.project_root recursively
        # Skip directories in self.exclude_dirs
        # Collect all .py files
        # Return list of Path objects
        for path in self.project_root.rglob("*.py"):
            # validate if any excluded dir is there in current path
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            valid_python_files.append(path)

        return valid_python_files

    def _analyze_file(self, filepath: Path) -> Optional[FileInfo]:
        """
        Parse a single Python file and extract metadata.

        Args:
            filepath: Path to the .py file

        Returns:
            FileInfo object or None if parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse with AST
            tree = ast.parse(content, filename=str(filepath))

            # Get relative path
            relative_path = str(filepath.relative_to(self.project_root))

            # Extract imports
            imports = self._extract_imports(tree)

            # Extract exports (top-level functions and classes)
            exports = self._extract_exports(tree)

            # Classify file type
            file_type = self._classify_file(filepath, tree)

            # Count lines
            line_count = len(content.splitlines())

            # Get modification time
            mtime = filepath.stat().st_mtime

            return FileInfo(
                filepath=str(filepath),
                relative_path=relative_path,
                imports=imports,
                exports=exports,
                file_type=file_type,
                line_count=line_count,
                mtime=mtime
            )

        except Exception as e:
            print(f"Warning: Failed to parse {filepath}: {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """
        Extract all import statements from an AST.

        Args:
            tree: Parsed AST

        Returns:
            List of imported module names (e.g., ['os', 'src.utils', 'json'])
        """
        # TODO(human): Implement this function
        # Walk through the AST tree
        # Find ast.Import and ast.ImportFrom nodes
        # For Import: collect names[0].name from each alias
        # For ImportFrom: collect the module name
        # Return unique list of module names
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imports.add(node.module)

        return sorted(list(imports))



    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """
        Extract top-level definitions (functions, classes) from an AST.

        Args:
            tree: Parsed AST

        Returns:
            List of exported names (e.g., ['MyClass', 'helper_function'])
        """
        # TODO(human): Implement this function
        # Walk through tree.body (top-level statements only)
        # Find ast.FunctionDef and ast.ClassDef nodes
        # Collect their names
        # Filter out private names (starting with _)
        # Return list of public names

        exports = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    exports.add(node.name)

        return sorted(list(exports))

    def _classify_file(self, filepath: Path, tree: ast.AST) -> FileType:
        """
        Classify a Python file by its role.

        Args:
            filepath: Path to the file
            tree: Parsed AST

        Returns:
            FileType enum value
        """
        filename = filepath.name

        # Check common patterns
        if filename == '__init__.py':
            return FileType.INIT
        if filename.startswith('test_') or filename.endswith('_test.py'):
            return FileType.TEST
        if filename in ('config.py', 'settings.py', 'configuration.py'):
            return FileType.CONFIG

        # Check for __main__ block (indicates script)
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check if it's "if __name__ == '__main__':"
                if isinstance(node.test, ast.Compare):
                    if isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
                        return FileType.SCRIPT

        return FileType.MODULE

    def _build_dependency_edges(self, graph: ProjectGraph):
        """
        Build dependency edges by resolving import statements to actual files.

        This is the tricky part: convert "from src.utils import X" into
        an actual filepath in the project.

        Args:
            graph: ProjectGraph to populate with edges
        """
        for file_info in graph.files.values():
            for import_name in file_info.imports:
                resolved_path = self._resolve_import(import_name, graph)
                if resolved_path:
                    graph.add_dependency(file_info.relative_path, resolved_path)

    def _resolve_import(self, import_name: str, graph: ProjectGraph) -> Optional[str]:
        """
        Resolve an import string to a relative file path in the project.

        Args:
            import_name: e.g., 'src.utils' or 'os' (stdlib)
            graph: The graph (to check if file exists)

        Returns:
            Relative path (e.g., 'src/utils.py') or None if not found / is stdlib
        """
        # Ignore stdlib modules (heuristic: single-word imports like 'os', 'sys')
        if '.' not in import_name and import_name in {'os', 'sys', 'json', 'ast', 'pathlib',
                                                        'typing', 'dataclasses', 'enum', 'math',
                                                        'datetime', 'collections', 're'}:
            return None

        # Convert module path to file path (e.g., 'src.utils' -> 'src/utils.py')
        potential_paths = [
            import_name.replace('.', os.sep) + '.py',           # src/utils.py
            import_name.replace('.', os.sep) + '/__init__.py',  # src/utils/__init__.py
        ]

        for path in potential_paths:
            if path in graph.files:
                return path

        return None
