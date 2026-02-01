"""
Utility functions for data processing workspace.
Provides helpers for validation, transformation, and common operations.
"""

from typing import Any, Dict, List, Union, Optional
import json
import csv
from pathlib import Path
import os


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate that a dictionary contains all required fields.

    Args:
        data: Dictionary to validate
        required_fields: List of field names that must be present

    Returns:
        Tuple of (is_valid, error_message)
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize a string by removing extra whitespace.

    Args:
        text: String to sanitize
        max_length: Optional maximum length (truncates if exceeded)

    Returns:
        Sanitized string
    """
    cleaned = ' '.join(text.split())
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def parse_json_safely(json_string: str) -> tuple[Optional[Dict], Optional[str]]:
    """
    Parse JSON string with error handling.

    Args:
        json_string: JSON string to parse

    Returns:
        Tuple of (parsed_data, error_message)
    """
    try:
        return json.loads(json_string), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split a list into batches of specified size.

    Args:
        items: List to batch
        batch_size: Size of each batch

    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def flatten_dict(nested_dict: Dict, parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        nested_dict: Dictionary to flatten
        parent_key: Prefix for keys
        sep: Separator between parent and child keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def read_csv_file(filepath: Union[str, Path]) -> tuple[List[Dict], Optional[str]]:
    """
    Read a CSV file and return list of dictionaries.

    Args:
        filepath: Path to CSV file

    Returns:
        Tuple of (data_list, error_message)
    """
    try:
        filepath = Path(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return data, None
    except Exception as e:
        return [], f"Error reading CSV: {str(e)}"


def write_json_file(data: Any, filepath: Union[str, Path], pretty: bool = True) -> Optional[str]:
    """
    Write data to a JSON file.

    Args:
        data: Data to write
        filepath: Path to output file
        pretty: Whether to format with indentation

    Returns:
        Error message if failed, None otherwise
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2 if pretty else None)
        return None
    except Exception as e:
        return f"Error writing JSON: {str(e)}"


def deduplicate(items: List[Any], key_func: Optional[callable] = None) -> List[Any]:
    """
    Remove duplicates from a list while preserving order.

    Args:
        items: List to deduplicate
        key_func: Optional function to extract comparison key

    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    for item in items:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def validate_file_path(filepath: Union[str, Path]) -> bool:
    """
    Validate that a file path exists.

    Args:
        filepath: Path to the file to check

    Returns:
        True if the file exists, False otherwise
    """
    return os.path.isfile(filepath)