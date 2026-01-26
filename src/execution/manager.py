"""
Execution manager that orchestrates code execution.
Routes execution requests to appropriate executors based on file type.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from python_executor import PythonExecutor, ExecutionResult, CompilationResult

def execute_code(file_path: str) -> ExecutionResult:
    """
    Execute a Python script and capture results.

    Args:
        file_path (str): Path to the Python file to execute

    Returns:
        ExecutionResult: Contains stdout, stderr, exit_code, and success flag
    """
    executor = PythonExecutor()
    return executor.run_script(file_path)

def compile_script(file_path: str) -> CompilationResult:
    """
    Compile a Python script to check for syntax errors.

    Args:
        file_path (str): Path to the Python file to compile

    Returns:
        CompilationResult: Contains success flag
    """
    executor = PythonExecutor()
    return executor.compile_script(file_path)

def format_execution_for_llm(result: ExecutionResult) -> str:
    """
    Format execution results in a human-readable way for LLM to understand.

    Args:
        result (ExecutionResult): The execution result to format

    Returns:
        str: Formatted message describing the execution result
    """
    if result.exit_code == 0:
        return f"✅ Code executed successfully!\nOutput:\n{result.stdout}"
    else:
        return f"❌ Script failed with exit code {result.exit_code}\nError:\n{result.stderr}"
