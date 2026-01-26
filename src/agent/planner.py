import os
import pathlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def plan_edits(file_path, user_prompt):
    """
    Reads a file and sends it to OpenAI with a user prompt.
    Returns: (original_content, edited_content) tuple
    """
    # Validate and read the file
    validated_path, file_exists = sanitize_file_path(file_path)

    if not file_exists:
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(validated_path, 'r') as f:
        file_content = f.read()

    system_prompt = """You are an expert code editor. Your task is to modify code based on user instructions.
IMPORTANT RULES:
1. Understand the current code structure
2. Apply ONLY the requested changes
3. Return the COMPLETE modified file with all changes applied
4. Preserve the original formatting style and indentation
5. DO NOT INCLUDE ANY MARKDOWN FORMATTING (no ```, no code blocks, no explanations)
6. Return ONLY the raw Python code, nothing else
7. Start with the first line of code, end with the last line of code"""

    prompt = f"""Task: {user_prompt}

File: {validated_path}

Current code:
{file_content}

RETURN ONLY THE MODIFIED PYTHON CODE. NO MARKDOWN. NO EXPLANATIONS. JUST THE CODE."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=messages
    )

    edited_content = response.choices[0].message.content

    # Strip markdown code blocks if the LLM accidentally included them
    # (Some models wrap code in ```python ... ``` despite instructions)
    edited_content = strip_markdown_code_blocks(edited_content)

    # Return both original and edited content so we can generate diffs
    return file_content, edited_content


def strip_markdown_code_blocks(text: str) -> str:
    """
    Remove markdown code block wrappers if present.

    If text starts with ```python or ``` and ends with ```,
    extract the code between them.
    """
    text = text.strip()

    # Check if wrapped in markdown code blocks
    if text.startswith("```"):
        # Find the end of the opening fence
        first_newline = text.find('\n')
        if first_newline != -1:
            # Check if it ends with ```
            if text.rstrip().endswith("```"):
                # Extract content between the fences
                extracted = text[first_newline+1:-3].rstrip()
                return extracted

    return text 

def refine_edits_based_on_error(file_path, original_prompt, previous_edit, execution_result):
    """
    Call LLM again with error context to fix the code.
    """
    error_prompt = f"""You previously edited this code based on: "{original_prompt}"

Your previous edit:
{previous_edit}

But when we ran it, we got this error:
Exit Code: {execution_result.exit_code}
Error Output:
{execution_result.stderr}

PLEASE FIX THIS CODE. RETURN ONLY THE CORRECTED PYTHON CODE WITH NO MARKDOWN, NO EXPLANATIONS, NO CODE BLOCKS. JUST THE RAW CODE."""

    messages = [
        {"role": "system", "content": "You are an expert Python code debugger. Your job is to fix syntax and runtime errors in Python code. IMPORTANT: Always return ONLY the corrected Python code. Never include markdown formatting, code blocks (```), or any explanations. Return raw code only."},
        {"role": "user", "content": error_prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages
    )

    refined_content = response.choices[0].message.content

    # Strip markdown code blocks if the LLM accidentally included them
    refined_content = strip_markdown_code_blocks(refined_content)

    return refined_content





