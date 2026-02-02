from dataclasses import dataclass
from typing import List, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.planner import plan_edits, refine_edits_based_on_error
from execution.manager import execute_code, compile_script
from storage.agentfs_manager import AgentFSManager
from src.utils import read_file_content, validate_file_path
from context.ast_analyzer import ASTAnalyzer, CodeBlock
from agent.merger import merge_block_into_file, validate_merge

LARGE_FILE_THRESHOLD = 200  # lines — files above this use chunked editing

@dataclass
class Iteration:
    attempt_number: int
    edited_content: str
    execution_result: Any
    success: bool

@dataclass
class FeedbackResult:
    original_content: str
    final_edited_content: str
    iterations: List[Iteration]
    success: bool
    

async def edit_with_validation(file_path: str, user_prompt: str, agent_fs_manager, max_iteration: int = 5):
    """
    Edit code and validate by running it, iterating up to max_iteration times.

    Workflow for each iteration:
    1. Get edited content from LLM (first time) OR refine based on previous errors (later times)
    2. Write edited content to AgentFS sandbox
    3. Compile the sandbox file
    4. If compilation succeeds, execute the sandbox file
    5. If execution succeeds, return success
    6. If any step fails, record iteration and continue to next iteration

    The key insight: Each iteration knows about ALL previous iterations because:
    - edited_content carries the latest version
    - execution_result carries the latest error (compilation or execution)
    - These are passed to refine_edits_based_on_error() so LLM can fix the right thing
    """
    original_content = None
    iterations = []
    edited_content = None
    last_error = None  # Track the last error (could be compilation or execution)

    for i in range(0, max_iteration):
        if i == 0:
            original_content = read_file_content(file_path)
            edited_content = plan_edits(original_content, user_prompt)
            print(f"🔄 Iteration {i+1}: Initial edit from LLM based on prompt")
        else:
            # Subsequent iterations: LLM refines based on previous edit + error
            # The LLM sees:
            # - The original user prompt (what user asked for)
            # - The previous edited_content (what we tried)
            # - The last_error (what went wrong - could be compilation or execution error)
            edited_content = refine_edits_based_on_error(
                file_path,
                user_prompt,                 # Original user instruction
                edited_content,              # Previous attempt (what LLM tried last time)
                last_error                   # Error from last attempt (what went wrong)
            )
            print(f"🔄 Iteration {i+1}: LLM refining based on error from iteration {i}")

        # Step 2: Write edited content to AgentFS sandbox
        # This OVERWRITES the sandbox file with the latest edited_content
        sandbox_path = await agent_fs_manager.write_to_sandbox(file_path, edited_content)

        # Step 3: Compile the sandbox file (syntax check)
        compilation_result = compile_script(sandbox_path)

        if compilation_result.success:
            # Compilation passed! Now try to execute
            # Step 4: Execute the sandbox file (runtime check)
            execution_result = execute_code(sandbox_path)

            if execution_result.success:
                # ✅✅ SUCCESS! Code compiled AND ran without errors
                print(f"✅ Iteration {i+1}: Script executed successfully!\n")
                iteration = Iteration(
                    attempt_number=i+1,
                    edited_content=edited_content,
                    execution_result=execution_result,
                    success=True
                )
                iterations.append(iteration)

                # Return successful result immediately
                return FeedbackResult(
                    original_content=original_content,
                    final_edited_content=edited_content,
                    iterations=iterations,
                    success=True
                )
            else:
                # ❌ Execution failed (runtime error)
                print(f"❌ Iteration {i+1}: Execution failed with error")
                iteration = Iteration(
                    attempt_number=i+1,
                    edited_content=edited_content,
                    execution_result=execution_result,  # Contains stderr from execution
                    success=False
                )
                iterations.append(iteration)
                last_error = execution_result  # Save for next iteration
                # Continue to next iteration - last_error is passed to LLM to fix
        else:
            # ❌ Compilation failed (syntax error)
            print(f"❌ Iteration {i+1}: Compilation failed")
            iteration = Iteration(
                attempt_number=i+1,
                edited_content=edited_content,
                execution_result=compilation_result,    # Contains compilation error
                success=False
            )
            iterations.append(iteration)
            last_error = compilation_result  # Save for next iteration
            # Continue to next iteration - last_error is passed to LLM to fix

    # All iterations exhausted - code still not working
    print(f"⚠️  Max iterations ({max_iteration}) reached. Code still has issues.")
    return FeedbackResult(
        original_content=original_content,
        final_edited_content=edited_content,
        iterations=iterations,
        success=False
    )


async def smart_edit(file_path: str, user_prompt: str, agent_fs_manager, max_iteration: int = 5):
    """
    Router: picks whole-file or chunked editing based on file size.

    TODO(human): Implement this function

    Hints:
    - Use read_file_content(file_path) to get the file text
    - Count lines: len(content.splitlines())
    - If lines <= LARGE_FILE_THRESHOLD, print that you're using whole-file mode
      and call: return await edit_with_validation(...)
    - Else, print that you're using chunked mode (and how many lines the file has)
      and call: return await edit_large_file_with_validation(...)
    """
    file_content = read_file_content(file_path)

    if len(file_content.splitlines()) <= LARGE_FILE_THRESHOLD:
        print(f"Small file detected, Sitback! Analyzing complete file ....")
        return await edit_with_validation(file_path,user_prompt,agent_fs_manager,max_iteration)

    print(f"Big file detected ({len(file_content.splitlines())} lines), Initiating smart chunking")
    return await edit_large_file_with_validation(file_path,user_prompt,agent_fs_manager, max_iteration)


async def edit_large_file_with_validation(file_path: str, user_prompt: str, agent_fs_manager, max_iteration: int = 5):
    """
    Edit a large file by extracting and editing only the relevant code block.

    Flow:
        1. Parse file → find relevant block → get context → send to LLM
        2. LLM returns edited chunk → merge back into full file
        3. Write merged file to sandbox → compile → execute → validate

    TODO(human): Implement this function step by step using the hints below.
    """

    original_content = read_file_content(file_path)

    analyzer = ASTAnalyzer()
    blocks = analyzer.parse_file(file_path)
    print(f"{len(blocks)} Blocks detected")
    relevant_chunk = analyzer.find_relevant_blocks(blocks,user_prompt)

    if not relevant_chunk:
        return await edit_with_validation(file_path,user_prompt,agent_fs_manager,max_iteration)
    
    target_block = relevant_chunk[0]
    context_blocks = analyzer.get_context_for_block(blocks,target_block)
    context_code = "\n\n".join(block.content for block in context_blocks)
    edited_chunk = plan_edits(context_code,user_prompt)
    edited_block = CodeBlock(
            type=target_block.type,
            name=target_block.name,
            start_line=target_block.start_line,
            end_line=target_block.end_line,
            content=edited_chunk
    )
    merged_content = merge_block_into_file(original_content,edited_block)

    if not validate_merge(original_content,merged_content):
        print(f"⚠️  Warning: Could not apply chunked changes, falling back to whole-file edit")
        return await edit_with_validation(file_path,user_prompt,agent_fs_manager,max_iteration)
    
    iterations = []
    last_error = None
    for i in range(0, max_iteration):
        if i == 0:
            edited_content = plan_edits(context_code,user_prompt)
            print(f"🔄 Iteration {i+1}: Initial edit from LLM based on prompt")
        else:
            edited_content = refine_edits_based_on_error(
                file_path,
                user_prompt,
                edited_content,
                last_error
            )
            print(f"🔄 Iteration {i+1}: LLM refining based on error from iteration {i}")

        # Merge the LLM's edited chunk back into the full file
        edited_block = CodeBlock(
            type=target_block.type,
            name=target_block.name,
            start_line=target_block.start_line,
            end_line=target_block.end_line,
            content=edited_content
        )

        merged_content = merge_block_into_file(original_content,edited_block)
        edited_content = merged_content
        sandbox_path = await agent_fs_manager.write_to_sandbox(file_path, edited_content)
        compilation_result = compile_script(sandbox_path)

        if compilation_result.success:
            execution_result = execute_code(sandbox_path)

            if execution_result.success:
                print(f"✅ Iteration {i+1}: Script executed successfully!\n")
                iteration = Iteration(
                    attempt_number=i+1,
                    edited_content=edited_content,
                    execution_result=execution_result,
                    success=True
                )
                iterations.append(iteration)

                # Return successful result immediately
                return FeedbackResult(
                    original_content=original_content,
                    final_edited_content=edited_content,
                    iterations=iterations,
                    success=True
                )
            else:
                # ❌ Execution failed (runtime error)
                print(f"❌ Iteration {i+1}: Execution failed with error")
                iteration = Iteration(
                    attempt_number=i+1,
                    edited_content=edited_content,
                    execution_result=execution_result,  # Contains stderr from execution
                    success=False
                )
                iterations.append(iteration)
                last_error = execution_result  # Save for next iteration
                # Continue to next iteration - last_error is passed to LLM to fix
        else:
            # ❌ Compilation failed (syntax error)
            print(f"❌ Iteration {i+1}: Compilation failed")
            iteration = Iteration(
                attempt_number=i+1,
                edited_content=edited_content,
                execution_result=compilation_result,    # Contains compilation error
                success=False
            )
            iterations.append(iteration)
            last_error = compilation_result  # Save for next iteration
            # Continue to next iteration - last_error is passed to LLM to fix

    # All iterations exhausted - code still not working
    print(f"⚠️  Max iterations ({max_iteration}) reached. Code still has issues.")
    return FeedbackResult(
        original_content=original_content,
        final_edited_content=edited_content,
        iterations=iterations,
        success=False
    )
    