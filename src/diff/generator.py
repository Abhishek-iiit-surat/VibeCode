import difflib

def generate_diff(original_content, edited_content, filename):
    """
    Generate a unified diff between original and edited content.

    Args:
        original_content (str): The original file content
        edited_content (str): The edited file content from LLM
        filename (str): The name of the file being edited

    Returns:
        str: Unified diff string
    """
    original_lines = original_content.splitlines(keepends=True)
    edited_lines = edited_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        edited_lines,
        fromfile=f'{filename} (original)',
        tofile=f'{filename} (edited)',
        lineterm=''
    )

    return '\n'.join(diff)
