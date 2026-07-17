"""
Large-file-editor sub-agent: the AST-chunked edit/validate/refine loop.

Ports the pre-restructure feedback.py/merger.py/ast_analyzer.py pipeline onto
Claude: parse the target file into blocks, find the block relevant to the
task, iteratively ask Claude to edit just that chunk, merge it back into the
full file, and validate the merge by compiling/executing a temp copy — never
the real file — before the usual diff+approval gate runs.
"""

import tempfile
from pathlib import Path

from vibecode.context.ast_analyzer import ASTAnalyzer, CodeBlock
from vibecode.diff.generator import generate_diff
from vibecode.execution.manager import compile_script, execute_code
from vibecode.subagents.merger import merge_block_into_file, validate_merge
from vibecode.subagents.prompts import PROMPT
from vibecode.ui.display import get_approval, show_diff
from vibecode.utils import read_file_content, strip_markdown_code_blocks

MAX_ITERATIONS = 5


def _ask_claude(client, model: str, system_prompt: str, user_prompt: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    return strip_markdown_code_blocks(text)


def _edit_chunk_with_claude(client, model: str, context_code: str, task: str, last_error) -> str:
    if last_error is None:
        prompt = f"Task: {task}\n\nCurrent code:\n{context_code}\n\nReturn the COMPLETE modified chunk."
    else:
        prompt = PROMPT["error_prompt"].format(
            original_prompt=task,
            previous_edit=context_code,
            execution_result=last_error,
        )
    return _ask_claude(client, model, PROMPT["planner_system_prompt"], prompt)


def run_large_file_editor(file_path: str, task: str, client, model: str) -> str:
    """
    Delegate-target for Task(subagent_type="large-file-editor"). Edits one
    large file, showing a diff and asking for approval before writing.
    """
    original_content = read_file_content(file_path)

    analyzer = ASTAnalyzer()
    blocks = analyzer.parse_file(file_path)
    relevant = analyzer.find_relevant_blocks(blocks, task)

    if not relevant:
        edited_content = _ask_claude(
            client, model, PROMPT["planner_system_prompt"],
            f"Task: {task}\n\nCurrent code:\n{original_content}\n\nReturn the COMPLETE modified file.",
        )
    else:
        target_block = relevant[0]
        context_blocks = analyzer.get_context_for_block(blocks, target_block)
        context_code = "\n\n".join(b.content for b in context_blocks)

        merged_content = original_content
        last_error = None
        for _ in range(MAX_ITERATIONS):
            edited_chunk = _edit_chunk_with_claude(client, model, context_code, task, last_error)
            edited_block = CodeBlock(
                type=target_block.type,
                name=target_block.name,
                start_line=target_block.start_line,
                end_line=target_block.end_line,
                content=edited_chunk,
            )
            merged_content = merge_block_into_file(original_content, edited_block)

            if not validate_merge(original_content, merged_content):
                break

            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
                tmp.write(merged_content)
                tmp_path = tmp.name

            compile_result = compile_script(tmp_path)
            if compile_result.success:
                exec_result = execute_code(tmp_path)
                if exec_result.success:
                    last_error = None
                    break
                last_error = exec_result
            else:
                last_error = compile_result

        edited_content = merged_content

    diff = generate_diff(original_content, edited_content, file_path)
    if not diff:
        return "No changes were necessary."

    show_diff(diff)
    approval = get_approval()
    if approval == "y":
        Path(file_path).write_text(edited_content)
        return f"Large-file edit applied to {file_path}."
    return f"Large-file edit for {file_path} was proposed but declined by the user."
