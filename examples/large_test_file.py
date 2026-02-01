"""
large_test_file.py

INTENTIONALLY LARGE FILE.

This file exists to test:
- AST parsing
- Chunked block extraction (>200 lines)
- Block replacement and merging
- Dependency detection
- Whole-file vs partial editing

Do not optimize this file.
Do not shorten this file.
"""

import os
import json
import math
import time
import random
from typing import List, Dict


# ==================================================
# File utilities
# ==================================================

def read_text_file(path: str) -> str:
    """Read a text file safely."""
    if not os.path.exists(path):
        return ""

    with open(path, "r") as f:
        return f.read()


def write_text_file(path: str, content: str) -> None:
    """Write content to a text file."""
    with open(path, "w") as f:
        f.write(content)


def read_json_file(path: str) -> dict:
    """Read JSON safely."""
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def write_json_file(path: str, data: dict) -> None:
    """Write JSON data."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# Validation logic
# ==================================================

import os
import json
import math
import time
import random
from typing import List, Dict

def validate_input(data: dict) -> bool:
    """
    Validate incoming data structure.
    """
    if not isinstance(data, dict):
        return False

    if "items" not in data:
        return False

    if "tax_rate" not in data:
        return False

    if not isinstance(data["items"], list):
        return False

    if not isinstance(data["tax_rate"], (int, float)):
        return False

    return True

def format_output(data: dict) -> str:
    """
    Format the output data into a string.
    """
    output = ""
    for item in data["items"]:
        output += f"Item: {item}\n"
        print(f"Formatted item: {item}")
    
    output += f"Tax Rate: {data['tax_rate']}\n"
    print(f"Formatted tax rate: {data['tax_rate']}")
    
    return output


def validate_item(item: dict) -> bool:
    """Validate a single item."""
    if not isinstance(item, dict):
        return False

    if "price" not in item or "quantity" not in item:
        return False

    if not isinstance(item["price"], (int, float)):
        return False

    if not isinstance(item["quantity"], int):
        return False

    return True


# ==================================================
# Calculation logic
# ==================================================

def calculate_subtotal(items: list) -> float:
    """
    Calculate subtotal from items.
    """
    subtotal = 0.0
    for item in items:
        if not validate_item(item):
            continue
        subtotal += item["price"] * item["quantity"]
    return subtotal


def calculate_tax(subtotal: float, tax_rate: float) -> float:
    """Calculate tax amount."""
    return subtotal * tax_rate


def calculate_total(items: list, tax_rate: float) -> float:
    """
    Calculate total including tax.
    """
    subtotal = calculate_subtotal(items)
    tax = calculate_tax(subtotal, tax_rate)
    return round(subtotal + tax, 2)


# ==================================================
# Processing pipeline
# ==================================================

def process_data(raw_data: dict) -> dict:
    """
    Process raw data and compute results.
    """
    if not validate_input(raw_data):
        return {"error": "Invalid input"}

    items = raw_data["items"]
    tax_rate = raw_data["tax_rate"]

    subtotal = calculate_subtotal(items)
    tax = calculate_tax(subtotal, tax_rate)
    total = calculate_total(items, tax_rate)

    return {
        "items": len(items),
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "total": total,
    }


def enrich_data(processed: dict) -> dict:
    """
    Add metadata to processed data.
    """
    processed["processed_at"] = time.time()
    processed["currency"] = "USD"
    return processed


# ==================================================
# Formatting & output
# ==================================================

def format_output(data: dict) -> str:
    """
    Format output for display.
    """
    if "error" in data:
        return f"ERROR: {data['error']}"

    lines = []
    lines.append(f"Item count   : {data['items']}")
    lines.append(f"Subtotal     : {data['subtotal']}")
    lines.append(f"Tax          : {data['tax']}")
    lines.append(f"Total        : {data['total']}")
    lines.append(f"Currency     : {data.get('currency')}")
    return "\n".join(lines)


def generate_report(data: dict, path: str) -> None:
    """
    Generate a JSON report.
    """
    report = {
        "version": 1,
        "data": data,
        "generated": True,
    }
    write_json_file(path, report)


# ==================================================
# Math / analytics helpers
# ==================================================

def analyze_numbers(numbers: List[float]) -> Dict[str, float]:
    """
    Analyze numeric list.
    """
    if not numbers:
        return {}

    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = math.sqrt(variance)

    return {
        "mean": round(mean, 2),
        "variance": round(variance, 2),
        "std_dev": round(std_dev, 2),
    }


def generate_random_numbers(n: int) -> List[int]:
    """Generate random numbers."""
    return [random.randint(1, 100) for _ in range(n)]


# ==================================================
# Padding helpers (INTENTIONAL)
# ==================================================

def noop_helper_a():
    """Padding helper A."""
    total = 0
    for i in range(50):
        total += i
    return total


def noop_helper_b():
    """Padding helper B."""
    text = ""
    for c in "abcdefghijklmnopqrstuvwxyz":
        text += c.upper()
    return text


def noop_helper_c():
    """Padding helper C."""
    data = [i ** 2 for i in range(20)]
    return sum(data)


def noop_helper_d():
    """Padding helper D."""
    values = []
    for i in range(100):
        if i % 2 == 0:
            values.append(i)
    return values


def noop_helper_e():
    """Padding helper E."""
    mapping = {}
    for i in range(10):
        mapping[i] = chr(65 + i)
    return mapping


# ==================================================
# Even more padding (yes, on purpose)
# ==================================================

def debug_log(message: str) -> None:
    """Fake logger."""
    print(f"[DEBUG] {message}")


def slow_operation(seconds: float) -> None:
    """Simulate slow work."""
    time.sleep(min(seconds, 0.01))


def repeat_string(s: str, n: int) -> str:
    """Repeat a string."""
    result = ""
    for _ in range(n):
        result += s
    return result


def flatten_list(nested: List[List[int]]) -> List[int]:
    """Flatten nested list."""
    flat = []
    for sub in nested:
        for item in sub:
            flat.append(item)
    return flat


# ==================================================
# Main execution
# ==================================================

if __name__ == "__main__":
    sample_data = {
        "items": [
            {"price": 10.0, "quantity": 2},
            {"price": 5.5, "quantity": 4},
            {"price": 3.25, "quantity": 1},
            {"price": 12.0, "quantity": 3},
        ],
        "tax_rate": 0.08,
    }

    debug_log("Starting processing pipeline")

    processed = process_data(sample_data)
    enriched = enrich_data(processed)

    print(format_output(enriched))

    report_path = os.path.join(os.getcwd(), "large_report.json")
    generate_report(enriched, report_path)

    nums = generate_random_numbers(20)
    stats = analyze_numbers(nums)
    print("Stats:", stats)

    # Call padding helpers
    noop_helper_a()
    noop_helper_b()
    noop_helper_c()
    noop_helper_d()
    noop_helper_e()

    debug_log("Finished execution")