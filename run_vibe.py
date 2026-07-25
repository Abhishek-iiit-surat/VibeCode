#!/usr/bin/env python3
"""
VibeCode - an agentic coding assistant

This is the entry point script that properly sets up paths and runs the CLI.

Usage:
  python run_vibe.py "add a docstring to utils.py"    # Single task
  python run_vibe.py                                   # Interactive REPL
"""

import sys
from pathlib import Path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from vibecode.cli import cli

if __name__ == '__main__':
    cli()
