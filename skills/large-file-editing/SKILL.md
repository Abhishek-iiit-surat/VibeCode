# Large File Editing

When a file you need to edit is large (roughly 200+ lines), don't read the whole
file and rewrite it yourself with `file_write`. Instead delegate to a specialized
sub-agent via the `Task` tool:

```
Task(
  description: "Edit large file",
  prompt: "<the user's editing instructions, verbatim>",
  subagent_type: "large-file-editor",
  file_path: "<path to the file>",
)
```

The large-file-editor sub-agent parses the file into AST blocks (functions/classes),
finds the block relevant to the request, edits just that chunk, merges it back into
the full file, and validates the merge by compiling and running a temporary copy
before showing the usual diff and asking for approval. This keeps the edit focused
and avoids spending a large fraction of the context window re-sending a big file
verbatim.

For small files, just use `file_read` and `file_write` directly — the Task tool's
overhead isn't worth it below the size threshold.
