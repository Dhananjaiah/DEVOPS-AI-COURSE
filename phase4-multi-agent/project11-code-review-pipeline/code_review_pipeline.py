# code_review_pipeline.py
# Project 11: Automated Code Review Pipeline
# Three specialized agents collaborate to review, test, and fix Python code.
# This demonstrates how AI can be integrated into CI/CD DevOps pipelines.

# Standard library imports
import os           # For file system operations and environment variables
import sys          # For reading command-line arguments
from datetime import datetime  # For timestamping output files

# Load environment variables from the .env file (API keys)
from dotenv import load_dotenv
load_dotenv()  # Reads ANTHROPIC_API_KEY from .env

# TypedDict for defining the shared state structure between agents
from typing import TypedDict, Optional

# LangGraph for building the multi-agent workflow graph
from langgraph.graph import StateGraph, END

# ChatAnthropic is the LangChain wrapper for Claude API calls
from langchain_anthropic import ChatAnthropic

# Message types for structuring prompts to Claude
from langchain_core.messages import HumanMessage, SystemMessage


# ============================================================
# STEP 1: DEFINE THE SHARED STATE
# ============================================================
# This state is shared across all three agents.
# Each agent reads from it and writes its output back to it.
# The state represents the complete "paper trail" of the code review.

class CodeReviewState(TypedDict):
    # The original code that needs to be reviewed
    original_code: str

    # The filename of the code being reviewed (for display purposes)
    filename: str

    # The structured review produced by the Code Reviewer agent
    # Contains CRITICAL/WARNING/INFO severity issues with line numbers
    review: Optional[str]

    # The pytest test file produced by the Test Writer agent
    # These tests would catch the bugs identified in the review
    test_code: Optional[str]

    # The corrected version of the code produced by the Code Fixer agent
    fixed_code: Optional[str]

    # Whether the fixed code has been approved by the Approval node
    approval_status: Optional[str]  # "APPROVED", "NEEDS_ANOTHER_FIX", or "MAX_CYCLES_REACHED"

    # How many fix cycles we have completed (used to prevent infinite loops)
    fix_cycles: int


# ============================================================
# STEP 2: INITIALIZE THE AI MODEL
# ============================================================

# Create the Claude model instance shared by all three agents
# claude-opus-4-6 has strong code understanding and generation capabilities
llm = ChatAnthropic(
    model="claude-opus-4-6",                               # Use the most capable model
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),  # API key from .env
    max_tokens=4096                                    # Code responses can be long
)


# ============================================================
# STEP 3: DEFINE AGENT SYSTEM PROMPTS
# ============================================================
# Each agent has a specialized identity defined by its system prompt.
# This is what makes a "reviewer" different from a "fixer" — they have
# different expertise, different priorities, different output formats.

# Agent 1: Code Reviewer — acts like a senior software engineer
REVIEWER_SYSTEM_PROMPT = """You are a senior software engineer doing code review. Analyze code for: bugs, security issues, performance problems, code style issues. Be specific about line numbers and issues.

When reviewing code:
1. Read the entire code carefully before writing any feedback
2. Categorize each issue with a severity level:
   - CRITICAL: bugs that cause crashes, security vulnerabilities, data loss risks
   - WARNING: poor practices, potential bugs, performance issues
   - INFO: style suggestions, minor improvements, best practices
3. Always reference specific line numbers where possible
4. Explain WHY each issue is a problem, not just that it is one
5. Be constructive — acknowledge good parts of the code too

Format your review exactly like this:
## Code Review Report

### Summary
[One paragraph overview of the code and its main issues]

### Issues Found

**[CRITICAL/WARNING/INFO] Issue Title (Line X)**
- Problem: [What the issue is]
- Risk: [What could go wrong]
- Fix: [How to resolve it]

### Positive Aspects
[What the code does well]

### Overall Assessment
[PASS/FAIL and brief justification]"""

# Agent 2: Test Writer — acts like a QA engineer
TEST_WRITER_SYSTEM_PROMPT = """You are a QA engineer. Given code and a review, write pytest test cases that would catch the bugs found in the review.

When writing tests:
1. Write one test function for each CRITICAL or WARNING issue identified in the review
2. Name tests descriptively: test_should_[behavior_being_tested]
3. Use pytest fixtures and parametrize where appropriate
4. Each test should actually fail on the buggy code and pass on the fixed code
5. Include docstrings explaining what each test is checking
6. Group tests in a class named TestCodeReview
7. Import only standard library modules and pytest (do not import the code being tested — include mock examples)
8. Add edge case tests for boundary conditions

Write a complete, runnable pytest file starting with proper imports."""

# Agent 3: Code Fixer — acts like a code improvement specialist
FIXER_SYSTEM_PROMPT = """You are a code fixer. Given original code, a review, and test cases, produce fixed code that addresses all CRITICAL and WARNING issues.

When fixing code:
1. Address ALL CRITICAL issues — these are non-negotiable
2. Address ALL WARNING issues where possible
3. You may skip INFO-level issues if fixing them would significantly change the code structure
4. Maintain the original code's overall structure and intent
5. Add comments explaining each fix you made
6. Do NOT change the function signatures (names, parameters) unless required by the fix
7. Make the fixed code production-ready

Start your response with a brief "## Changes Made" section listing each fix, then provide the complete fixed code.
The fixed code should be enclosed in ```python code blocks."""


# ============================================================
# STEP 4: DEFINE THE AGENT NODES
# ============================================================

def review_node(state: CodeReviewState) -> dict:
    """
    Node 1: Code Reviewer Agent
    Reads the original code and produces a structured review with
    CRITICAL/WARNING/INFO severity issues and specific line numbers.
    """
    # Announce which agent is working
    print("\n" + "="*60)
    print("🔍 Code Reviewer analyzing code...")
    print(f"   File: {state.get('filename', 'unknown')}")
    print("="*60)

    # Count lines to give the reviewer context about code size
    code_lines = state["original_code"].split('\n')
    print(f"   Code size: {len(code_lines)} lines")

    # Build the prompt for the reviewer
    # We provide the full code and ask for a structured review
    review_prompt = f"""Please perform a thorough code review of the following Python code.

File: {state.get('filename', 'code.py')}

```python
{state['original_code']}
```

Review this code for:
1. Security vulnerabilities (SQL injection, XSS, authentication flaws)
2. Bugs that would cause runtime errors or incorrect behavior
3. Performance issues (inefficient algorithms, unnecessary loops)
4. Code quality issues (missing error handling, unclear variable names)
5. Missing input validation

Be specific with line numbers and provide clear explanations of each issue."""

    # Call the Reviewer agent (Claude with the reviewer system prompt)
    response = llm.invoke([
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),  # Reviewer's identity
        HumanMessage(content=review_prompt)              # What to review
    ])

    # Extract the review text from the response
    review = response.content

    # Count issues found by severity level
    critical_count = review.upper().count("CRITICAL")
    warning_count = review.upper().count("WARNING")
    info_count = review.upper().count("INFO")

    # Display review summary in the terminal
    print(f"\n📋 Review Summary:")
    print(f"   CRITICAL issues: {critical_count}")
    print(f"   WARNING issues:  {warning_count}")
    print(f"   INFO issues:     {info_count}")
    print("\n   Review Preview (first 600 chars):")
    print("-" * 40)
    print(review[:600] + "..." if len(review) > 600 else review)
    print("-" * 40)

    # Return the review to state
    return {
        "review": review,
        "fix_cycles": 0  # Reset fix cycle counter at the start
    }


def test_node(state: CodeReviewState) -> dict:
    """
    Node 2: Test Writer Agent
    Takes the original code and the review, then writes pytest test cases
    that would specifically catch the bugs identified in the review.
    """
    # Announce which agent is working
    print("\n" + "="*60)
    print("🧪 Test Writer creating test cases...")
    print("="*60)

    # Build the prompt for the test writer
    # We give it both the code AND the review so it knows what bugs to test for
    test_prompt = f"""Please write pytest test cases for the following code based on the code review findings.

ORIGINAL CODE:
```python
{state['original_code']}
```

CODE REVIEW FINDINGS:
{state['review']}

Write pytest test cases that:
1. Test each CRITICAL issue identified in the review
2. Test each WARNING issue identified in the review
3. Include edge cases and boundary condition tests
4. Would FAIL on the original buggy code
5. Would PASS on properly fixed code

Provide a complete, runnable pytest file."""

    # Call the Test Writer agent
    response = llm.invoke([
        SystemMessage(content=TEST_WRITER_SYSTEM_PROMPT),  # Test writer's identity
        HumanMessage(content=test_prompt)                   # What tests to write
    ])

    # Extract the test code from the response
    test_code = response.content

    # Show preview of the tests
    print(f"\n🧪 Test Code Preview (first 600 chars):")
    print("-" * 40)
    print(test_code[:600] + "..." if len(test_code) > 600 else test_code)
    print("-" * 40)
    print(f"   Total test code: {len(test_code)} characters")

    # Count how many test functions were written
    test_count = test_code.count("def test_")
    print(f"   Test functions written: {test_count}")

    # Return the test code to state
    return {"test_code": test_code}


def fix_node(state: CodeReviewState) -> dict:
    """
    Node 3: Code Fixer Agent
    Takes the original code, review, and test cases, then produces
    a fixed version of the code that addresses all CRITICAL and WARNING issues.
    """
    # Get the current fix cycle number
    cycle = state.get("fix_cycles", 0) + 1

    # Announce which agent is working
    print("\n" + "="*60)
    print(f"🔧 Code Fixer fixing issues (cycle {cycle})...")
    print("="*60)

    # Check if this is the first fix or a re-fix after failed approval
    is_refix = state.get("fix_cycles", 0) > 0

    if is_refix:
        # We already tried to fix it once but approval failed
        # Tell the fixer to try harder
        print("   Re-fixing after approval failure...")
        fix_prompt = f"""The previous fix attempt did not fully address all CRITICAL issues. Please try again more carefully.

ORIGINAL CODE:
```python
{state['original_code']}
```

CODE REVIEW:
{state['review']}

TEST CASES (the fixed code should pass these):
{state['test_code']}

PREVIOUS FIX ATTEMPT:
```python
{state.get('fixed_code', 'No previous fix')}
```

Please produce a NEW, more thorough fix that:
1. Addresses ALL CRITICAL issues without exception
2. Addresses ALL WARNING issues
3. Would pass all the test cases provided
4. Includes clear comments explaining each fix"""
    else:
        # First fix attempt
        fix_prompt = f"""Please fix the following Python code based on the review and test cases provided.

ORIGINAL CODE:
```python
{state['original_code']}
```

CODE REVIEW (issues to fix):
{state['review']}

TEST CASES (your fixed code should pass these):
{state['test_code']}

Produce a fixed version that addresses all CRITICAL and WARNING issues.
Add inline comments explaining each fix you made."""

    # Call the Code Fixer agent
    response = llm.invoke([
        SystemMessage(content=FIXER_SYSTEM_PROMPT),  # Fixer's identity
        HumanMessage(content=fix_prompt)              # What to fix
    ])

    # Extract the fixed code from the response
    fixed_code = response.content

    # Show preview of the fixed code
    print(f"\n🔧 Fixed Code Preview (first 600 chars):")
    print("-" * 40)
    print(fixed_code[:600] + "..." if len(fixed_code) > 600 else fixed_code)
    print("-" * 40)
    print(f"   Total response: {len(fixed_code)} characters")

    # Return the fixed code and increment the fix cycle counter
    return {
        "fixed_code": fixed_code,
        "fix_cycles": cycle  # Track how many fix cycles we have done
    }


def approve_node(state: CodeReviewState) -> dict:
    """
    Node 4: Approval Node
    Checks if the fixed code adequately addresses all CRITICAL issues.
    Either approves the fix or requests another fix cycle.
    Has a maximum of 2 fix cycles to prevent infinite loops.
    """
    # Announce the approval check
    print("\n" + "="*60)
    print("✅ Approval Agent checking fix quality...")
    print("="*60)

    # Get current fix cycle count
    current_cycles = state.get("fix_cycles", 0)

    # Circuit breaker: if we have done 2 fix cycles, force approval
    if current_cycles >= 2:
        print("   Max fix cycles reached (2). Approving as-is.")
        return {"approval_status": "MAX_CYCLES_REACHED"}

    # Ask Claude to evaluate whether the fix addressed all CRITICAL issues
    approval_prompt = f"""Please evaluate whether the fixed code adequately addresses all CRITICAL and WARNING issues from the code review.

ORIGINAL CODE REVIEW (issues that needed fixing):
{state['review']}

FIXED CODE:
{state.get('fixed_code', 'No fix provided')}

For each CRITICAL issue in the review, check:
1. Is the issue actually fixed in the new code?
2. Did the fix introduce any new problems?
3. Does the fix follow best practices?

Respond in this exact format:
VERDICT: APPROVED or NEEDS_ANOTHER_FIX
UNRESOLVED_ISSUES: [List any CRITICAL issues that were NOT fixed, or "None"]
NOTES: [Brief explanation of your decision]"""

    # Call Claude to evaluate the fix quality
    response = llm.invoke([
        SystemMessage(content="You are a senior software architect doing final approval review. Be strict about security and critical bugs."),
        HumanMessage(content=approval_prompt)
    ])

    approval_text = response.content

    # Parse the verdict from the response
    if "VERDICT: APPROVED" in approval_text or "APPROVED" in approval_text.upper():
        approval_status = "APPROVED"
        print("   ✅ Fix APPROVED! All critical issues resolved.")
    else:
        approval_status = "NEEDS_ANOTHER_FIX"
        print("   ⚠️  Fix needs more work. Sending for another fix cycle.")

    # Show the approval feedback
    print(f"\n   Approval notes: {approval_text[:300]}...")

    # Return the approval status
    return {"approval_status": approval_status}


def output_node(state: CodeReviewState) -> dict:
    """
    Final Node: Output and Save
    Saves all outputs to the review_output/ directory:
    - review.md: The code review report
    - test_cases.py: The generated test file
    - fixed_code.py: The corrected code
    - summary.md: A summary of the entire pipeline run
    """
    # Announce the final output step
    print("\n" + "="*60)
    print("💾 Saving all outputs to review_output/...")
    print("="*60)

    # Create the output directory if it does not exist
    os.makedirs("review_output", exist_ok=True)

    # Create a timestamp for this review run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create a safe filename prefix from the source filename
    safe_name = state.get("filename", "code").replace(".py", "").replace(" ", "_")

    # Save the code review report
    review_path = f"review_output/{safe_name}_review_{timestamp}.md"
    with open(review_path, "w", encoding="utf-8") as f:
        f.write(f"# Code Review: {state.get('filename', 'Unknown File')}\n")
        f.write(f"Reviewed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(state.get("review", "No review available"))
    print(f"   📋 Review saved to: {review_path}")

    # Save the generated test cases
    test_path = f"review_output/{safe_name}_tests_{timestamp}.py"
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(f"# Auto-generated test cases for: {state.get('filename', 'Unknown')}\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(state.get("test_code", "# No tests generated"))
    print(f"   🧪 Tests saved to: {test_path}")

    # Save the fixed code
    fixed_path = f"review_output/{safe_name}_fixed_{timestamp}.py"
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write(f"# Fixed version of: {state.get('filename', 'Unknown')}\n")
        f.write(f"# Fixed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Fix cycles: {state.get('fix_cycles', 0)}\n\n")
        f.write(state.get("fixed_code", "# No fix generated"))
    print(f"   🔧 Fixed code saved to: {fixed_path}")

    # Save a summary report
    summary_path = f"review_output/{safe_name}_summary_{timestamp}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Code Review Pipeline Summary\n\n")
        f.write(f"**File reviewed:** {state.get('filename', 'Unknown')}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Fix cycles:** {state.get('fix_cycles', 0)}\n")
        f.write(f"**Approval status:** {state.get('approval_status', 'Unknown')}\n\n")
        f.write("## Pipeline Steps Completed\n")
        f.write("1. ✅ Code Review — identified all issues with severity levels\n")
        f.write("2. ✅ Test Generation — wrote pytest cases for each issue\n")
        f.write("3. ✅ Code Fix — addressed all CRITICAL and WARNING issues\n")
        f.write("4. ✅ Approval — verified fix quality\n\n")
        f.write("## Output Files\n")
        f.write(f"- Review report: `{review_path}`\n")
        f.write(f"- Test cases: `{test_path}`\n")
        f.write(f"- Fixed code: `{fixed_path}`\n")
    print(f"   📊 Summary saved to: {summary_path}")

    # Display the final summary in the terminal
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"   File reviewed: {state.get('filename', 'Unknown')}")
    print(f"   Fix cycles: {state.get('fix_cycles', 0)}")
    print(f"   Approval status: {state.get('approval_status', 'Unknown')}")
    print(f"\n   All outputs saved to: review_output/")
    print("\n   To run the generated tests:")
    print(f"   pytest {test_path} -v")

    return {}  # No state changes needed at the end


# ============================================================
# STEP 5: ROUTING FUNCTION FOR APPROVAL
# ============================================================

def should_refix(state: CodeReviewState) -> str:
    """
    Routing function: decides whether the code needs another fix cycle.
    Called after approve_node to determine the next step.
    Returns: "fix" to go back for another fix, "output" to save and finish
    """
    status = state.get("approval_status", "NEEDS_ANOTHER_FIX")

    if status == "APPROVED":
        print("   ➡️  Routing: Approved → going to OUTPUT")
        return "output"  # Done — save and finish
    elif status == "MAX_CYCLES_REACHED":
        print("   ➡️  Routing: Max cycles → going to OUTPUT (forced)")
        return "output"  # Max retries hit — save what we have
    else:
        print(f"   ➡️  Routing: Needs more fixing → going back to FIX (cycles: {state.get('fix_cycles', 0)})")
        return "fix"  # Go back for another fix attempt


# ============================================================
# STEP 6: BUILD THE LANGGRAPH WORKFLOW
# ============================================================

def build_pipeline() -> StateGraph:
    """
    Builds the code review pipeline workflow.
    The pipeline flows: review → test → fix → approve → [fix again or output]
    """
    # Create the workflow graph
    workflow = StateGraph(CodeReviewState)

    # Register all nodes
    workflow.add_node("review", review_node)    # Code Reviewer agent
    workflow.add_node("test", test_node)         # Test Writer agent
    workflow.add_node("fix", fix_node)           # Code Fixer agent
    workflow.add_node("approve", approve_node)   # Approval checker
    workflow.add_node("output", output_node)     # Final output saver

    # Set the entry point
    workflow.set_entry_point("review")

    # Define the pipeline flow
    workflow.add_edge("review", "test")    # After review, write tests
    workflow.add_edge("test", "fix")       # After tests, fix the code
    workflow.add_edge("fix", "approve")    # After fixing, check approval

    # Conditional edge after approval: refix or output
    workflow.add_conditional_edges(
        "approve",      # Starting node for the conditional
        should_refix,   # Routing function
        {
            "fix": "fix",       # If "fix" returned, go back to fix node
            "output": "output"  # If "output" returned, go to output node
        }
    )

    # After output, workflow ends
    workflow.add_edge("output", END)

    # Compile the workflow into an executable graph
    compiled = workflow.compile()

    print("\n✅ Code review pipeline built!")
    print("   Flow: review → test → fix → approve → [fix loop] → output")

    return compiled


# ============================================================
# STEP 7: MAIN ENTRY POINT
# ============================================================

def run_code_review_pipeline(code: str, filename: str = "code.py"):
    """
    Main function to run the full code review pipeline on a piece of code.
    Three agents will review, test, and fix the code automatically.
    """
    print("\n" + "🔬 "*20)
    print("CODE REVIEW PIPELINE")
    print("🔬 "*20)
    print("\nThis pipeline uses THREE specialized AI agents:")
    print("   1. 🔍 Code Reviewer  — finds bugs, security issues, performance problems")
    print("   2. 🧪 Test Writer    — writes pytest tests for each issue found")
    print("   3. 🔧 Code Fixer     — fixes all CRITICAL and WARNING issues")
    print("   4. ✅ Approval Agent — verifies the fix is complete")
    print(f"\nReviewing file: {filename}")
    print(f"Code size: {len(code.splitlines())} lines")

    # Build the pipeline workflow
    app = build_pipeline()

    # Set up the initial state
    initial_state = {
        "original_code": code,    # The code to review
        "filename": filename,      # Filename for display and output naming
        "review": None,            # Will be filled by review_node
        "test_code": None,         # Will be filled by test_node
        "fixed_code": None,        # Will be filled by fix_node
        "approval_status": None,   # Will be filled by approve_node
        "fix_cycles": 0            # Start with 0 fix cycles
    }

    # Run the pipeline
    print("\n⏳ Running code review pipeline... (this may take 60-90 seconds)")
    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("✅ CODE REVIEW PIPELINE COMPLETE!")
    print("="*60)
    print(f"   File: {filename}")
    print(f"   Fix cycles: {final_state.get('fix_cycles', 0)}")
    print(f"   Status: {final_state.get('approval_status', 'Unknown')}")
    print("   Check review_output/ directory for all saved files.")

    return final_state


# ============================================================
# STEP 8: RUN IF EXECUTED DIRECTLY
# ============================================================

if __name__ == "__main__":
    # Check if a file was provided as a command-line argument
    if len(sys.argv) > 1:
        # User provided a Python file path: python code_review_pipeline.py mycode.py
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            # Read the file contents
            with open(filepath, "r", encoding="utf-8") as f:
                code_to_review = f.read()
            # Run the pipeline on the provided file
            run_code_review_pipeline(code_to_review, filename=os.path.basename(filepath))
        else:
            # File does not exist
            print(f"Error: File '{filepath}' not found.")
            print("Usage: python code_review_pipeline.py <python_file.py>")
            sys.exit(1)
    else:
        # No file provided — use the sample buggy code file
        print("No file specified. Using sample_buggy_code.py for demonstration.")
        print("Usage: python code_review_pipeline.py <your_file.py>")
        print()

        # Check if sample file exists
        sample_file = "sample_buggy_code.py"
        if os.path.exists(sample_file):
            with open(sample_file, "r", encoding="utf-8") as f:
                code_to_review = f.read()
            run_code_review_pipeline(code_to_review, filename=sample_file)
        else:
            # Sample file not found — create a minimal example inline
            print("sample_buggy_code.py not found. Using inline example.")
            inline_example = '''
import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = \'" + username + "\'"
    cursor.execute(query)
    return cursor.fetchone()

def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)
'''
            run_code_review_pipeline(inline_example, filename="inline_example.py")
