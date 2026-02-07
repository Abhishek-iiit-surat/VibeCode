#!/usr/bin/env python3
"""
Quick test script for ProjectIndexer.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.context import ProjectIndexer

def main():
    project_root = Path(__file__).parent
    print(f"Scanning project: {project_root}")

    indexer = ProjectIndexer(str(project_root))
    graph = indexer.scan_project()

    print(f"\n✅ Found {len(graph.files)} Python files\n")

    # Show a few examples
    print("=" * 60)
    print("Sample files:")
    print("=" * 60)

    for i, (rel_path, file_info) in enumerate(sorted(graph.files.items())[:5]):
        print(f"\n{i+1}. {rel_path}")
        print(f"   Type: {file_info.file_type.value}")
        print(f"   Lines: {file_info.line_count}")
        print(f"   Imports: {file_info.imports[:3]}{'...' if len(file_info.imports) > 3 else ''}")
        print(f"   Exports: {file_info.exports[:3]}{'...' if len(file_info.exports) > 3 else ''}")

    # Show dependency stats
    print("\n" + "=" * 60)
    print("Dependency Statistics:")
    print("=" * 60)

    files_with_deps = sum(1 for deps in graph.dependencies.values() if deps)
    total_edges = sum(len(deps) for deps in graph.dependencies.values())

    print(f"Files with dependencies: {files_with_deps}")
    print(f"Total dependency edges: {total_edges}")

    # Show most connected files
    print("\n" + "=" * 60)
    print("Most connected files (by incoming dependencies):")
    print("=" * 60)

    by_dependents = sorted(
        graph.reverse_dependencies.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:5]

    for filepath, dependents in by_dependents:
        print(f"\n{filepath}")
        print(f"   Used by {len(dependents)} files: {dependents[:2]}{'...' if len(dependents) > 2 else ''}")

    print("\n" + "=" * 60)
    print("✅ Project indexing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
