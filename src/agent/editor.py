"""
Editor module for safely applying changes to files.
"""

def apply_changes(file_path, edited_content):
    """
    Apply the edited content to the actual file (without sandbox).

    This is for non-sandboxed mode (backward compatibility).

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


async def apply_sandbox_to_real_file(file_path: str, agentfs_manager):
    """
    Copy edited content from AgentFS sandbox to real file.

    Called after user approves changes.

    Args:
        file_path (str): Path to the file to modify
        agentfs_manager: AgentFSManager instance to access sandbox

    Raises:
        IOError: If file cannot be written
    """
    try:
        await agentfs_manager.apply_to_real_file(file_path)
        return True
    except Exception as e:
        raise IOError(f"Failed to apply changes from sandbox: {e}")



