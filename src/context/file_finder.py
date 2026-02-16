"""
Intelligent file finder using the project graph.

When users don't specify a filepath, this module searches the project
to find the most relevant files based on their query.

Strategies:
1. Keyword matching against file exports (function/class names)
2. Keyword matching against file paths
3. Keyword matching against imports (find where something is used)
4. Multi-keyword extraction (splits queries into meaningful tokens)
5. Confidence-based autonomous decision making
"""

from typing import List, Tuple, Optional, Dict
from pathlib import Path
from .project_indexer import ProjectGraph, FileInfo
import re


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

        # Confidence thresholds for autonomous decisions
        self.HIGH_CONFIDENCE_THRESHOLD = 15  # Auto-select if top score >= this
        self.CONFIDENCE_GAP_RATIO = 2.0      # Auto-select if top_score / second_score >= this

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
        # 1. Extract keywords from query using _extract_keywords(query)
        # 2. Convert query to lowercase for case-insensitive matching
        # 3. Create a list to store (filepath, score, reason) for each file
        # 4. For each file_info in self.graph.files.values():
        #    - Calculate a relevance score using _score_file(file_info, query_lower, keywords)
        #    - If score > 0, add (file_info.filepath, score, reason) to results
        # 5. Sort results by score (descending)
        # 6. Return top_k results
        #
        # Enhanced Scoring strategy (multi-keyword aware):
        # - Exact export match: +15 points (boosted from 10)
        # - Partial export match: +7 points (boosted from 5)
        # - Exact filename match: +10 points (new)
        # - Partial filename match: +5 points (boosted from 3)
        # - Path directory match: +4 points (boosted from 2)
        # - Import match: +2 points (boosted from 1)
        # - Multi-keyword bonus: +3 per additional keyword match

        # Step 1: Extract keywords
        keywords = self._extract_keywords(query)

        # Step 2: Convert query to lowercase
        query_lower = query.lower()

        # Step 3: Create results list
        results = []

        # Step 4: Score each file
        for file_info in self.graph.files.values():
            score, reason = self._score_file(file_info, query_lower, keywords)
            if score > 0:
                results.append((file_info.filepath, score, reason))

        # Step 5: Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        # Step 6: Return top_k results
        return results[:top_k]

    def _score_file(self, file_info: FileInfo, query: str, keywords: List[str]) -> Tuple[float, str]:
        """
        Score a single file's relevance to the query using enhanced multi-keyword matching.

        Args:
            file_info: The file to score
            query: Lowercase search query (full query string)
            keywords: Extracted keywords from the query

        Returns:
            (score, reason) tuple - score is 0 if not relevant
        """
        # TODO(human): Implement this function with enhanced scoring
        # 1. Initialize score = 0 and reasons = []
        # 2. Get filename stem: filename = Path(file_info.relative_path).stem
        #
        # 3. Check exports for matches (HIGHEST PRIORITY):
        #    - For each export in file_info.exports:
        #      - If query == export.lower(): score += 15, reasons.append(f"Exact export: {export}")
        #      - Elif any keyword in export.lower() for keyword in keywords:
        #           score += 7, reasons.append(f"Partial export: {export}")
        #
        # 4. Check filename matches:
        #    - If query == filename.lower(): score += 10, reasons.append(f"Exact filename: {filename}")
        #    - Elif query in filename.lower(): score += 5, reasons.append(f"Filename contains: {filename}")
        #    - Elif any keyword in filename.lower() for keyword in keywords:
        #           score += 3, reasons.append(f"Filename keyword: {filename}")
        #
        # 5. Check path components (e.g., "auth" in "src/auth/handler.py"):
        #    - path_parts = Path(file_info.relative_path).parts[:-1]  # exclude filename
        #    - For each keyword in keywords:
        #        - If keyword in any path_part.lower(): score += 4, reasons.append(f"Path: {keyword}")
        #
        # 6. Check imports (where this module is used):
        #    - For each imp in file_info.imports:
        #      - If any keyword in imp.lower() for keyword in keywords:
        #           score += 2, reasons.append(f"Imports: {imp}")
        #
        # 7. Multi-keyword bonus (rewards files matching multiple keywords):
        #    - matched_keywords = count of unique keywords found across all checks
        #    - If matched_keywords >= 2: score += (matched_keywords - 1) * 3
        #      reasons.append(f"Multi-match: {matched_keywords} keywords")
        #
        # 8. Return (score, " | ".join(reasons))
        score = 0
        reasons = []
        matched_keywords = set()  # Track unique keywords that matched

        filename = Path(file_info.relative_path).stem

        # Check exports (highest priority)
        for export in file_info.exports:
            if query == export.lower():
                score += 15
                reasons.append(f"Exact export: {export}")
                matched_keywords.update(keywords)  # All keywords contributed to this match
            else:
                for keyword in keywords:
                    if keyword in export.lower():
                        score += 7
                        reasons.append(f"Partial export: {export}")
                        matched_keywords.add(keyword)
                        break  # Only count once per export

        # Check filename
        if query == filename.lower():
            score += 10
            reasons.append(f"Exact filename: {filename}")
            matched_keywords.update(keywords)
        elif query in filename.lower():
            score += 5
            reasons.append(f"Filename contains: {filename}")
            matched_keywords.update(keywords)
        else:
            for keyword in keywords:
                if keyword in filename.lower():
                    score += 3
                    reasons.append(f"Filename keyword: {filename}")
                    matched_keywords.add(keyword)
                    break  # Only count once

        # Check path components
        path_parts = Path(file_info.relative_path).parts[:-1]  # Exclude filename
        for keyword in keywords:
            for part in path_parts:
                if keyword in part.lower():
                    score += 4
                    reasons.append(f"Path: {keyword}")
                    matched_keywords.add(keyword)
                    break  # Only count once per keyword

        # Check imports
        for imp in file_info.imports:
            for keyword in keywords:
                if keyword in imp.lower():
                    score += 2
                    reasons.append(f"Imports: {imp}")
                    matched_keywords.add(keyword)
                    break  # Only count once per import

        # Multi-keyword bonus
        if len(matched_keywords) >= 2:
            bonus = (len(matched_keywords) - 1) * 3
            score += bonus
            reasons.append(f"Multi-match: {len(matched_keywords)} keywords")

        return (score, " | ".join(reasons))

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from a user query.

        This helper method processes natural language queries and extracts
        the important keywords for matching against the codebase.

        Examples:
            "fix authentication bug" -> ["fix", "authentication", "bug"]
            "add error handling to parser" -> ["add", "error", "handling", "parser"]
            "calculateTotalPrice function" -> ["calculate", "total", "price", "function"]
            "update_user_profile method" -> ["update", "user", "profile", "method"]

        Args:
            query: User's natural language query

        Returns:
            List of lowercase keywords (stop words removed)
        """
        # TODO(human): Implement keyword extraction
        #
        # STEP 1: Handle camelCase
        #   - Use regex to split camelCase: "calculateTotal" -> "calculate Total"
        #   - Pattern: re.sub(r'([a-z])([A-Z])', r'\1 \2', query)
        #   - This finds lowercase letter followed by uppercase and adds space between
        #
        # STEP 2: Handle snake_case
        #   - Replace underscores with spaces: "calculate_total" -> "calculate total"
        #   - Simple: query = query.replace('_', ' ')
        #
        # STEP 3: Remove common stop words
        #   - Define stop words set: {'the', 'a', 'an', 'to', 'in', 'on', 'for', 'with', 'at', 'from', 'by', 'of', 'and', 'or'}
        #   - Split query into words: words = query.lower().split()
        #   - Filter: keywords = [w for w in words if w not in stop_words and len(w) > 1]
        #
        # STEP 4: Return the filtered keywords list
        #   - Return keywords

        stop_words = {'the', 'a', 'an', 'to', 'in', 'on', 'for', 'with', 'at', 'from', 'by', 'of', 'and', 'or'}

        # Step 1: Split camelCase
        query_filter1 = re.sub(r'([a-z])([A-Z])', r'\1 \2', query)

        # Step 2: Split snake_case
        query_filter2 = query_filter1.replace("_", " ")

        # Step 3: Remove stop words and filter
        query_filter2_list = query_filter2.lower().split()  # Fixed: added () to lower
        keywords = [w for w in query_filter2_list if w not in stop_words and len(w) > 1]

        return keywords

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
