import ast
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class CodeBlock:
    type: str
    start_line: int
    end_line: int
    content: str
    docstring: Optional[str] = None
    dependencies: List[str] = None


class DependencyVisitor(ast.NodeVisitor):
    """Collect imported names used inside a node"""

    def __init__(self, imports: Set[str]):
        self.imports = imports
        self.used: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        if node.id in self.imports:
            self.used.add(node.id)
        self.generic_visit(node)


class ASTAnalyzer:
    """Analyze Python source code into semantic chunks"""

    def parse_source(self, source: str) -> List[CodeBlock]:
        tree = ast.parse(source)
        lines = source.splitlines()
        blocks: List[CodeBlock] = []

        imports = self._collect_imports(tree)

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # print(f"lines:{lines}")
                blocks.append(self._make_block("import", node, lines))

            elif isinstance(node, ast.FunctionDef):
                blocks.append(self._make_block(
                    "function", node, lines, imports
                ))

            elif isinstance(node, ast.ClassDef):
                blocks.append(self._make_block(
                    "class", node, lines, imports
                ))

        return blocks

    def _collect_imports(self, tree: ast.AST) -> Set[str]:
        imported = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported.add(alias.asname or alias.name)

        return imported

    def _make_block(self,block_type: str,node: ast.AST,lines: List[str],imports: Optional[Set[str]] = None) -> CodeBlock:

        start = node.lineno
        end = getattr(node, "end_lineno", start)

        content = "\n".join(lines[start - 1:end])

        docstring = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)

        dependencies = []
        if imports:
            visitor = DependencyVisitor(imports)
            visitor.visit(node)
            dependencies = sorted(visitor.used)

        return CodeBlock(
            type=block_type,
            start_line=start,
            end_line=end,
            content=content,
            docstring=docstring,
            dependencies=dependencies
        )



# -------------------------
# Example usage
# -------------------------

SOURCE_CODE = """
import os
import math

def area(r):
    \"\"\"Compute circle area\"\"\"
    return math.pi * r * r

class Circle:
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r ** 2
"""

analyzer = ASTAnalyzer()
blocks = analyzer.parse_source(SOURCE_CODE)

for b in blocks:
    print("TYPE:", b.type)
    print("LINES:", b.start_line, "-", b.end_line)
    print("DOC:", b.docstring)
    print("DEPS:", b.dependencies)
    print("CONTENT:\n", b.content)
    print("-" * 40)
