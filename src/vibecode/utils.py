# contains common functions used accross project

import pathlib

def validate_file_path(file_path):
    """
    Validate that the file path exists and is readable.
    Returns: (absolute_path, exists) tuple
    """
    try:
        abs_path = pathlib.Path(file_path).resolve()
        if abs_path.exists() and abs_path.is_file():
            return str(abs_path), True
        else:
            return str(abs_path), False
    except Exception as e:
        print(f"Error validating file path: {e}")
        return None, False


def read_file_content(file_path):
    """
    Read and return the content of a file.
    Args:
        file_path (str): Path to the file
    Returns:
        str: Content of the file
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    print(f"📰 Reading file content from {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()

    return content


def strip_markdown_code_blocks(text: str) -> str:
    """
    Remove markdown code block wrappers if present.

    If text starts with ```python or ``` and ends with ```,
    extract the code between them.
    """
    text = text.strip()

    if text.startswith("```"):
        first_newline = text.find('\n')
        if first_newline != -1 and text.rstrip().endswith("```"):
            return text[first_newline + 1:-3].rstrip()

    return text

