"""
Code chunk merger for reconstructing full files from edited blocks.

This module handles merging LLM-edited code chunks back into the original file,
replacing only the specific functions/classes that were modified.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from context.ast_analyzer import CodeBlock
from typing import List
import ast


def merge_block_into_file(original_content: str, edited_block: CodeBlock) -> str:
    """
    Replace a code block in the original file with its edited version.

    This function takes a full file and replaces the lines corresponding to
    edited_block with the new content from the block.

    TODO(human): Implement this function

    Args:
        original_content: The full original file content as a string
        edited_block: CodeBlock containing the edited code and line numbers

    Returns:
        The full file content with the block replaced

    Implementation hints:
    - Split original_content into lines using .splitlines()
    - Replace lines from edited_block.start_line to edited_block.end_line
    - Remember: line numbers are 1-indexed, but list indices are 0-indexed
    - Split edited_block.content into lines
    - Reconstruct the file: before_lines + edited_lines + after_lines
    - Join with newlines

    Example:
        original = "line1\nline2\nline3\nline4\nline5"
        block = CodeBlock(type='function', name='foo', start_line=2, end_line=3,
                         content="new_line2\nnew_line3")
        result = merge_block_into_file(original, block)
        # result = "line1\nnew_line2\nnew_line3\nline4\nline5"
    """
    # TODO(human): Your implementation here

    start_idx = edited_block.start_line -1
    end_idx = edited_block.end_line

    original_lines = original_content.splitlines()
    edited_lines = edited_block.content.splitlines()

    new_lines = original_lines[:start_idx] + edited_lines + original_lines[end_idx:]
    new_lines = ("\n").join(new_lines)
    return new_lines




def merge_multiple_blocks(original_content: str, edited_blocks: List[CodeBlock]) -> str:
    """
    Merge multiple edited blocks into the original file.

    Processes blocks in reverse order (bottom to top) to avoid line number shifts.

    TODO(human): Implement this function

    Args:
        original_content: The full original file content
        edited_blocks: List of CodeBlock objects with edited content

    Returns:
        The full file with all blocks replaced

    Implementation hints:
    - Sort edited_blocks by start_line in DESCENDING order (highest line first)
    - This prevents line number shifts as we edit from bottom to top
    - Call merge_block_into_file() for each block
    - Each merge updates the content for the next iteration

    Example:
        original = "line1\nline2\nline3\nline4\nline5"
        blocks = [
            CodeBlock(name='a', start_line=2, end_line=2, content="EDIT2"),
            CodeBlock(name='b', start_line=4, end_line=4, content="EDIT4")
        ]
        # Process in reverse: edit line 4 first, then line 2
        # This keeps line numbers valid throughout the process
    """
    edited_blocks = sorted(edited_blocks,key=lambda b: b.start_line,reverse=True)
    lines = original_content.splitlines()
    for block in edited_blocks:
        start_idx  = block.start_line-1
        end_idx = block.end_line
        edited_content = block.content.splitlines()
        lines = lines[:start_idx] + edited_content + lines[end_idx:]
    
    return ("\n").join(lines)



def validate_merge(original_content: str, merged_content: str) -> bool:
    """
    Simple validation to ensure merge didn't corrupt the file.

    TODO(human): Implement this function

    Args:
        original_content: Original file content
        merged_content: Content after merging

    Returns:
        True if merge looks valid, False otherwise

    Implementation hints:
    - Check that merged_content is not empty
    - Check that merged_content has at least some lines
    - Optional: Check that indentation structure looks reasonable
    - Optional: Try to parse as Python AST to verify syntax
    """
    # TODO(human): Your implementation here

    if not merged_content or len(merged_content.splitlines()) == 0:
        return False

    try:
        ast.parse(merged_content)
        return True
    except SyntaxError:
        return False


