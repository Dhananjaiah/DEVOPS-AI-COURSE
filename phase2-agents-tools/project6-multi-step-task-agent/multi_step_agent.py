"""
=============================================================================
PROJECT 6: Multi-Step Task Agent with LangGraph
=============================================================================

WHAT THIS FILE TEACHES:
    - What LangGraph is and why it exists (beyond simple ReAct agents)
    - What a StateGraph is (a graph of nodes connected by edges)
    - How to define and share State across an entire workflow
    - How to write individual node functions (each does one job)
    - How conditional routing works (branching logic between nodes)
    - How to build a complete plan → execute → evaluate → finish pipeline

THE KEY UPGRADE FROM PROJECTS 4 & 5:
    Projects 4 and 5 used a single ReAct loop.
    The agent would improvise each step on the fly.

    Project 6 uses a STRUCTURED WORKFLOW:
    1. PLAN: First break the goal into concrete steps
    2. EXECUTE: Work through each step one at a time
    3. EVALUATE: Check if all steps are done
    4. FINISH: Compile and save the final output

    This is like the difference between:
    - Winging it and figuring things out as you go (simple ReAct)
    - Writing a project plan first, then executing it methodically (LangGraph)

BEFORE YOU RUN:
    1. Copy .env.example to .env
    2. Add your ANTHROPIC_API_KEY to .env
    3. pip install -r requirements.txt
    4. python multi_step_agent.py

=============================================================================
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------

# Standard library
import os           # File system operations
import sys          # Program exit
import json         # JSON parsing (for Claude's structured responses)
import re           # Regular expressions (for cleaning up text)
from datetime import datetime  # Timestamps for output filenames

# dotenv: loads .env file variables into environment
from dotenv import load_dotenv

# ChatAnthropic: LangChain's Claude wrapper
from langchain_anthropic import ChatAnthropic

# HumanMessage, SystemMessage: Message types for building prompts
# LangGraph works best when we construct messages explicitly
from langchain_core.messages import HumanMessage, SystemMessage

# ---------------------------------------------------------------------------
# LANGGRAPH IMPORTS — The Key New Concepts
# ---------------------------------------------------------------------------
#
# StateGraph: The main LangGraph class. You build a graph by adding nodes
#             and edges to it, then compiling it into a runnable workflow.
#
# END:        A special constant representing the terminal node.
#             When you route to END, the workflow stops.
#
# Annotated:  From Python's typing module — used to annotate state fields
#             with special behaviors (like "always append to this list")
#
# TypedDict:  Used to define the structure of the shared State object.
#             Think of it as a typed Python dictionary.

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
import operator  # operator.add is used for list fields that append

# ---------------------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment.")
    print("Did you copy .env.example to .env and add your key?")
    sys.exit(1)

# ---------------------------------------------------------------------------
# INITIALIZE THE LLM
# ---------------------------------------------------------------------------

# temperature=0.3: slightly higher than research tasks — we want creativity
# in planning but still mostly factual in execution
llm = ChatAnthropic(
    model="claude-opus-4-6",
    anthropic_api_key=ANTHROPIC_API_KEY,
    temperature=0.3,
    max_tokens=4096,
)

# ---------------------------------------------------------------------------
# STATE DEFINITION — The Heart of LangGraph
# ---------------------------------------------------------------------------
#
# In a LangGraph workflow, ALL nodes share a single "State" object.
# Every node:
#   1. READS from the State to know what's been done so far
#   2. DOES its work
#   3. RETURNS a dictionary with UPDATES to the State
#
# The State is like the shared whiteboard for the whole workflow.
# Every node can see everything written on the whiteboard.
#
# We define the State using TypedDict — a dictionary with specific typed fields.

class WorkflowState(TypedDict):
    """
    The shared state that flows through the entire LangGraph workflow.

    Every node receives this state as input and returns a partial update.
    LangGraph merges the update into the running state automatically.
    """

    # The original high-level goal provided by the user
    # e.g., "Research Python best practices and create a summary document"
    goal: str

    # The list of concrete steps created by the plan_node
    # Each item is a string describing one step
    # e.g., ["Research Python naming conventions", "Research error handling", ...]
    # Annotated with operator.add means: when a node returns a new plan list,
    # LangGraph APPENDS it to the existing list (not replaces)
    plan: Annotated[List[str], operator.add]

    # Index of the step currently being executed (0-based)
    # e.g., 0 = first step, 1 = second step, etc.
    current_step_index: int

    # List of step descriptions that have been completed
    # Used by evaluate_node to check progress
    completed_steps: Annotated[List[str], operator.add]

    # List of text outputs produced for each completed step
    # These get compiled into the final document
    outputs: Annotated[List[str], operator.add]

    # Workflow status: "planning", "executing", "evaluating", "done", "error"
    # Used for progress display and routing decisions
    status: str

    # Optional error message if something goes wrong
    error_message: Optional[str]

# ---------------------------------------------------------------------------
# NODE 1: plan_node
# ---------------------------------------------------------------------------
#
# WHAT IS A NODE?
# A node is a function that takes the current State and returns State updates.
# It does ONE thing in the workflow — this node's job is to create the plan.
#
# The plan_node:
#   1. Reads the goal from State
#   2. Asks Claude to break it into 3-5 concrete steps
#   3. Returns the plan list as a State update

def plan_node(state: WorkflowState) -> dict:
    """
    Node 1: Takes the user's high-level goal and breaks it into concrete steps.

    This is the PLANNING phase. We ask Claude to think about the goal
    and produce a numbered list of specific, actionable steps.

    Returns: State updates containing the plan list and updated status.
    """

    goal = state["goal"]  # Read the goal from shared state

    print("\n" + "="*60)
    print("PHASE 1: PLANNING")
    print("="*60)
    print(f"Goal: {goal}")
    print("Claude is breaking this into concrete steps...")

    # Build the prompt asking Claude to create a plan
    messages = [
        SystemMessage(content="""You are a project planning assistant.
Your job is to break down a high-level goal into 3-5 concrete, specific, actionable steps.

Rules:
- Each step should be completable on its own
- Steps should be in logical order (each one builds on previous)
- Steps should be specific and clear (not vague)
- Return ONLY a numbered list, nothing else

Example format:
1. Research current Python naming convention standards from PEP 8
2. Gather examples of good vs. bad naming conventions
3. Research Python error handling best practices
4. Write a section on code organization and project structure
5. Compile all findings into a structured document"""),

        HumanMessage(content=f"Create a step-by-step plan to accomplish this goal:\n\n{goal}")
    ]

    # Call Claude to generate the plan
    response = llm.invoke(messages)
    plan_text = response.content

    # Parse the numbered list into individual steps
    # We use a regex to find lines starting with "1.", "2.", etc.
    steps = []
    for line in plan_text.strip().split("\n"):
        line = line.strip()
        # Match patterns like "1. Step description" or "1) Step description"
        match = re.match(r"^\d+[.)]\s+(.+)$", line)
        if match:
            step_text = match.group(1).strip()  # Extract just the step text (no number)
            if step_text:
                steps.append(step_text)

    # Fallback: if parsing failed, split on newlines and clean up
    if not steps:
        steps = [line.strip() for line in plan_text.split("\n")
                 if line.strip() and not line.strip().isdigit()]
        steps = steps[:5]  # Limit to 5 steps max

    print(f"\nPlan created ({len(steps)} steps):")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")

    # Return updates to State
    # LangGraph merges these into the running State automatically
    return {
        "plan": steps,          # The list of steps (appended to plan field)
        "current_step_index": 0, # Start at step 0 (first step)
        "status": "executing",   # Move to executing phase
    }

# ---------------------------------------------------------------------------
# NODE 2: execute_node
# ---------------------------------------------------------------------------
#
# The execute_node:
#   1. Reads the current step from State (using current_step_index)
#   2. Asks Claude to actually DO that step (produce content for it)
#   3. Returns the output and updates the progress
#
# This node runs REPEATEDLY — once for each step in the plan.
# It's the worker node. After each execution, evaluate_node decides
# whether to run it again (more steps) or move on.

def execute_node(state: WorkflowState) -> dict:
    """
    Node 2: Executes a single step from the plan.

    This node is called multiple times — once per step.
    Each time, it reads which step to execute (current_step_index),
    asks Claude to produce content for that step, and saves the output.

    Returns: State updates with the completed step output and updated index.
    """

    plan = state["plan"]                      # The full plan list
    current_index = state["current_step_index"]  # Which step we're on now
    goal = state["goal"]                       # The original goal (for context)

    # Safety check: make sure we haven't gone past the end of the plan
    if current_index >= len(plan):
        return {"status": "evaluating"}

    current_step = plan[current_index]  # The step description we're executing
    step_number = current_index + 1     # Human-readable step number (1-based)
    total_steps = len(plan)

    print(f"\n--- Step {step_number}/{total_steps}: {current_step} ---")
    print("Working...")

    # Build the context from steps already completed
    # This gives Claude the "project memory" — it knows what's already been done
    completed_context = ""
    if state.get("completed_steps") and state.get("outputs"):
        completed_context = "\n\nWork completed so far:\n"
        for step, output in zip(state["completed_steps"], state["outputs"]):
            # Include a snippet of previous outputs (first 300 chars) for context
            output_preview = output[:300] + "..." if len(output) > 300 else output
            completed_context += f"\nStep '{step}':\n{output_preview}\n"

    # Ask Claude to execute this specific step
    messages = [
        SystemMessage(content=f"""You are an AI assistant executing a specific step in a larger project.

The overall goal is: {goal}

You are executing step {step_number} of {total_steps}.
{completed_context}

For this step, provide detailed, high-quality content.
Write in a clear, professional style suitable for a technical document.
Aim for 150-300 words of substantive content.
Do NOT include step numbers or meta-commentary — just the content itself."""),

        HumanMessage(content=f"Execute this step and provide the content:\n\n{current_step}")
    ]

    # Call Claude to generate the content for this step
    response = llm.invoke(messages)
    step_output = response.content.strip()

    # Format the output section with a header
    formatted_output = f"## {current_step}\n\n{step_output}"

    print(f"Completed: {len(step_output)} characters generated")

    # Return State updates:
    # - completed_steps: add this step to the completed list (appended via operator.add)
    # - outputs: add this step's content to the outputs list
    # - current_step_index: advance to the next step
    # - status: signal that we should evaluate progress
    return {
        "completed_steps": [current_step],    # Will be APPENDED to existing list
        "outputs": [formatted_output],         # Will be APPENDED to existing list
        "current_step_index": current_index + 1,  # Next step index
        "status": "evaluating",               # Trigger evaluation
    }

# ---------------------------------------------------------------------------
# NODE 3: evaluate_node
# ---------------------------------------------------------------------------
#
# The evaluate_node doesn't do work — it makes a ROUTING DECISION.
# It reads the State and returns a routing key ("continue" or "finish")
# that LangGraph uses to decide which node comes next.
#
# This is called "conditional routing" — the workflow branches based on logic.

def evaluate_node(state: WorkflowState) -> dict:
    """
    Node 3: Checks if all steps are complete.

    This node examines the State to determine if the execute_node should
    run again (more steps remaining) or if we're done and should finish.

    It does NOT generate content — it just sets the status for routing.

    Returns: State update with routing status ("continue" or "finish").
    """

    plan = state["plan"]
    completed_steps = state.get("completed_steps", [])
    current_index = state["current_step_index"]

    # Count how many steps are done vs. total
    completed_count = len(completed_steps)
    total_steps = len(plan)

    print(f"\n[Evaluating: {completed_count}/{total_steps} steps complete]")

    # Decision: are there more steps to do?
    if current_index < total_steps:
        # More steps remaining — signal to continue executing
        print(f"[Continuing to step {current_index + 1}: {plan[current_index]}]")
        return {"status": "continue"}
    else:
        # All steps done — signal to finish
        print(f"[All {total_steps} steps complete — moving to final compilation]")
        return {"status": "finish"}

# ---------------------------------------------------------------------------
# ROUTING FUNCTION — The Decision Logic for Conditional Edges
# ---------------------------------------------------------------------------
#
# A "conditional edge" in LangGraph is an edge that goes to different nodes
# based on a function's return value.
#
# This function reads the State and returns a string:
#   "continue" → route back to execute_node (more work to do)
#   "finish"   → route to finish_node (all done)
#
# We'll connect this to the graph with add_conditional_edges() below.

def route_after_evaluate(state: WorkflowState) -> str:
    """
    Routing function called after evaluate_node.

    Reads the status field in State to decide where to go next.
    Returns a string that LangGraph uses to pick the next node.
    """
    status = state.get("status", "continue")

    if status == "finish":
        return "finish"   # Go to finish_node
    else:
        return "continue" # Go back to execute_node

# ---------------------------------------------------------------------------
# NODE 4: finish_node
# ---------------------------------------------------------------------------
#
# The finish_node:
#   1. Collects all the outputs from each step
#   2. Compiles them into a final document
#   3. Saves the document to a .txt file
#   4. Returns the final status

def finish_node(state: WorkflowState) -> dict:
    """
    Node 4: Compiles all step outputs into a final document and saves it.

    This is the last node in the workflow. It takes all the individual
    step outputs, arranges them into a complete document, and saves
    the result to a timestamped .txt file.

    Returns: State updates marking the workflow as done.
    """

    goal = state["goal"]
    outputs = state.get("outputs", [])
    completed_steps = state.get("completed_steps", [])

    print("\n" + "="*60)
    print("PHASE 4: COMPILING FINAL DOCUMENT")
    print("="*60)

    # Ask Claude to write an executive summary for the entire document
    print("Generating executive summary...")

    # Summarize all the output content
    all_content = "\n\n".join(outputs)

    messages = [
        SystemMessage(content="You are a technical writer. Write a concise executive summary."),
        HumanMessage(content=f"""Based on this research and work done on the goal:
"{goal}"

Content produced:
{all_content[:2000]}...

Write a 3-4 sentence executive summary that captures the key takeaways.
Return ONLY the summary text, no labels or headers.""")
    ]

    summary_response = llm.invoke(messages)
    executive_summary = summary_response.content.strip()

    # Build the complete document
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    document = f"""================================================================================
TASK COMPLETION REPORT
================================================================================
Goal: {goal}
Generated: {timestamp}
Steps Completed: {len(completed_steps)}
================================================================================

EXECUTIVE SUMMARY
-----------------
{executive_summary}

================================================================================
DETAILED FINDINGS
================================================================================

"""

    # Append each step's output to the document
    for i, output in enumerate(outputs, 1):
        document += f"{output}\n\n"
        document += "-" * 60 + "\n\n"

    # Add a completion footer
    document += f"""================================================================================
END OF REPORT
Generated by Multi-Step Task Agent | {timestamp}
================================================================================
"""

    # Save to file
    # Create a filename from the first 40 characters of the goal
    safe_goal = re.sub(r'[^a-zA-Z0-9\s]', '', goal)[:40].strip()
    safe_goal = safe_goal.replace(" ", "_").lower()
    filename = f"output_{safe_goal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(document)
        print(f"\nDocument saved to: {filename}")
    except Exception as e:
        print(f"\nWarning: Could not save file: {e}")
        filename = None

    # Print a preview of the document
    print("\n" + "="*60)
    print("FINAL DOCUMENT PREVIEW")
    print("="*60)
    print(document[:1500])
    if len(document) > 1500:
        print(f"\n... [Document continues — {len(document)} total characters] ...")

    return {
        "status": "done",
    }

# ---------------------------------------------------------------------------
# BUILD THE LANGGRAPH STATE GRAPH
# ---------------------------------------------------------------------------
#
# Now we assemble the nodes into a graph.
# Think of it like drawing a flowchart — nodes are boxes, edges are arrows.
#
# Our workflow:
#
#  START → plan_node → execute_node → evaluate_node ─┐
#                           ↑                         │ (if more steps)
#                           └─────────────────────────┘
#                                                     │ (if done)
#                                                     ▼
#                                               finish_node → END

def build_workflow() -> StateGraph:
    """
    Assembles the LangGraph StateGraph with all nodes and edges.

    Returns a compiled, runnable workflow.
    """

    # Create the StateGraph, telling it what our State schema looks like
    # WorkflowState defines all the fields and their types
    workflow = StateGraph(WorkflowState)

    # ---------------------------------------------------------------------------
    # ADD NODES
    # ---------------------------------------------------------------------------
    # workflow.add_node(name, function)
    # name: the string identifier for this node (used in edges)
    # function: the Python function to run when this node is activated

    workflow.add_node("plan", plan_node)         # Node that creates the plan
    workflow.add_node("execute", execute_node)   # Node that executes one step
    workflow.add_node("evaluate", evaluate_node) # Node that checks progress
    workflow.add_node("finish", finish_node)     # Node that compiles results

    # ---------------------------------------------------------------------------
    # ADD EDGES
    # ---------------------------------------------------------------------------
    # Edges define which node runs after which.
    # workflow.add_edge(from_node, to_node)

    # Set the entry point: when the workflow starts, run "plan" first
    workflow.set_entry_point("plan")

    # After planning, always go to execute
    workflow.add_edge("plan", "execute")

    # After executing, always go to evaluate
    workflow.add_edge("execute", "evaluate")

    # After evaluate, CONDITIONALLY go to execute OR finish
    # add_conditional_edges takes:
    #   1. The source node
    #   2. The routing function (returns a string key)
    #   3. A mapping from string keys to destination nodes
    workflow.add_conditional_edges(
        "evaluate",              # Source: after evaluate_node runs...
        route_after_evaluate,    # ...call this function to get the routing key...
        {
            "continue": "execute",  # ...if key is "continue", go back to execute
            "finish": "finish",     # ...if key is "finish", go to finish
        }
    )

    # After finish, end the workflow
    workflow.add_edge("finish", END)

    # Compile the graph into a runnable app
    # compile() validates the graph structure and returns a runnable object
    app = workflow.compile()

    return app

# ---------------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------------

def run_multi_step_agent():
    """
    Main function: gets a goal from the user, runs the LangGraph workflow,
    and saves the output.
    """

    print("\n" + "="*60)
    print("   MULTI-STEP TASK AGENT")
    print("   Powered by LangGraph + Claude")
    print("="*60)
    print("\nThis agent will:")
    print("  Phase 1 (PLAN):     Break your goal into concrete steps")
    print("  Phase 2 (EXECUTE):  Work through each step one by one")
    print("  Phase 3 (EVALUATE): Check if all steps are complete")
    print("  Phase 4 (FINISH):   Compile everything into a final document")
    print("\nExample goals:")
    print("  - 'Research Python best practices and create a summary document'")
    print("  - 'Create a beginner guide to Docker containers'")
    print("  - 'Write a comparison of SQL vs NoSQL databases'")
    print("  - 'Create a study guide for Kubernetes concepts'")
    print("-"*60)

    # Get the goal from the user
    goal = input("\nEnter your goal: ").strip()

    if not goal:
        goal = "Research Python best practices and create a comprehensive summary document"
        print(f"Using default goal: '{goal}'")

    print(f"\nStarting workflow for: '{goal}'")

    # Build the workflow graph
    app = build_workflow()

    # Create the initial State
    # We only need to provide the fields we're initializing
    # LangGraph fills in the rest with defaults (empty lists, None values)
    initial_state = {
        "goal": goal,
        "plan": [],            # Empty — plan_node will fill this in
        "current_step_index": 0,
        "completed_steps": [], # Empty — execute_node will fill this in
        "outputs": [],         # Empty — execute_node will fill this in
        "status": "planning",  # Initial status
        "error_message": None,
    }

    # ---------------------------------------------------------------------------
    # RUN THE WORKFLOW
    # ---------------------------------------------------------------------------
    #
    # app.invoke() runs the entire graph from start to END.
    # It blocks until the workflow completes (all nodes have run to completion).
    # It returns the final State after the last node.

    try:
        print("\n" + "="*60)
        print("STARTING WORKFLOW")
        print("="*60)

        final_state = app.invoke(initial_state)

        # Print final statistics
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Goal:        {goal}")
        print(f"Steps:       {len(final_state.get('completed_steps', []))}")
        print(f"Status:      {final_state.get('status', 'unknown')}")

    except KeyboardInterrupt:
        print("\n\nWorkflow cancelled by user.")
    except Exception as e:
        print(f"\nERROR: Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_multi_step_agent()
