"""
Editor module for safely applying changes to files.
"""

def apply_changes(file_path, edited_content):
    """
    Apply the edited content to the actual file.

    Args:
        file_path (str): Path to the file to modify
        edited_content (str): The new content from LLM

    Returns:
        bool: True if successful, False otherwise

    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(file_path, 'w') as f:
            f.write(edited_content)
        return True
    except IOError as e:
        raise IOError(f"Failed to write to file {file_path}: {e}")
