# Project 6: Multi-Step Task Agent with LangGraph

## Phase 2 — Agents and Tools | Lesson 3 of 3

---

## What You Will Build

An agent that takes a high-level goal, breaks it into a concrete plan, executes each step methodically, evaluates its progress, and compiles a final document — all automatically. You give it "Research Python best practices and create a summary document" and it produces a complete, structured report.

The core teaching point is **LangGraph**: a framework for building stateful, multi-stage AI workflows that go far beyond a simple ReAct loop.

---

## Prerequisites

- Completed Projects 4 and 5 (ReAct agents, custom tools)
- Understanding of the agent loop (Thought → Action → Observation)
- Python 3.9 or higher

---

## Setup

```bash
cd phase2-agents-tools/project6-multi-step-task-agent

pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

python multi_step_agent.py
```

---

## Part 1: The Problem with Simple ReAct Agents

### What Simple ReAct Does Well

The ReAct agents you built in Projects 4 and 5 are excellent for:
- Single-question research tasks
- Simple file operations
- Tasks where you don't know in advance how many steps are needed
- Exploratory, open-ended problems

### Where Simple ReAct Struggles

Try giving a simple ReAct agent a complex multi-stage goal like "Research Python best practices, then write a structured document with sections on naming conventions, error handling, and testing, then create an executive summary."

What often happens:
- The agent rushes to an answer too quickly
- It loses track of what it's already done versus what it still needs to do
- It mixes planning and executing in a messy, unpredictable way
- You cannot inspect the plan or intervene between steps
- There is no clear "done" state

### The LangGraph Solution

LangGraph solves this by letting you define EXPLICIT stages in your workflow. Instead of one loop doing everything, you have distinct nodes:

```
PLAN first
  ↓
EXECUTE each step
  ↓
EVALUATE progress
  ↓ (loop back if more steps)
FINISH when complete
```

Each stage has a clear job, a clear input, and a clear output. The workflow is **transparent** (you can see every stage), **controllable** (you can intervene between stages), and **reliable** (it won't skip steps or forget what it's done).

---

## Part 2: What Is LangGraph?

### The Plain English Version

LangGraph is a library that lets you build AI workflows as **graphs**.

- A **graph** is a set of boxes (nodes) connected by arrows (edges)
- Each **node** is a function that does one thing
- Each **edge** defines which node runs next
- Some edges are **conditional** — they go to different nodes depending on logic

It is exactly like drawing a flowchart, then making that flowchart executable.

### The State Machine Analogy

If you have ever seen a traffic light controller, you have seen a state machine.

```
RED  ──(timer)──→  GREEN  ──(timer)──→  YELLOW  ──(timer)──→  RED
```

The traffic light is always in ONE state (Red, Green, or Yellow). It transitions between states based on rules. The rules are simple: wait X seconds, then move to the next state.

LangGraph is a state machine where:
- The **states** are your nodes (Plan, Execute, Evaluate, Finish)
- The **transitions** are edges (always go here, or conditionally go here/there)
- The **shared data** is the State object (available to all nodes)

The difference from a simple state machine: your transitions can use AI reasoning instead of simple timers.

### Why LangGraph Exists

LangChain's simple ReAct agents (AgentExecutor) are great for simple tasks. But as workflows get more complex, you need:

1. **Explicit state management** — all nodes share a single State object
2. **Cyclical workflows** — loops where you go back to a previous node (execute multiple times)
3. **Conditional branching** — go to node A or node B based on what happened
4. **Parallel execution** — run multiple nodes at the same time (covered in Phase 4)
5. **Human-in-the-loop** — pause the workflow and wait for human input before continuing

LangGraph provides all of these. AgentExecutor provides none of them.

---

## Part 3: Core Concepts

### The State Object

The State is the shared whiteboard for the entire workflow. Every node can read from it and write to it.

```python
class WorkflowState(TypedDict):
    goal: str                    # The user's original goal
    plan: List[str]              # Steps created by plan_node
    current_step_index: int      # Which step we're on
    completed_steps: List[str]   # Steps that are done
    outputs: List[str]           # Content produced for each step
    status: str                  # "planning", "executing", "evaluating", "done"
    error_message: Optional[str] # Any error that occurred
```

This is defined using `TypedDict` — a Python type hint that describes a dictionary with specific keys and types. LangGraph uses this to validate state updates.

### The Annotated List Fields

Notice some fields use `Annotated[List[str], operator.add]`. This is special:

```python
plan: Annotated[List[str], operator.add]
```

`operator.add` for lists means "append, don't replace." When a node returns `{"plan": ["new step"]}`, LangGraph APPENDS "new step" to the existing plan list instead of replacing the whole list.

Without this, every `execute_node` return would wipe out the previous completed steps. With `operator.add`, each return appends to the growing list.

### Nodes

A node is any Python function that:
1. Takes the current State as its only argument
2. Does some work
3. Returns a dictionary of State UPDATES (not the whole State — just the changes)

```python
def my_node(state: WorkflowState) -> dict:
    # 1. Read from state
    goal = state["goal"]

    # 2. Do work
    result = do_something(goal)

    # 3. Return ONLY the fields you want to update
    return {
        "status": "done",
        "outputs": [result],   # Appended to existing outputs list
    }
```

LangGraph automatically merges your return dict into the running State.

### Edges

Edges connect nodes. Two types:

**Simple edges:** Always go from A to B.
```python
workflow.add_edge("plan", "execute")   # After plan, always go to execute
```

**Conditional edges:** Go to A or B based on a routing function.
```python
workflow.add_conditional_edges(
    "evaluate",              # After evaluate...
    route_after_evaluate,    # ...call this function to get the next node name...
    {
        "continue": "execute",  # ...if it returns "continue", go to execute
        "finish": "finish",     # ...if it returns "finish", go to finish
    }
)
```

The routing function simply reads the State and returns a string:
```python
def route_after_evaluate(state: WorkflowState) -> str:
    if state["status"] == "finish":
        return "finish"
    return "continue"
```

### The END Constant

`END` is a special LangGraph constant representing the terminal state. When you route to `END`, the workflow stops and returns the final State.

```python
workflow.add_edge("finish", END)  # After finish, stop the workflow
```

### Compiling and Running

```python
# Build the graph structure
workflow = StateGraph(WorkflowState)
workflow.add_node("plan", plan_node)
# ... add more nodes and edges ...
workflow.set_entry_point("plan")

# Compile into a runnable app
app = workflow.compile()

# Run it — blocks until complete, returns final State
final_state = app.invoke({"goal": "My goal here", "plan": [], ...})
```

---

## Part 4: Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER INPUT                        │
│         "Research Python best practices"             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │       PLAN NODE         │
         │                         │
         │  Asks Claude to break   │
         │  goal into 3-5 steps    │
         │                         │
         │  State.plan = [         │
         │    "Research PEP 8",    │
         │    "Research errors",   │
         │    "Research testing",  │
         │    "Write summary",     │
         │  ]                      │
         └────────────┬────────────┘
                      │ (always)
                      ▼
         ┌─────────────────────────┐
         │      EXECUTE NODE       │◄──────────────────┐
         │                         │                   │
         │  Reads current_step     │                   │
         │  Asks Claude to do it   │                   │
         │  Saves output           │                   │
         │  Increments step index  │                   │
         └────────────┬────────────┘                   │
                      │ (always)                       │
                      ▼                                │
         ┌─────────────────────────┐                   │
         │     EVALUATE NODE       │                   │
         │                         │                   │
         │  Checks: more steps?    │                   │
         │  Sets status:           │                   │
         │    "continue" or        │                   │
         │    "finish"             │     "continue"    │
         └────────────┬────────────┘───────────────────┘
                      │ "finish"
                      ▼
         ┌─────────────────────────┐
         │      FINISH NODE        │
         │                         │
         │  Compiles all outputs   │
         │  Generates summary      │
         │  Saves to .txt file     │
         └────────────┬────────────┘
                      │
                      ▼
                     END
```

---

## Part 5: Code Walkthrough

### Step 1: Define the State

```python
class WorkflowState(TypedDict):
    goal: str
    plan: Annotated[List[str], operator.add]
    current_step_index: int
    completed_steps: Annotated[List[str], operator.add]
    outputs: Annotated[List[str], operator.add]
    status: str
    error_message: Optional[str]
```

The `Annotated[List[str], operator.add]` on `plan`, `completed_steps`, and `outputs` means these lists grow by appending. Every other field is replaced on update.

### Step 2: plan_node

The planning node receives the goal and calls Claude with a prompt asking for a numbered list of steps. It parses the response with a regex to extract clean step descriptions, then returns them as the plan.

Key: the plan is only created once. After `plan_node` runs, the workflow never returns to it.

### Step 3: execute_node (called multiple times)

```python
def execute_node(state: WorkflowState) -> dict:
    current_index = state["current_step_index"]
    current_step = state["plan"][current_index]

    # Build context from completed steps
    # Give Claude the "memory" of what it has already done
    completed_context = ""
    for step, output in zip(state["completed_steps"], state["outputs"]):
        completed_context += f"Step '{step}':\n{output[:300]}...\n"

    # Call Claude to execute the current step
    response = llm.invoke([...])

    return {
        "completed_steps": [current_step],
        "outputs": [formatted_output],
        "current_step_index": current_index + 1,
        "status": "evaluating",
    }
```

The "completed context" passed to Claude is what gives the workflow memory across steps. Step 3 can build on what Steps 1 and 2 produced because execute_node passes them as context.

### Step 4: evaluate_node and Routing

```python
def evaluate_node(state: WorkflowState) -> dict:
    if state["current_step_index"] < len(state["plan"]):
        return {"status": "continue"}
    else:
        return {"status": "finish"}

def route_after_evaluate(state: WorkflowState) -> str:
    return "finish" if state["status"] == "finish" else "continue"
```

These two functions work together. `evaluate_node` sets the status. `route_after_evaluate` reads the status and returns the routing key. LangGraph maps the routing key to the next node.

### Step 5: finish_node

Collects all outputs, asks Claude to write an executive summary, formats a complete document, and saves it to a timestamped `.txt` file.

### Step 6: Assembling the Graph

```python
workflow = StateGraph(WorkflowState)

workflow.add_node("plan", plan_node)
workflow.add_node("execute", execute_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("finish", finish_node)

workflow.set_entry_point("plan")
workflow.add_edge("plan", "execute")
workflow.add_edge("execute", "evaluate")
workflow.add_conditional_edges("evaluate", route_after_evaluate,
    {"continue": "execute", "finish": "finish"})
workflow.add_edge("finish", END)

app = workflow.compile()
```

---

## Part 6: Sample Output

```
============================================================
   MULTI-STEP TASK AGENT
   Powered by LangGraph + Claude
============================================================

Enter your goal: Research Python best practices and create a summary document

============================================================
PHASE 1: PLANNING
============================================================
Goal: Research Python best practices and create a summary document
Claude is breaking this into concrete steps...

Plan created (4 steps):
  1. Research Python naming conventions and PEP 8 standards
  2. Research Python error handling and exception best practices
  3. Research Python testing practices and common frameworks
  4. Write an executive summary and structure the final document

============================================================
STARTING WORKFLOW
============================================================

--- Step 1/4: Research Python naming conventions and PEP 8 standards ---
Working...
Completed: 847 characters generated

[Evaluating: 1/4 steps complete]
[Continuing to step 2: Research Python error handling...]

--- Step 2/4: Research Python error handling and exception best practices ---
Working...
Completed: 912 characters generated

[Evaluating: 2/4 steps complete]
[Continuing to step 3: Research Python testing...]

--- Step 3/4: Research Python testing practices and common frameworks ---
Working...
Completed: 783 characters generated

[Evaluating: 3/4 steps complete]
[Continuing to step 4: Write executive summary...]

--- Step 4/4: Write an executive summary and structure the final document ---
Working...
Completed: 654 characters generated

[Evaluating: 4/4 steps complete]
[All 4 steps complete — moving to final compilation]

============================================================
PHASE 4: COMPILING FINAL DOCUMENT
============================================================
Generating executive summary...

Document saved to: output_research_python_best_practices_20241215_143022.txt

============================================================
FINAL DOCUMENT PREVIEW
============================================================
================================================================================
TASK COMPLETION REPORT
================================================================================
Goal: Research Python best practices and create a summary document
Generated: 2024-12-15 14:30
Steps Completed: 4
================================================================================

EXECUTIVE SUMMARY
-----------------
Python best practices center around readability, consistency, and
maintainability. PEP 8 provides the foundational style guide, while
proper error handling, comprehensive testing with pytest, and clean
code organization ensure robust, professional Python codebases. These
practices significantly improve collaboration and long-term code quality.

[... document continues ...]
```

---

## Part 7: LangGraph vs. Simple ReAct — Side by Side

| Feature | Simple ReAct (Projects 4 & 5) | LangGraph (This Project) |
|---------|------------------------------|--------------------------|
| Structure | One loop, improvised | Explicit stages (nodes) |
| State | Implicit (scratchpad) | Explicit (TypedDict) |
| Progress tracking | Not visible | Transparent at each node |
| Looping | Auto (until Final Answer) | Explicit (conditional edges) |
| Intervene between steps | Not possible | Yes (pause before any node) |
| Good for | Open-ended tasks | Structured multi-stage tasks |
| Complexity | Low | Medium |
| Predictability | Lower | Higher |

Neither is "better" — they are tools for different jobs. Experienced engineers use both, choosing based on the problem.

---

## Part 8: Real World Use Cases

### 1. Automated Incident Response

```
Goal: "Investigate the high error rate on the payments API"

Plan:
  Step 1: Query logs for errors in the last hour
  Step 2: Identify the most common error types
  Step 3: Check recent deployments and config changes
  Step 4: Generate incident report with root cause hypothesis
  Step 5: Create Jira ticket and notify on-call team
```

Each step uses custom tools (log queries, Jira API, Slack). LangGraph ensures each step completes before the next starts, and the final step always runs even if earlier steps find nothing.

### 2. Content Generation Pipeline

```
Goal: "Write a blog post about Kubernetes 1.30 new features"

Plan:
  Step 1: Research Kubernetes 1.30 release notes
  Step 2: Identify top 5 most impactful features for DevOps teams
  Step 3: Write technical explanation for each feature
  Step 4: Write introduction and conclusion
  Step 5: Generate SEO metadata and tags
```

### 3. Code Review Automation

```
Goal: "Review the pull request #247 for code quality"

Plan:
  Step 1: Fetch the diff from GitHub API
  Step 2: Check for security vulnerabilities
  Step 3: Check for test coverage gaps
  Step 4: Check for code style issues
  Step 5: Generate review summary and post comment
```

### 4. Customer Onboarding

```
Goal: "Onboard new customer Acme Corp"

Plan:
  Step 1: Create account in billing system
  Step 2: Provision cloud resources
  Step 3: Configure SSO and access controls
  Step 4: Send welcome email with credentials
  Step 5: Create Slack channel and invite team
```

---

## Part 9: Extend This Project

### Idea 1: Add Web Search to Execute Steps

Combine Projects 4 and 6. Use Tavily search in the `execute_node` to gather real information for each step:

```python
from langchain_community.tools.tavily_search import TavilySearchResults

search = TavilySearchResults(max_results=2)

def execute_node(state: WorkflowState) -> dict:
    current_step = state["plan"][state["current_step_index"]]

    # Search for information relevant to this step
    search_results = search.invoke(current_step)
    search_context = "\n".join([r["content"] for r in search_results])

    # Pass search results to Claude along with the step
    messages = [
        SystemMessage(content="Use these search results to complete the step."),
        HumanMessage(content=f"Step: {current_step}\n\nSearch Results:\n{search_context}")
    ]
    response = llm.invoke(messages)
    # ...
```

### Idea 2: Human-in-the-Loop Approval

Add a node that pauses after planning and asks the human to approve or edit the plan before execution starts:

```python
def human_approval_node(state: WorkflowState) -> dict:
    print("\nPROPOSED PLAN:")
    for i, step in enumerate(state["plan"], 1):
        print(f"  {i}. {step}")

    approval = input("\nApprove this plan? (yes/edit/cancel): ").strip().lower()

    if approval == "cancel":
        return {"status": "cancelled"}
    elif approval == "edit":
        # Let user modify steps
        # ...
        return {"plan": new_steps, "status": "approved"}
    else:
        return {"status": "approved"}
```

### Idea 3: Parallel Step Execution

For steps that don't depend on each other, run them in parallel using LangGraph's `Send` API. This dramatically speeds up multi-step workflows.

---

## Part 10: What You Learned

**LangGraph Architecture**
- What a StateGraph is (a directed graph of nodes and edges)
- How State flows through the entire workflow (shared TypedDict)
- How `Annotated[List, operator.add]` enables append-only list updates

**Nodes and Edges**
- Nodes are functions: take State, return State updates
- Simple edges always go from A to B
- Conditional edges use a routing function to choose the destination

**Multi-Stage Workflow Design**
- Plan → Execute → Evaluate → Finish as a complete workflow pattern
- The execute/evaluate loop for processing list items one by one
- How context from previous steps flows into subsequent steps

**The Comparison**
- When to use simple ReAct (open-ended, exploratory, low structure)
- When to use LangGraph (structured pipeline, explicit stages, auditability needed)

---

## Part 11: Quiz

**Question 1:** In a LangGraph workflow, what does `Annotated[List[str], operator.add]` do that plain `List[str]` does not?

<details>
<summary>Click to reveal answer</summary>

`Annotated[List[str], operator.add]` tells LangGraph to use the `operator.add` function when merging state updates for that field. For lists, `operator.add` performs list concatenation (appending), not replacement. This means when a node returns `{"completed_steps": ["step 1"]}`, LangGraph APPENDS "step 1" to the existing completed_steps list. Without this annotation, each node's return would REPLACE the entire list, causing previously completed steps to be lost.

</details>

---

**Question 2:** What is the purpose of passing `completed_context` to Claude in `execute_node`? What would happen without it?

<details>
<summary>Click to reveal answer</summary>

`completed_context` passes a summary of all previously completed steps and their outputs to Claude when executing the current step. This gives Claude "memory" within the workflow — it knows what has already been researched or written so it can build on it coherently. Without it, each step would be executed in isolation. Step 4 (writing a document) would have no knowledge of what Steps 1-3 found, leading to generic content that doesn't actually synthesize the earlier research.

</details>

---

**Question 3:** You want to add a node that runs between `plan` and `execute` to let a human approve the plan before work begins. What two changes would you need to make to the graph?

<details>
<summary>Click to reveal answer</summary>

Two changes are needed:

1. Add the new node: `workflow.add_node("human_approval", human_approval_node)` — this registers the function as a node in the graph.

2. Update the edges: Change `workflow.add_edge("plan", "execute")` to `workflow.add_edge("plan", "human_approval")`, then add `workflow.add_edge("human_approval", "execute")`. Or, if the human can cancel, use a conditional edge from `human_approval` that routes to `execute` on approval and to `END` on cancellation.

The node itself would be a function that displays the plan, gets user input, and returns a state update (possibly modifying the plan if the human edits it).

</details>

---

## Vocabulary Reference

| Term | Plain English Definition |
|------|--------------------------|
| LangGraph | A library for building stateful, multi-stage AI workflows as graphs |
| StateGraph | The main LangGraph class — a graph you add nodes and edges to |
| State | The shared data object that all nodes read from and write to |
| TypedDict | A Python dict with declared field names and types (used to define State) |
| Node | A function in the graph that reads State, does work, and returns updates |
| Edge | A connection between nodes defining which runs next |
| Conditional edge | An edge that routes to different nodes based on a routing function |
| END | A LangGraph constant — routing to END stops the workflow |
| operator.add | Python's addition function — for lists, performs append (used in Annotated) |
| Routing function | A function that reads State and returns a string key to select the next node |
| Entry point | The first node that runs when the workflow starts |
| compile() | Validates and "locks" the graph into a runnable app |

---

*Phase 2 Complete! Next: Phase 3 — Memory and Context (Persistent Agents)*
