#!/usr/bin/env python3
"""
VibeCode - AI-powered code editor with automatic feedback loop

This is the entry point script that properly sets up paths and runs the CLI.

Usage:
  python run_vibe.py "Add docstrings" src/utils.py    # Single edit
  python run_vibe.py                                   # Interactive session
"""

import sys
from pathlib import Path

# Get the src directory path
src_dir = Path(__file__).parent / "src"

# Add src to Python path
sys.path.insert(0, str(src_dir))

# Import and run the CLI
from main import main

if __name__ == '__main__':
    main()
