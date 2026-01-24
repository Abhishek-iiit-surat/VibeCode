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
When given a file and instructions:
1. Understand the current code structure
2. Apply the requested changes
3. Return the COMPLETE modified file with all changes applied
4. Preserve the original formatting style and indentation where appropriate
5. Do not include any explanation, just return the modified code."""

    prompt = f"""Task: {user_prompt}

File: {validated_path}

Current code:
```
{file_content}
```

Please apply the requested changes and return the complete modified file."""

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

    # Return both original and edited content so we can generate diffs
    return file_content, edited_content 

def refine_edits_based_on_error(file_path, original_prompt, previous_edit, execution_result):
    """                                              
      Call LLM again with error context to fix the     
      code.                                                
    """

    error_prompt = f"""You previously edited this    
        code based on: "{original_prompt}"                   
                                                            
        Your previous edit:                                  
        {previous_edit}                                      
                                                            
        But when we ran it, we got this error:               
        Exit Code: {execution_result.exit_code}              
        Error Output:                                        
        {execution_result.stderr}                            
                                                            
        Please fix the code so it runs without errors. Return
        the complete corrected file."""                     
                                                            
      messages = [                                     
          {"role": "system", "content": "You are an expert code debugger. Fix the errors in the code."}, 
          {"role": "user", "content": error_prompt}    
      ]                                                
                                                       
      response = client.chat.completions.create(       
          model="gpt-4o-mini",                         
          temperature=0.7,                             
          messages=messages                            
      )                                                
                                                       
      return response.choices[0].message.content





