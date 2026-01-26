# contains common functions used accross project

import pathlib

def sanitize_file_path(file_path):
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