# VibeCode Usage Guide

VibeCode is an AI-powered code editor that uses LLM feedback loops to fix and improve your code automatically.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Two Usage Modes

### Mode 1: Single Edit (Quick Mode)

For quick, one-off edits:

```bash
python src/main.py "Add error handling" src/utils.py
```

**What happens:**
1. ✅ AgentFS sandbox initializes
2. 🔄 LLM edits the file (up to 5 iterations with feedback)
3. 📝 Shows diff and asks for approval
4. ✨ Applies changes (if approved)
5. 🧹 Cleans up and exits

**Best for:** Single file modifications

---

### Mode 2: Interactive Session (Full Session)

For working on multiple files:

```bash
python src/main.py
```

**What happens:**
1. ✅ AgentFS sandbox initializes ONCE for the entire session
2. 📝 Prompts: "Enter prompt (or 'quit'/'exit' to exit)"
3. 📁 Prompts: "Enter filepath"
4. 🔄 LLM edits the file (up to 5 iterations)
5. 📝 Shows diff and asks for approval
6. ✨ Applies changes (if approved)
7. ❓ Asks: "Would you like to edit another file?"
8. 🔄 Repeat steps 2-7 OR exit
9. 🧹 Cleans up sandbox and exits

**Best for:** Editing multiple files in one session

---

## Interactive Session Example

```
🤖 VibeCode Interactive Session Mode
💡 Tip: Type 'quit' or press CTRL+C to exit

============================================================
📝 Enter prompt (or 'quit'/'exit' to exit): Add error handling to file
📁 Enter filepath: src/main.py

🔄 Running code through AI feedback loop...

============================================================
ITERATION SUMMARY
============================================================
  Attempt 1: ❌ (exit code: 1)
  Attempt 2: ✅ (exit code: 0)
============================================================

📝 Here's what will change:

--- src/main.py (original)
+++ src/main.py (edited)
@@ -1,5 +1,10 @@
+try:
     def process_data(x):
         return x * 2
+except Exception as e:
+    print(f"Error: {e}")

✅ Iteration 2: Success!
Output:
Process data result: 42

============================================================
Apply changes? (y)es / (n)o / (e)dit: y

⏳ Applying changes to real file...

✨ Changes applied successfully!

Would you like to edit another file? [y/N]: y

============================================================
📝 Enter prompt (or 'quit'/'exit' to exit): Fix imports
📁 Enter filepath: src/config.py

🔄 Running code through AI feedback loop...

[... Same process for second file ...]

Would you like to edit another file? [y/N]: n

👋 Ending interactive session...

⏳ Cleaning up sandbox...
✅ Session ended gracefully
```

---

## Exit Commands

You can exit an interactive session in three ways:

### Option 1: Type 'quit'
```
📝 Enter prompt (or 'quit'/'exit' to exit): quit
👋 Ending interactive session...
```

### Option 2: Type 'exit'
```
📝 Enter prompt (or 'quit'/'exit' to exit): exit
👋 Ending interactive session...
```

### Option 3: Press CTRL+C
```
[... editing ...]
^C
👋 Session ended (CTRL+C). Goodbye!
```

---

## Understanding the Feedback Loop

VibeCode automatically fixes errors through AI iteration:

### ❌ Iteration 1 - Compilation Fails
```
LLM tries to fix syntax error:
  def hello()
      print('hi')

Error: SyntaxError: invalid syntax
```

### ✅ Iteration 2 - Fixed!
```
LLM sees the error and fixes the colon:
  def hello():
      print('hi')

Success! Code compiled and executed.
```

**Key insight:** The LLM gets smarter with each iteration because it sees:
- What it tried before (previous edit)
- What went wrong (error message)
- What the goal was (your original prompt)

---

## Approval Workflow

After VibeCode generates changes, you have three options:

### (y)es - Apply Changes
```
Apply changes? (y)es / (n)o / (e)dit: y

⏳ Applying changes to real file...

✨ Changes applied successfully!
```

The edited code from the AgentFS sandbox is written to your real file.

### (n)o - Discard Changes
```
Apply changes? (y)es / (n)o / (e)dit: n

❌ Changes discarded.
```

Your original file is unchanged. The sandbox is discarded.

### (e)dit - Edit Manually (Not Yet Implemented)
```
Apply changes? (y)es / (n)o / (e)dit: e

💡 Edit mode not implemented yet.
   (You can manually edit the file and run vibe again)
```

---

## Important Notes

### ✅ Files Are Safe
- All changes happen in AgentFS sandbox FIRST
- Your real files are ONLY modified after you approve
- You can always reject changes

### ⏳ Multiple Iterations
- VibeCode tries up to 5 times to fix errors
- Each iteration, the LLM gets feedback
- It stops early if code succeeds

### 🧹 Session Cleanup
- AgentFS sandbox is automatically cleaned up
- Works with both `quit` command and CTRL+C
- No leftover files or resources

---

## Example Use Cases

### Adding Error Handling
```
python src/main.py "Add try-except error handling" src/api.py
```

### Fixing Syntax Errors
```
python src/main.py "Fix all syntax errors" src/broken_code.py
```

### Adding Docstrings
```
python src/main.py "Add docstrings to all functions" src/utils.py
```

### Refactoring
```
python src/main.py "Refactor to use list comprehension where possible" src/data.py
```

### Adding Logging
```
python src/main.py "Add logging statements for debugging" src/worker.py
```

---

## Troubleshooting

### FileNotFoundError
```
❌ Error: File not found: src/missing.py
```
**Solution:** Make sure the filepath is correct and the file exists.

### AgentFS Error
```
❌ Error: AgentFS initialization failed
```
**Solution:**
1. Check that `agentfs-sdk` is installed: `pip install agentfs-sdk`
2. Ensure you have write permissions in the current directory

### LLM Rate Limit
```
❌ Unexpected error: Rate limit exceeded
```
**Solution:** Wait a few seconds and try again.

### CTRL+C Not Responsive
Sometimes CTRL+C is ignored if async operations are blocking:
```
press CTRL+C twice
or wait for current iteration to complete
```

---

## Configuration

### API Keys

VibeCode uses OpenAI's API (via GPT-4 mini). Set your API key in `.env`:

```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
```

### Iteration Count

To change max iterations (default: 5), edit `src/main.py`:

```python
# Line 160: max_iteration=5  # Change this number
result = await edit_with_validation(str(file_path_obj), prompt, agentfs_manager, max_iteration=10)
```

---

## Performance Tips

1. **Keep files under 1000 lines** - LLM works better with smaller files
2. **Be specific in prompts** - "Add error handling for file operations" is better than "Fix my code"
3. **Use single edit mode for quick fixes** - Faster than interactive session for one file
4. **Reuse interactive session** - Avoids re-initializing AgentFS for multiple files

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│ main.py - CLI Interface                 │
│  - Single edit mode                     │
│  - Interactive session mode (while loop)│
└──────────────┬──────────────────────────┘
               │
               ├─→ agentfs_manager.py ──→ AgentFS Sandbox
               │
               ├─→ feedback.py (Iteration Loop)
               │    ├─→ planner.py ──→ OpenAI LLM
               │    ├─→ execution/ ──→ python_executor.py
               │    └─→ storage/ ──→ AgentFS write
               │
               ├─→ diff/generator.py ──→ unified diff
               │
               └─→ ui/display.py ──→ Terminal colors
```

---

## Next Steps

1. **Test with a simple file:**
   ```bash
   echo 'print("hello"' > test.py
   python src/main.py "Fix syntax error" test.py
   ```

2. **Try interactive session:**
   ```bash
   python src/main.py
   ```

3. **Edit multiple files:**
   - Enter first prompt + file
   - Review and apply
   - Say 'y' to continue
   - Edit second file
   - Type 'quit' to exit

Happy coding! 🚀
