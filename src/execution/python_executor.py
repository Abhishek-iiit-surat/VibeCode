# Execution module to run Python scripts and capture output

import subprocess
import os
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Result from executing a Python script"""
    stdout: str
    stderr: str
    exit_code: int
    success: bool

    def __init__(self, stdout, stderr, exit_code):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.success = True if exit_code == 0 else False

@dataclass
class CompilationResult:
    """Result from compiling a Python script"""
    exit_code: int
    stderr: str
    success: bool

    def __init__(self, returncode: int = 1, error_message: str = ""):
        self.exit_code = returncode
        self.stderr = error_message if error_message else "Compilation failed" if returncode != 0 else ""
        self.success = True if returncode == 0 else False


class PythonExecutor:
    """Executes Python scripts and captures their output"""

    def run_script(self, file_path: str, timeout: int = 120) -> ExecutionResult:
        """
        Run a Python script and capture stdout, stderr, and exit code.

        Args:
            file_path (str): Path to the Python file to execute
            timeout (int): Maximum time in seconds for script execution (default: 120)

        Returns:
            ExecutionResult: Object containing stdout, stderr, exit_code, and success flag
        """
        try:
            result = subprocess.run(
                ['python3', file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return ExecutionResult(result.stdout, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            return ExecutionResult("", "Timeout: Script took too long", -1)

        except Exception as e:
            file_name = os.path.basename(file_path)
            print(f"Exception occurred during running file {file_name}\nError: {str(e)}")
            return ExecutionResult("", f"Error occurred: {str(e)}", -1)

    def compile_script(self, file_path: str) -> CompilationResult:
        """
        Compile a Python script to check for syntax errors.

        Args:
            file_path (str): Path to the Python file to compile

        Returns:
            CompilationResult: Object containing exit code, error message, and success flag
        """
        try:
            result = subprocess.run(
                ['python3', "-m", "py_compile", file_path],
                capture_output=True,
                text=True
            )
            # If compilation failed, stderr contains the error message
            error_msg = result.stderr if result.returncode != 0 else ""
            return CompilationResult(result.returncode, error_msg)

        except Exception as e:
            file_name = os.path.basename(file_path)
            error_msg = f"Exception during compilation of {file_name}: {str(e)}"
            print(f"Error: {error_msg}")
            return CompilationResult(-1, error_msg)
