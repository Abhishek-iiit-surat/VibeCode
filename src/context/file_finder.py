"""
Intelligent file finder using the project graph.

When users don't specify a filepath, this module searches the project
to find the most relevant files based on their query.

Strategies:
1. Keyword matching against file exports (function/class names)
2. Keyword matching against file paths
3. Keyword matching against imports (find where something is used)
"""

from typing import List, Tuple, Optional
from pathlib import Path
from .project_indexer import ProjectGraph, FileInfo


class FileFinder:
    """
    Searches the project graph to find relevant files for a query.
    """

    def __init__(self, graph: ProjectGraph, project_root: str):
        """
        Initialize the file finder.

        Args:
            graph: The project dependency graph
            project_root: Absolute path to project root
        """
        self.graph = graph
        self.project_root = Path(project_root)

    def find_relevant_files(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Find the most relevant files for a user query.

        Args:
            query: User's search query (e.g., "authentication", "parse json", "calculate tax")
            top_k: Number of results to return

        Returns:
            List of (filepath, score, reason) tuples, sorted by relevance
        """
        # TODO(human): Implement this function
        # 1. Convert query to lowercase for case-insensitive matching
        # 2. Create a list to store (filepath, score, reason) for each file
        # 3. For each file_info in self.graph.files.values():
        #    - Calculate a relevance score using _score_file(file_info, query_lower)
        #    - If score > 0, add (file_info.filepath, score, reason) to results
        # 4. Sort results by score (descending)
        # 5. Return top_k results
        #
        # Scoring strategy:
        # - Exact match in export name: +10 points
        # - Partial match in export name: +5 points
        # - Match in filename: +3 points
        # - Match in relative path: +2 points
        # - Match in imports: +1 point
        pass

    def _score_file(self, file_info: FileInfo, query: str) -> Tuple[float, str]:
        """
        Score a single file's relevance to the query.

        Args:
            file_info: The file to score
            query: Lowercase search query

        Returns:
            (score, reason) tuple - score is 0 if not relevant
        """
        # TODO(human): Implement this function
        # 1. Initialize score = 0 and reasons = []
        # 2. Check exports for matches:
        #    - For each export in file_info.exports:
        #      - If query == export.lower(): score += 10, reasons.append(f"Exact match: {export}")
        #      - Elif query in export.lower(): score += 5, reasons.append(f"Partial match: {export}")
        # 3. Check filename:
        #    - filename = Path(file_info.relative_path).stem  (e.g., "utils" from "src/utils.py")
        #    - If query in filename.lower(): score += 3, reasons.append(f"Filename match")
        # 4. Check path:
        #    - If query in file_info.relative_path.lower(): score += 2, reasons.append(f"Path match")
        # 5. Check imports (find where this module is used):
        #    - For each import in file_info.imports:
        #      - If query in import.lower(): score += 1, reasons.append(f"Imports: {import}")
        # 6. Return (score, ", ".join(reasons))
        pass

    def find_by_export(self, export_name: str) -> Optional[str]:
        """
        Find a file that exports a specific function or class.

        Args:
            export_name: Name of the function/class to find

        Returns:
            Filepath or None if not found
        """
        export_lower = export_name.lower()
        for file_info in self.graph.files.values():
            for export in file_info.exports:
                if export.lower() == export_lower:
                    return file_info.filepath
        return None

    def find_files_importing(self, module_name: str) -> List[str]:
        """
        Find all files that import a specific module.

        Args:
            module_name: Module name (e.g., "src.utils", "os")

        Returns:
            List of filepaths
        """
        results = []
        for file_info in self.graph.files.values():
            if module_name in file_info.imports:
                results.append(file_info.filepath)
        return results

    def suggest_context_files(self, target_file: str) -> List[str]:
        """
        Suggest additional files that might be relevant context for editing a file.

        Returns:
        - Files that the target imports from (dependencies)
        - Files that import the target (reverse dependencies)

        Args:
            target_file: Relative path of the file being edited

        Returns:
            List of filepath suggestions
        """
        suggestions = []

        # Add dependencies (files this imports from)
        deps = self.graph.get_dependencies(target_file)
        suggestions.extend(deps)

        # Add reverse dependencies (files that import this)
        reverse_deps = self.graph.get_dependents(target_file)
        suggestions.extend(reverse_deps)

        # Remove duplicates and return
        return list(set(suggestions))
