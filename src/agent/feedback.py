from dataclasses import dataclass
from typing import List, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.planner import plan_edits, refine_edits_based_on_error
from execution.manager import execute_code, compile_script
from storage.agentfs_manager import AgentFSManager

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
        # Step 1: Get edited content from LLM
        if i == 0:
            # First iteration: get initial edit from LLM using user_prompt
            original_content, edited_content = plan_edits(file_path, user_prompt)
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
            # ✅ Compilation passed! Now try to execute
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