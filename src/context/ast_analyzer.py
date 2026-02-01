"""
AST-based code analyzer for extracting semantic chunks from Python files.

This module parses Python files into structured CodeBlock objects representing
functions, classes, and other code units. This enables targeted editing of large
files by sending only relevant chunks to the LLM.
"""

import ast
from dataclasses import dataclass, field
from typing import List, Optional, Set
from pathlib import Path


@dataclass
class CodeBlock:
    """
    Represents a semantic unit of code (function, class, or module-level code).

    Attributes:
        type: Block type ('function', 'class', 'import', 'module_code')
        name: Name of the function/class (or 'imports' for import blocks)
        start_line: First line number (1-indexed)
        end_line: Last line number (inclusive)
        content: The actual source code for this block
        docstring: The docstring if present, None otherwise
        dependencies: Names of other functions/classes this block references
    """
    type: str
    name: str
    start_line: int
    end_line: int
    content: str
    docstring: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)


class ASTAnalyzer:
    """
    Parse Python files into semantic code blocks using AST analysis.

    This analyzer extracts functions, classes, and imports from Python files,
    making it possible to edit specific parts of large files without loading
    the entire file into LLM context.

    Example:
        analyzer = ASTAnalyzer()
        blocks = analyzer.parse_file("src/main.py")

        # Find a specific function
        target = next(b for b in blocks if b.name == "process_data")
        print(f"Function at lines {target.start_line}-{target.end_line}")
    """

    def __init__(self):
        self.source_lines = []  # Cache of file lines for extraction

    def parse_file(self, filepath: str) -> List[CodeBlock]:
        """
        Extract all functions, classes, and imports from a Python file.

        Args:
            filepath: Path to the Python file to analyze

        Returns:
            List of CodeBlock objects representing the file's structure

        Raises:
            FileNotFoundError: If filepath doesn't exist
            SyntaxError: If the Python file has syntax errors
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            self.source_lines = source.splitlines()

        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as e:
            raise SyntaxError(f"Failed to parse {filepath}: {e}")

        blocks = []

        # Extract imports first (usually at the top)
        imports = self._extract_imports(tree, source)
        if imports:
            blocks.append(imports)

        # Extract top-level functions and classes
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                blocks.append(self._extract_function(node, source))
            elif isinstance(node, ast.ClassDef):
                blocks.append(self._extract_class(node, source))

        return blocks

    def _extract_imports(self, tree: ast.AST, source: str) -> Optional[CodeBlock]:
        """
        Extract all import statements into a single CodeBlock.

        TODO(human): Implement this method to collect all Import and ImportFrom nodes

        Args:
            tree: The parsed AST of the file
            source: The original source code

        Returns:
            CodeBlock with type='import' containing all imports, or None if no imports

        Implementation guide:
        - Loop through tree.body to find ast.Import and ast.ImportFrom nodes
        - For each import node:
          * Use node.lineno to get the starting line number
          * Use ast.get_source_segment(source, node) to get the import statement text
        - Collect all import lines and combine them into a single content string
        - Find the min start_line and max end_line across all imports
        - Return a CodeBlock with type='import', name='imports', and all the import code
        """
        # TODO(human): Your implementation here
        import_nodes = []
        import_contents = []
        start_lines = []
        end_lines = []
        # Step 1: Find all import nodes in tree.body
        for node in tree.body:
            if isinstance(node,(ast.Import, ast.ImportFrom)):
                segment = ast.get_source_segment(source, node)
                if segment:
                    import_contents.append(segment)
                    start_lines.append(node.lineno)
                    end_lines.append(getattr(node, "end_lineno", node.lineno))


        if not import_contents:
            return None

        start_line = min(start_lines)
        end_line = max(end_lines)
        content = "\n".join(import_contents)

        return CodeBlock(
           type = "import",
           name = "imports",
           start_line = start_line,
           end_line  = end_line,
           content= content,
           docstring=None,
           dependencies=None, 
        )

    def _extract_function(self, node: ast.FunctionDef, source: str) -> CodeBlock:
        """
        Extract a function definition into a CodeBlock.

        Args:
            node: AST node representing a function
            source: Full source code of the file

        Returns:
            CodeBlock representing this function
        """
        # Get the source code for this function
        content = ast.get_source_segment(source, node)

        # Extract docstring if present
        docstring = ast.get_docstring(node)

        # Extract dependencies (functions/classes this function calls)
        dependencies = self._find_dependencies(node)

        return CodeBlock(
            type='function',
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno,
            content=content,
            docstring=docstring,
            dependencies=dependencies
        )

    def _extract_class(self, node: ast.ClassDef, source: str) -> CodeBlock:
        """
        Extract a class definition into a CodeBlock.

        Args:
            node: AST node representing a class
            source: Full source code of the file

        Returns:
            CodeBlock representing this class with all its methods
        """
        # Get the source code for this class
        content = ast.get_source_segment(source, node)

        # Extract docstring if present
        docstring = ast.get_docstring(node)

        # Extract dependencies
        dependencies = self._find_dependencies(node)

        return CodeBlock(
            type='class',
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno,
            content=content,
            docstring=docstring,
            dependencies=dependencies
        )

    def _find_dependencies(self, node: ast.AST) -> Set[str]:
        """
        Find all function/class names that this code block references.

        Args:
            node: AST node to analyze

        Returns:
            Set of names (as strings) that this block depends on
        """
        dependencies = set()

        for child in ast.walk(node):
            # Find function calls
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    # For calls like obj.method(), we want 'method'
                    dependencies.add(child.func.attr)

        return dependencies

    def find_relevant_blocks(self, blocks: List[CodeBlock], query: str) -> List[CodeBlock]:
        """
        Find code blocks relevant to a user's query.

        This uses simple keyword matching for now. Future versions could use
        embeddings or more sophisticated NLP.

        Args:
            blocks: List of CodeBlock objects to search through
            query: User's edit request (e.g., "add error handling to process_data")

        Returns:
            List of relevant CodeBlock objects, ordered by relevance

        Example:
            >>> blocks = analyzer.parse_file("src/main.py")
            >>> relevant = analyzer.find_relevant_blocks(blocks, "fix the login function")
            >>> # Returns [CodeBlock(name='login', ...), CodeBlock(name='authenticate', ...)]
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_blocks = []

        for block in blocks:
            score = 0

            # Exact name match (highest priority)
            if block.name.lower() in query_lower:
                score += 10

            # Partial name match
            for word in query_words:
                if word in block.name.lower():
                    score += 5

            # Keyword in docstring
            if block.docstring and any(word in block.docstring.lower() for word in query_words):
                score += 2

            # Keyword in content
            content_lower = block.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1

            if score > 0:
                scored_blocks.append((score, block))

        # Sort by score (descending)
        scored_blocks.sort(key=lambda x: x[0], reverse=True)

        return [block for score, block in scored_blocks]

    def get_context_for_block(self, blocks: List[CodeBlock], target_block: CodeBlock,
                              max_blocks: int = 5) -> List[CodeBlock]:
        """
        Get relevant context blocks for editing a target block.

        This includes:
        - The target block itself
        - Imports (always needed)
        - Functions/classes that the target depends on
        - Functions/classes that depend on the target

        Args:
            blocks: All blocks from the file
            target_block: The block being edited
            max_blocks: Maximum number of context blocks to return

        Returns:
            List of CodeBlock objects needed for context
        """
        context = []

        # Always include imports
        import_block = next((b for b in blocks if b.type == 'import'), None)
        if import_block:
            context.append(import_block)

        # Include the target block
        context.append(target_block)

        # Include blocks that target depends on
        for dep_name in target_block.dependencies:
            dep_block = next((b for b in blocks if b.name == dep_name), None)
            if dep_block and dep_block not in context:
                context.append(dep_block)
                if len(context) >= max_blocks:
                    break

        return context
