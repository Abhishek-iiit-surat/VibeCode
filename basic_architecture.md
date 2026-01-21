I'll help you build a terminal-based coding assistant! Let me first explore the agentfs library to understand its capabilities, then suggest a solid architecture.

● Web Search("agentfs python library agentic filesystem 2026")
  ⎿  Did 1 search in 15s                                             


● Great! AgentFS provides perfect isolation for our coding assistant. Let me design a simple, achievable flow for your project.

  ★ Insight ─────────────────────────────────────
  AgentFS is ideal for coding assistants because it creates an isolated SQLite-backed filesystem - all LLM edits happen in a sandbox, and nothing touches your real files until you approve. This gives you safe diffs and rollback capabilities out of the box.
  ─────────────────────────────────────────────────

  Suggested Flow

  1. User Query → 2. LLM Plans → 3. Show Diff → 4. User Approves → 5. Apply Changes

  Terminal Input: "Add docstrings to utils.py"
             ↓
      [AgentFS mounts workspace]
             ↓
      [LLM reads file, makes edits in isolated FS]
             ↓
      [Show unified diff to user]
             ↓
      [User: 'y' to apply, 'n' to reject, 'e' to edit]
             ↓
      [If approved: copy from AgentFS to real filesystem]

  Project Structure

  vibe-code/
  ├── src/
  │   ├── __init__.py
  │   ├── main.py              # CLI entry point (argparse/click)
  │   ├── agent/
  │   │   ├── __init__.py
  │   │   ├── planner.py       # LLM interaction for planning edits
  │   │   ├── editor.py        # Apply edits via AgentFS
  │   │   └── prompts.py       # System prompts for LLM
  │   ├── diff/
  │   │   ├── __init__.py
  │   │   └── viewer.py        # Generate and display diffs
  │   ├── storage/
  │   │   ├── __init__.py
  │   │   └── agentfs_manager.py  # Wrap agentfs operations
  │   └── ui/
  │       ├── __init__.py
  │       └── terminal.py      # Rich/colorama for pretty output
  ├── tests/
  │   ├── __init__.py
  │   ├── test_editor.py
  │   └── test_diff.py
  ├── examples/
  │   └── sample_workspace/    # Test files for development
  ├── .env.example             # LLM API keys template
  ├── requirements.txt
  ├── setup.py
  └── README.md

  MVP Feature Set (v0.1)

  Core capabilities:
  - Single file editing only
  - Show unified diffs before applying
  - Simple approval workflow (y/n/e for edit)
  - Support OpenAI/Anthropic API

  What we'll skip initially:
  - Multi-file refactoring
  - Git integration
  - Conversation history
  - Streaming responses

  Proposed Tech Stack

  # requirements.txt
  agentfs>=0.1.0          # Filesystem isolation
  anthropic>=0.40.0       # Claude API (or openai)
  rich>=13.0.0            # Terminal UI
  click>=8.0.0            # CLI framework
  python-dotenv>=1.0.0    # Environment variables
  difflib                 # Built-in, for diffs

  Simple Usage Example

  # Start the assistant
  $ vibe-code

  # User queries
  > Add type hints to calculate_total function in utils.py
  > Refactor the parse_config function to use pathlib
  > Fix the bug in line 42 of main.py

  Would you like me to start building this? I suggest we begin with:

  1. Project structure setup - Create the directories and initial files
  2. AgentFS integration - Basic mount/unmount wrapper
  3. Simple LLM call - Get one edit working end-to-end
  4. Diff viewer - Show changes before applying

  Which component would you like to tackle first, or shall I set up the entire skeleton?

  Sources:
  - https://github.com/tursodatabase/agentfs
  - https://docs.turso.tech/agentfs/introduction
  - https://www.agentfs.ai/
  - https://turso.tech/blog/agentfs-fuse