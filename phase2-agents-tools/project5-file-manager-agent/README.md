# Project 5: File Manager Agent — Building Custom Tools

## Phase 2 — Agents and Tools | Lesson 2 of 3

---

## What You Will Build

A file management agent that takes natural language commands and executes file operations. You say "Create a project structure with src, tests, and docs folders, and put a README in each one" — and it does exactly that, using five custom tools you built yourself.

The core teaching point is not the file management. It is **how to build your own tools** and wire them into an agent.

---

## Prerequisites

- Completed Project 4 (Web Research Agent)
- Understanding of the ReAct pattern (Thought → Action → Observation loop)
- Python 3.9 or higher

---

## Setup

```bash
cd phase2-agents-tools/project5-file-manager-agent

pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

python file_manager_agent.py
```

---

## Part 1: Pre-built Tools vs. Custom Tools

### What You Did in Project 4

In Project 4, you used `TavilySearchResults` — a tool that someone else wrote. You imported it and plugged it in. That is powerful and fast, but it only works for use cases that someone has already built a tool for.

### The Real World Problem

Imagine you work at a company and you want to build an agent that can:
- Query your internal PostgreSQL database
- Create tickets in your Jira instance
- Deploy a new version via your internal deploy script
- Send a notification to your team's Slack channel

None of these have pre-built LangChain tools. You need to write them yourself.

That is what this project teaches. The `@tool` decorator lets you turn ANY Python function into an agent tool.

---

## Part 2: The @tool Decorator — How It Works

A decorator in Python is the `@something` that appears above a function definition. It modifies or "wraps" the function.

When you write this:

```python
from langchain.tools import tool

@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file and return them as a string.
    Use this when you need to see what is inside a file.
    """
    with open(file_path, "r") as f:
        return f.read()
```

LangChain does three things automatically:

1. **Registers it as a tool** — it becomes part of the tools registry
2. **Uses the function name as the tool name** — `read_file` is what the agent writes in "Action: read_file"
3. **Uses the docstring as the tool description** — this is what the agent reads to know what the tool does

The agent NEVER sees the function body. It only sees:
- The name: `read_file`
- The description: "Read the contents of a file and return them as a string. Use this when you need to see what is inside a file."

---

## Part 3: Why Docstrings Are Critical

This is the most important concept in this project.

### The Agent's Perspective

When the agent is deciding what to do, it reads a list that looks like this (generated automatically from your tools):

```
read_file: Read the contents of a file and return them as a string.
           Use this when you need to see what is inside a file.
           The file_path should be relative to the workspace.

write_file: Write content to a file, creating it if it doesn't exist.
            Use this when you need to create a new file or update an existing one.
            The file_path should be relative to the workspace.
            The content parameter is the text to write.

list_files: List all files and subdirectories inside a directory.
            Use this when you need to see what files exist.
            Pass '.' to list the root workspace directory.

create_directory: Create a new directory inside the workspace.
                  Use this when you need to organize files into subdirectories.

delete_file: Delete a file from the workspace permanently.
             Use ONLY when explicitly asked to delete a file.
             WARNING: This action cannot be undone.
```

The agent makes its decisions entirely from these descriptions. It reasons: "The user wants to read a file. The `read_file` tool says it reads files. I should use `read_file`."

### The Docstring Rules

**Rule 1: Say WHAT the tool does.**
Bad: `"""File reading utility."""`
Good: `"""Read the contents of a file and return them as a string."""`

**Rule 2: Say WHEN to use it.**
Bad: `"""Reads file contents."""`
Good: `"""Use this when you need to see what is inside a file."""`

**Rule 3: Describe the parameters.**
Bad: `"""Takes a file path."""`
Good: `"""The file_path should be relative to the workspace (e.g., 'notes.txt' or 'subdir/data.txt')."""`

**Rule 4: Warn about side effects or dangers.**
The `delete_file` docstring says "WARNING: This action cannot be undone." This discourages the agent from deleting things accidentally.

**Rule 5: Be specific about what NOT to do.**
The `delete_file` docstring says "Do NOT use this unless the user clearly wants the file deleted." This grounding instruction prevents accidental deletions.

### An Experiment You Can Try

Change the `delete_file` docstring to: `"""Removes a file."""`

Then ask the agent to "clean up the workspace." It may start deleting everything because the vague description gives no guidance on when not to use the tool. The docstring is the agent's constraint.

---

## Part 4: The Grounding Concept — Safety by Design

### What Is Grounding?

Grounding means limiting what an agent can do to a safe, controlled scope. An ungrounded file manager agent could theoretically:
- Delete system files
- Read your `.env` file with API keys
- Overwrite important configuration files

This is not theoretical. In 2023, several AI agent demos caused chaos by operating outside their intended scope.

### Our Safety Approach: The Workspace Directory

Every tool in this project checks that the target path is inside `./workspace/` before doing anything. This check uses a helper function:

```python
WORKSPACE_DIR = os.path.abspath("./workspace")

def is_safe_path(path: str) -> tuple[bool, str]:
    if not os.path.isabs(path):
        absolute_path = os.path.join(WORKSPACE_DIR, path)
    else:
        absolute_path = path

    real_path = os.path.realpath(absolute_path)

    if not real_path.startswith(os.path.realpath(WORKSPACE_DIR)):
        return False, "SAFETY ERROR: Path is outside the workspace."

    return True, real_path
```

The key is `os.path.realpath()`. This resolves tricks like `../../etc/passwd` to their true absolute paths. Without this, a path traversal attack could escape the sandbox.

### Grounding at Multiple Levels

This project shows two levels of grounding:

1. **Code-level grounding** — the tools themselves check safety. Even if the agent tries to use them outside the workspace, the functions refuse.

2. **Prompt-level grounding** — the system prompt tells the agent: "You can ONLY operate on files within the workspace directory." This stops the agent from even trying.

Both levels are needed. Code-level grounding is the hard stop. Prompt-level grounding prevents the agent from wasting time trying things that will fail.

---

## Part 5: Code Walkthrough

### Tool Definition Pattern

Every custom tool follows this template:

```python
@tool
def tool_name(param1: type, param2: type) -> str:
    """
    What this tool does.
    When to use this tool.
    What the parameters mean.
    What it returns.
    Any warnings or constraints.
    """
    # 1. Safety check
    is_safe, result = is_safe_path(param1)
    if not is_safe:
        return result  # Return error message as string

    # 2. Validate inputs
    if not os.path.exists(result):
        return "ERROR: File does not exist."

    # 3. Do the actual work
    try:
        # ... do the thing ...
        return "SUCCESS: ..."
    except Exception as e:
        return f"ERROR: {str(e)}"
```

Note that tools ALWAYS return strings. The agent receives the return value as the "Observation" text. Error conditions are returned as error strings, not raised as exceptions. This keeps the agent loop running — it can read the error and decide what to do next.

### The Tools We Built

```
read_file(file_path)         → reads file, returns content as string
write_file(file_path, content) → writes content to file, returns status
list_files(directory)        → lists directory contents, returns formatted string
create_directory(dir_path)   → creates directory, returns status
delete_file(file_path)       → deletes file, returns status (with warning in docstring)
```

### Assembling the Agent

```python
tools = [read_file, write_file, list_files, create_directory, delete_file]

agent = create_react_agent(llm=llm, tools=tools, prompt=FILE_MANAGER_PROMPT)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=15,   # Higher than Project 4 — multi-step file tasks need more iterations
)
```

The only difference from Project 4 is the tools list. Everything else is the same pattern. This is the power of the tool abstraction — you swap in new tools and the framework handles the rest.

### The Interactive Loop

```python
while True:
    command = input("What would you like to do? > ").strip()
    if command.lower() in ("quit", "exit", "q"):
        break
    result = agent_executor.invoke({"input": command})
    print(result["output"])
```

A simple while loop keeps the agent running until the user types "quit". Each command is a fresh agent invocation — the agent doesn't remember previous commands (stateless invocations). We add memory in Phase 3.

---

## Part 6: How the Agent Chooses Tools

Here is a trace of what happens when you type:
"Create a folder called reports and put a file called summary.txt in it with the text Analysis complete."

```
Thought: I need to create a folder first, then write a file into it.
         I'll use create_directory for the folder.
Action: create_directory
Action Input: reports
Observation: Successfully created directory 'reports'.

Thought: Now I need to create the file inside the reports directory.
         I'll use write_file with the path 'reports/summary.txt'.
Action: write_file
Action Input: {"file_path": "reports/summary.txt", "content": "Analysis complete."}
Observation: Successfully wrote 1 line(s) to 'reports/summary.txt'.

Thought: Both tasks are done. Let me verify by listing the reports directory.
Action: list_files
Action Input: reports
Observation: Contents of 'reports':
  [FILE] summary.txt (17 bytes)
  Total: 0 directories, 1 file(s)

Thought: The folder and file were created successfully.
Final Answer: Done! I created the 'reports' folder and placed 'summary.txt' inside it
              with the text "Analysis complete." The file is 17 bytes.
```

Notice three things:
1. The agent reasoned that folder creation must come before file creation
2. It used the correct tool for each step based on the docstrings
3. It voluntarily verified its work with `list_files` before finishing

You did not tell it to verify. The system prompt says "verify your work." It followed that instruction.

---

## Part 7: Sample Session

```
============================================================
   FILE MANAGER AGENT
   Powered by Claude + Custom LangChain Tools
============================================================

Workspace: /home/user/project5-file-manager-agent/workspace

What would you like to do? > Show me what's in the workspace

> Entering new AgentExecutor chain...
Thought: The user wants to see the workspace contents. I'll use list_files.
Action: list_files
Action Input: .
Observation: Directory 'workspace (root)' is empty.

Thought: The workspace is empty.
Final Answer: The workspace is currently empty. No files or directories exist yet.

============================================================
RESULT:
The workspace is currently empty. No files or directories exist yet.
============================================================

What would you like to do? > Create a project structure for a Python app with
  src, tests, and docs folders, and put a README.md in each folder

AGENT THINKING:
> Entering new AgentExecutor chain...
Thought: I need to create 3 directories and 3 files. Let me do them in order.
Action: create_directory
Action Input: src
Observation: Successfully created directory 'src'.

Thought: Now create tests directory.
Action: create_directory
Action Input: tests
Observation: Successfully created directory 'tests'.

Thought: Now create docs directory.
Action: create_directory
Action Input: docs
Observation: Successfully created directory 'docs'.

Thought: Now create README.md in src.
Action: write_file
Action Input: {"file_path": "src/README.md", "content": "# Source Code\n\nPut your Python source files here."}
Observation: Successfully wrote 3 line(s) to 'src/README.md'.

Thought: README in tests.
Action: write_file
Action Input: {"file_path": "tests/README.md", "content": "# Tests\n\nPut your test files here."}
Observation: Successfully wrote 3 line(s) to 'tests/README.md'.

Thought: README in docs.
Action: write_file
Action Input: {"file_path": "docs/README.md", "content": "# Documentation\n\nPut your documentation here."}
Observation: Successfully wrote 3 line(s) to 'docs/README.md'.

Thought: All done. Let me verify by listing the workspace.
Action: list_files
Action Input: .
Observation: Contents of 'workspace (root)':
  [DIR] docs/
  [DIR] src/
  [DIR] tests/
  Total: 3 directories, 0 files

Final Answer: Created your Python project structure:
  - src/ with README.md
  - tests/ with README.md
  - docs/ with README.md
```

---

## Part 8: Real World Application

### Enterprise AI Agents All Need Custom Tools

Every real-world enterprise agent has custom tools. Here is what a DevOps agent might look like:

```python
@tool
def query_database(sql_query: str) -> str:
    """Run a read-only SQL query against the metrics database."""
    conn = psycopg2.connect(DATABASE_URL)
    # ... execute query, return results as string

@tool
def create_jira_ticket(title: str, description: str, priority: str) -> str:
    """Create a new Jira ticket in the DevOps project."""
    # ... call Jira API

@tool
def get_deployment_status(service_name: str) -> str:
    """Get the current deployment status of a service in Kubernetes."""
    result = subprocess.run(["kubectl", "rollout", "status", f"deployment/{service_name}"])
    return result.stdout

@tool
def run_playbook(playbook_name: str, environment: str) -> str:
    """Execute an Ansible playbook in a specific environment."""
    # ... trigger playbook run
```

The agent can now:
- Check database metrics
- Create tickets for anomalies
- Check if deployments are healthy
- Trigger remediation playbooks

All from a natural language command: "Check the API service health, and if there are more than 100 errors in the last hour, create a P1 Jira ticket and run the restart-api playbook in production."

That is a real agentic DevOps workflow. The tools are different, but the pattern is identical to what you built here.

---

## Part 9: Extend This Project

### Idea 1: Add an Append Tool

Currently, `write_file` overwrites the whole file. Add an `append_file` tool:

```python
@tool
def append_file(file_path: str, content: str) -> str:
    """
    Append text to the end of an existing file without overwriting it.
    Use this when you want to add content to a file that already has content.
    Creates the file if it doesn't exist.
    """
    is_safe, absolute_path = is_safe_path(file_path)
    if not is_safe:
        return absolute_path
    with open(absolute_path, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully appended to '{file_path}'."
```

### Idea 2: Add a Search Tool

Let the agent search for content within files:

```python
@tool
def search_in_files(search_term: str) -> str:
    """
    Search for a text pattern across all files in the workspace.
    Returns a list of files that contain the search term and the matching lines.
    Use this when you need to find which files contain specific content.
    """
    matches = []
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r") as f:
                    for i, line in enumerate(f, 1):
                        if search_term.lower() in line.lower():
                            rel_path = os.path.relpath(filepath, WORKSPACE_DIR)
                            matches.append(f"{rel_path}:{i}: {line.strip()}")
            except Exception:
                pass
    if not matches:
        return f"No files contain '{search_term}'."
    return "\n".join(matches)
```

### Idea 3: Connect to a Real System

Replace the file tools with database tools. Use `psycopg2` or `sqlite3` to query a real database. The agent pattern stays exactly the same — only the tools change.

---

## Part 10: What You Learned

**Custom Tool Creation**
- The `@tool` decorator turns any Python function into an agent tool
- The tool name, docstring, and type hints are all the agent sees
- Tools should return strings (including error messages)

**Docstring Engineering**
- Docstrings are the agent's instruction manual for each tool
- They must explain WHAT the tool does, WHEN to use it, and WHAT the parameters mean
- Vague docstrings lead to wrong tool selection and unpredictable behavior

**Grounding and Safety**
- Always restrict agents to a safe scope (workspace directory, read-only mode, specific APIs)
- Apply grounding at two levels: code-level (the function refuses) and prompt-level (the agent is told not to try)
- `os.path.realpath()` prevents path traversal attacks

**Agent Decision Making**
- The agent picks tools by matching the task description to tool docstrings
- Multi-step tasks are broken down automatically (create directory, then write file)
- The agent can verify its own work when the system prompt encourages it

---

## Part 11: Quiz

**Question 1:** You create a custom tool but the agent never uses it, even when the task clearly needs it. What is the most likely cause?

<details>
<summary>Click to reveal answer</summary>

The docstring is missing, empty, or unclear. The agent makes tool selection decisions by reading the docstring. If the docstring doesn't clearly explain what the tool does and when to use it, the agent won't know to call it. Fix: Write a clear docstring that says "Use this tool when [specific situation]."

</details>

---

**Question 2:** A user asks the file manager agent: "Delete all temporary files." The agent starts deleting things it shouldn't. What went wrong, and how would you fix it?

<details>
<summary>Click to reveal answer</summary>

The `delete_file` docstring (or system prompt) didn't clearly define what "temporary" means or add a confirmation step. The agent interpreted the instruction broadly. Fix options: (1) Add "Only delete files if they have extensions like .tmp, .log, or .cache" to the docstring. (2) Add a confirmation step in the tool: list the files that would be deleted and return a message asking for confirmation before actually deleting. (3) Add prompt-level grounding: "Before deleting any file, list what you plan to delete and state why."

</details>

---

**Question 3:** What is the difference between code-level grounding and prompt-level grounding? Give an example of each from this project.

<details>
<summary>Click to reveal answer</summary>

Code-level grounding is safety enforced in the tool's Python code — it cannot be bypassed by the agent no matter what. Example: the `is_safe_path()` check in every tool that refuses to operate outside `./workspace/` regardless of what path is passed.

Prompt-level grounding is safety enforced in the system prompt — it tells the agent not to try certain things. Example: "You can ONLY operate on files within the workspace directory. Never attempt to access files outside the workspace." This is softer (a sufficiently adversarial prompt might bypass it) but prevents the agent from even attempting unsafe operations.

Both are needed: code-level for hard safety, prompt-level for guided behavior.

</details>

---

## Vocabulary Reference

| Term | Plain English Definition |
|------|--------------------------|
| @tool decorator | Python syntax that registers a function as an agent tool |
| Custom tool | A tool you write yourself (vs. importing a pre-built one) |
| Docstring | The string inside triple quotes below a function definition — the agent reads this |
| Grounding | Limiting what an agent can do to a safe, controlled scope |
| Workspace | A designated directory that the agent is restricted to operating within |
| Path traversal | A security attack using `../` to escape a sandbox directory |
| os.path.realpath() | Python function that resolves all `../` and symlinks to the true absolute path |
| Tool selection | How the agent decides which tool to use (by matching task to docstring) |

---

*Next Project: Project 6 — Multi-Step Task Agent with LangGraph (Stateful Workflows)*
