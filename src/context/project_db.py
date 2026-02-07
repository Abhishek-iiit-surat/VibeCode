"""
SQLite-based persistence for ProjectGraph.

Stores file metadata and dependency edges in a local database (.vibe/project.db)
to avoid re-scanning the entire project on every run. Only re-indexes files
that have changed (by comparing mtime).

Tables:
- files: filepath, imports (JSON), exports (JSON), file_type, line_count, mtime
- dependencies: source_file, target_file

Key methods:
- save_graph(): Persist a ProjectGraph to SQLite
- load_graph(): Load a ProjectGraph from SQLite
- needs_update(): Check if a file needs re-indexing (mtime changed)
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Set

from .project_indexer import ProjectGraph, FileInfo, FileType


class ProjectDatabase:
    """
    SQLite wrapper for persisting ProjectGraph data.
    """

    def __init__(self, db_path: str):
        """
        Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file (e.g., '.vibe/project.db')
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._create_tables()

    def _create_tables(self):
        """
        Create the database schema if it doesn't exist.

        Tables:
        - files: Stores FileInfo metadata
        - dependencies: Stores dependency edges
        """
        cursor = self.conn.cursor()

        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                filepath TEXT PRIMARY KEY,
                relative_path TEXT NOT NULL,
                imports TEXT NOT NULL,
                exports TEXT NOT NULL,
                file_type TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                mtime REAL NOT NULL
            )
        """)

        # Dependencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                source_file TEXT NOT NULL,
                target_file TEXT NOT NULL,
                PRIMARY KEY (source_file, target_file)
            )
        """)

        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dependencies_source
            ON dependencies(source_file)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dependencies_target
            ON dependencies(target_file)
        """)

        self.conn.commit()

    def save_graph(self, graph: ProjectGraph):
        """
        Save a ProjectGraph to the database.

        This will:
        1. Clear existing data
        2. Insert all files from graph.files
        3. Insert all edges from graph.dependencies

        Args:
            graph: The ProjectGraph to persist
        """
        # TODO(human): Implement this function
        # 1. Get a cursor: cursor = self.conn.cursor()
        # 2. Clear old data: cursor.execute("DELETE FROM files") and same for dependencies
        # 3. For each file_info in graph.files.values():
        #    - Convert imports and exports lists to JSON strings using json.dumps()
        #    - INSERT INTO files with all fields
        # 4. For source_file, targets in graph.dependencies.items():
        #    - For each target in targets:
        #      - INSERT INTO dependencies (source_file, target_file)
        # 5. Commit: self.conn.commit()
        cursor =self.conn.cursor()
        # delete old data from files table
        cursor.execute("DELETE FROM files")
        cursor.execute("DELETE FROM dependencies")

        # save new project graph and dependency graph

        for file_info in graph.files.values():
            cursor.execute("""
            INSERT INTO files VALUES (?,?,?,?,?,?,?)
        """, (
            file_info.filepath,
            file_info.relative_path,
            json.dumps(file_info.imports),
            json.dumps(file_info.exports),
            file_info.file_type.value,
            file_info.line_count,
            file_info.mtime
        ))
        
        # save new dependencies

        for source_file, targets in graph.dependencies.items():
            for target in targets:
                cursor.execute("""
                INSERT INTO dependencies VALUES(?,?)
                """, (source_file, target))

        self.conn.commit()

    def load_graph(self) -> ProjectGraph:
        """
        Load a ProjectGraph from the database.

        Returns:
            ProjectGraph reconstructed from the database
        """
        # TODO(human): Implement this function
        # 1. Create empty graph: graph = ProjectGraph()
        # 2. Load files: cursor.execute("SELECT * FROM files")
        # 3. For each row:
        #    - Parse imports and exports from JSON: json.loads(row['imports'])
        #    - Convert file_type string to FileType enum: FileType(row['file_type'])
        #    - Create FileInfo object
        #    - Add to graph: graph.add_file(file_info)
        # 4. Load dependencies: cursor.execute("SELECT * FROM dependencies")
        # 5. For each row:
        #    - Call graph.add_dependency(row['source_file'], row['target_file'])
        # 6. Return graph
        graph = ProjectGraph()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files")
        for row in cursor.fetchall():
            file_info = FileInfo(
                filepath=row['filepath'],
                relative_path=row['relative_path'],
                imports=json.loads(row['imports']),
                exports=json.loads(row['exports']),
                file_type=FileType(row['file_type']),
                line_count=row['line_count'],
                mtime=row['mtime']
            )
            graph.add_file(file_info)

        # Load dependencies
        cursor.execute("SELECT * FROM dependencies")
        for row in cursor.fetchall():
            graph.add_dependency(row['source_file'], row['target_file'])

        return graph 

    def get_stored_mtime(self, relative_path: str) -> Optional[float]:
        """
        Get the stored modification time for a file.

        Args:
            relative_path: Relative path to the file

        Returns:
            Stored mtime or None if file not in database
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT mtime FROM files WHERE relative_path = ?",
            (relative_path,)
        )
        row = cursor.fetchone()
        return row['mtime'] if row else None

    def needs_update(self, file_info: FileInfo) -> bool:
        """
        Check if a file needs to be re-indexed.

        Compares the file's current mtime with the stored mtime.

        Args:
            file_info: FileInfo with current mtime

        Returns:
            True if file is new or has been modified since last index
        """
        stored_mtime = self.get_stored_mtime(file_info.relative_path)
        if stored_mtime is None:
            return True  # New file
        return file_info.mtime > stored_mtime

    def get_all_files(self) -> Set[str]:
        """
        Get all relative paths stored in the database.

        Returns:
            Set of relative file paths
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT relative_path FROM files")
        return {row['relative_path'] for row in cursor.fetchall()}

    def remove_files(self, relative_paths: Set[str]):
        """
        Remove files from the database.

        Used when files have been deleted from the project.

        Args:
            relative_paths: Set of relative paths to remove
        """
        if not relative_paths:
            return

        cursor = self.conn.cursor()

        # Remove from files table
        placeholders = ','.join('?' * len(relative_paths))
        cursor.execute(
            f"DELETE FROM files WHERE relative_path IN ({placeholders})",
            tuple(relative_paths)
        )

        # Remove from dependencies table (both as source and target)
        cursor.execute(
            f"DELETE FROM dependencies WHERE source_file IN ({placeholders})",
            tuple(relative_paths)
        )
        cursor.execute(
            f"DELETE FROM dependencies WHERE target_file IN ({placeholders})",
            tuple(relative_paths)
        )

        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()


def incremental_index(project_root: str, db_path: str = ".vibe/project.db") -> ProjectGraph:
    """
    Perform incremental indexing: only re-scan changed files.

    This is the main entry point for efficient project indexing.

    Args:
        project_root: Absolute path to project root
        db_path: Path to SQLite database (relative to project root)

    Returns:
        Updated ProjectGraph
    """
    from .project_indexer import ProjectIndexer

    db_full_path = Path(project_root) / db_path

    with ProjectDatabase(str(db_full_path)) as db:
        indexer = ProjectIndexer(project_root)

        # If database is empty, do full scan
        stored_files = db.get_all_files()
        if not stored_files:
            print("First run: performing full project scan...")
            graph = indexer.scan_project()
            db.save_graph(graph)
            print(f"Indexed {len(graph.files)} files.")
            return graph

        # Load existing graph
        graph = db.load_graph()
        print(f"Loaded {len(graph.files)} files from cache.")

        # Find current files
        current_files = {
            str(Path(f.filepath).relative_to(project_root))
            for f in [indexer._analyze_file(p) for p in indexer._find_python_files()]
            if f is not None
        }

        # Detect deleted files
        deleted = stored_files - current_files
        if deleted:
            print(f"Removing {len(deleted)} deleted files...")
            db.remove_files(deleted)
            for rel_path in deleted:
                graph.files.pop(rel_path, None)

        # Detect new or modified files
        modified_count = 0
        for py_file in indexer._find_python_files():
            file_info = indexer._analyze_file(py_file)
            if file_info and db.needs_update(file_info):
                graph.add_file(file_info)
                modified_count += 1

        if modified_count > 0:
            print(f"Re-indexed {modified_count} modified files.")
            # Rebuild all dependency edges (since changes can affect the graph)
            graph.dependencies.clear()
            graph.reverse_dependencies.clear()
            indexer._build_dependency_edges(graph)
            db.save_graph(graph)
        else:
            print("No changes detected.")

        return graph
