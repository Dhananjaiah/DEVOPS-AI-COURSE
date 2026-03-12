"""
=============================================================================
PROJECT 5: File Manager Agent — Building Custom Tools
=============================================================================

WHAT THIS FILE TEACHES:
    - How to create custom tools using the @tool decorator
    - Why docstrings are critical (the agent reads them as instructions)
    - How to build a ReAct agent with your own tools
    - How to "ground" an agent (safety constraints on what it can do)
    - How the agent chooses which tool to use based on natural language

KEY TEACHING POINT:
    In Project 4, we used a PRE-BUILT tool (TavilySearchResults).
    In this project, you write tools FROM SCRATCH.
    This is how every enterprise AI agent works — custom tools that
    interact with YOUR company's specific systems.

BEFORE YOU RUN:
    1. Copy .env.example to .env
    2. Add your ANTHROPIC_API_KEY to .env
    3. pip install -r requirements.txt
    4. python file_manager_agent.py

=============================================================================
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------

# os: file system operations (checking if paths exist, listing directories, etc.)
import os

# shutil: higher-level file operations (we use it for deleting files/dirs)
import shutil

# dotenv: reads .env file and loads API keys into environment
from dotenv import load_dotenv

# sys: for clean program exit on errors
import sys

# tool: the DECORATOR that turns any Python function into a LangChain tool
# A decorator is the @thing that goes above a function definition
# @tool tells LangChain: "this function can be called by an agent"
from langchain.tools import tool

# ChatAnthropic: LangChain's Claude wrapper (same as Project 4)
from langchain_anthropic import ChatAnthropic

# create_react_agent, AgentExecutor: the ReAct agent framework (same as Project 4)
from langchain.agents import create_react_agent, AgentExecutor

# PromptTemplate: builds our system prompt with the required ReAct placeholders
from langchain.prompts import PromptTemplate

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
# SAFETY CONFIGURATION — THE "WORKSPACE" CONCEPT
# ---------------------------------------------------------------------------
#
# GROUNDING: limiting what the agent can do is called "grounding" the agent.
# Without limits, a file manager agent could theoretically delete system files,
# read your SSH keys, or overwrite important configs.
#
# Our safety rule: ALL file operations MUST happen inside ./workspace/
# If the user asks the agent to touch files outside this directory,
# the tools return an error instead of complying.
#
# This is a simple but effective safety guardrail.

# Get the absolute path to the workspace directory
# os.path.abspath() converts "./workspace" to a full path like
# "/home/user/project5-file-manager-agent/workspace"
WORKSPACE_DIR = os.path.abspath("./workspace")

# Create the workspace directory if it doesn't exist yet
# exist_ok=True means: don't crash if it already exists
os.makedirs(WORKSPACE_DIR, exist_ok=True)

print(f"Workspace directory: {WORKSPACE_DIR}")
print("(All file operations are restricted to this directory for safety)")

# ---------------------------------------------------------------------------
# SAFETY HELPER FUNCTION
# ---------------------------------------------------------------------------

def is_safe_path(path: str) -> tuple[bool, str]:
    """
    Check if a given path is safely inside the WORKSPACE_DIR.

    Returns:
        (True, absolute_path) if the path is safe
        (False, error_message) if the path would escape the workspace

    This uses os.path.realpath() which resolves any ".." tricks like
    "workspace/../../../etc/passwd" back to the real absolute path.
    """
    # Convert the path to an absolute path
    # If the user passes a relative path like "notes.txt", we prepend the workspace
    if not os.path.isabs(path):
        # Relative path: put it inside the workspace
        absolute_path = os.path.join(WORKSPACE_DIR, path)
    else:
        # Already absolute: use as-is but check if it's inside workspace
        absolute_path = path

    # Resolve any ".." or symlinks to get the REAL path
    real_path = os.path.realpath(absolute_path)

    # Check if the real path starts with the workspace directory
    # os.path.realpath(WORKSPACE_DIR) ensures we compare both resolved paths
    if not real_path.startswith(os.path.realpath(WORKSPACE_DIR)):
        return False, f"SAFETY ERROR: Path '{path}' is outside the workspace directory. Only operations within ./workspace/ are allowed."

    return True, real_path

# ---------------------------------------------------------------------------
# CUSTOM TOOLS — THIS IS THE CORE OF THIS PROJECT
# ---------------------------------------------------------------------------
#
# HOW THE @tool DECORATOR WORKS:
#
# When you write:
#
#     @tool
#     def read_file(file_path: str) -> str:
#         """Reads a file and returns its content."""
#         ...
#
# LangChain does the following:
#   1. Registers this function as a tool
#   2. Uses the function name ("read_file") as the tool's name
#   3. Uses the DOCSTRING as the tool's description (what the agent reads!)
#   4. Uses the type hints (str) to understand input/output types
#
# THE CRITICAL LESSON: THE DOCSTRING IS THE AGENT'S INSTRUCTION MANUAL
# The agent NEVER sees the function body — only its name and docstring.
# If your docstring is unclear or missing, the agent won't know when to use the tool.
#
# ---------------------------------------------------------------------------

@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file and return them as a string.
    Use this tool when you need to see what is inside a file.
    The file_path should be relative to the workspace (e.g., 'notes.txt' or 'subdir/data.txt').
    Returns the file contents as a string, or an error message if the file doesn't exist.
    """
    # Check if the path is safe (inside workspace)
    is_safe, result = is_safe_path(file_path)
    if not is_safe:
        # Return the error message as a string (the agent will see this as the observation)
        return result

    # result is the resolved absolute path (since is_safe is True)
    absolute_path = result

    # Check if the file actually exists
    if not os.path.exists(absolute_path):
        return f"ERROR: File '{file_path}' does not exist in the workspace."

    # Check if it's actually a file (not a directory)
    if not os.path.isfile(absolute_path):
        return f"ERROR: '{file_path}' is a directory, not a file. Use list_files to see its contents."

    # Try to read the file — use try/except to handle permission errors or encoding issues
    try:
        with open(absolute_path, "r", encoding="utf-8") as f:
            # f.read() reads the entire file into a string
            content = f.read()

        # If the file is empty, say so explicitly
        if not content.strip():
            return f"File '{file_path}' exists but is empty."

        return f"Contents of '{file_path}':\n\n{content}"

    except PermissionError:
        return f"ERROR: Permission denied reading '{file_path}'."
    except UnicodeDecodeError:
        return f"ERROR: '{file_path}' appears to be a binary file and cannot be read as text."
    except Exception as e:
        return f"ERROR reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, creating it if it doesn't exist or overwriting it if it does.
    Use this tool when you need to create a new file or update an existing file's content.
    The file_path should be relative to the workspace (e.g., 'notes.txt').
    The content parameter is the text to write into the file.
    Returns a success message or an error message.
    """
    # Check safety
    is_safe, result = is_safe_path(file_path)
    if not is_safe:
        return result

    absolute_path = result

    # If the file is in a subdirectory, make sure that subdirectory exists
    # os.path.dirname() gets the directory part of a path
    # e.g., for "subdir/notes.txt" it returns "subdir"
    parent_dir = os.path.dirname(absolute_path)
    if parent_dir:
        # exist_ok=True: don't crash if it already exists
        os.makedirs(parent_dir, exist_ok=True)

    # Write the content to the file
    # "w" mode: write (creates file if it doesn't exist, overwrites if it does)
    # encoding="utf-8": standard text encoding
    try:
        with open(absolute_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Count the lines we wrote for a helpful success message
        line_count = len(content.splitlines())
        return f"Successfully wrote {line_count} line(s) to '{file_path}'."

    except PermissionError:
        return f"ERROR: Permission denied writing to '{file_path}'."
    except Exception as e:
        return f"ERROR writing file: {str(e)}"


@tool
def list_files(directory: str) -> str:
    """
    List all files and subdirectories inside a directory.
    Use this tool when you need to see what files exist in the workspace or a subdirectory.
    Pass '.' or 'workspace' to list the root workspace directory.
    Pass a subdirectory name like 'projects' to list files inside that subdirectory.
    Returns a formatted list of files and directories, or an error message.
    """
    # Handle the special case where the user says "." or "workspace" to mean the root
    if directory in (".", "workspace", "", WORKSPACE_DIR):
        target_dir = WORKSPACE_DIR
        display_name = "workspace (root)"
    else:
        # Check if the subdirectory path is safe
        is_safe, result = is_safe_path(directory)
        if not is_safe:
            return result
        target_dir = result
        display_name = directory

    # Check if the directory exists
    if not os.path.exists(target_dir):
        return f"ERROR: Directory '{directory}' does not exist in the workspace."

    # Check it's actually a directory (not a file)
    if not os.path.isdir(target_dir):
        return f"ERROR: '{directory}' is a file, not a directory. Use read_file to read its contents."

    try:
        # os.listdir() returns a list of names in the directory
        # sorted() alphabetizes them for readability
        entries = sorted(os.listdir(target_dir))

        if not entries:
            return f"Directory '{display_name}' is empty."

        # Build a nicely formatted output
        # Separate files from directories for clarity
        dirs = []
        files = []

        for entry in entries:
            full_entry_path = os.path.join(target_dir, entry)
            if os.path.isdir(full_entry_path):
                dirs.append(f"  [DIR]  {entry}/")
            else:
                # Get file size in a human-readable format
                size = os.path.getsize(full_entry_path)
                files.append(f"  [FILE] {entry} ({size} bytes)")

        output = f"Contents of '{display_name}':\n"
        if dirs:
            output += "\nDirectories:\n" + "\n".join(dirs)
        if files:
            output += "\nFiles:\n" + "\n".join(files)

        output += f"\n\nTotal: {len(dirs)} directory/ies, {len(files)} file(s)"
        return output

    except PermissionError:
        return f"ERROR: Permission denied listing '{directory}'."
    except Exception as e:
        return f"ERROR listing directory: {str(e)}"


@tool
def create_directory(dir_path: str) -> str:
    """
    Create a new directory (folder) inside the workspace.
    Use this tool when you need to organize files into subdirectories.
    The dir_path should be relative to the workspace (e.g., 'projects' or 'projects/backend').
    This can create nested directories in one call (e.g., 'a/b/c' creates all three levels).
    Returns a success message or an error message.
    """
    # Check safety
    is_safe, result = is_safe_path(dir_path)
    if not is_safe:
        return result

    absolute_path = result

    # Check if it already exists
    if os.path.exists(absolute_path):
        if os.path.isdir(absolute_path):
            return f"Directory '{dir_path}' already exists."
        else:
            return f"ERROR: '{dir_path}' already exists as a file, not a directory."

    try:
        # os.makedirs() creates the directory AND any necessary parent directories
        # exist_ok=True prevents errors if it somehow already exists
        os.makedirs(absolute_path, exist_ok=True)
        return f"Successfully created directory '{dir_path}'."

    except PermissionError:
        return f"ERROR: Permission denied creating directory '{dir_path}'."
    except Exception as e:
        return f"ERROR creating directory: {str(e)}"


@tool
def delete_file(file_path: str) -> str:
    """
    Delete a file from the workspace permanently.
    Use this tool ONLY when explicitly asked to delete or remove a specific file.
    Do NOT use this unless the user clearly wants the file deleted.
    The file_path should be relative to the workspace (e.g., 'old_notes.txt').
    This cannot delete directories — only individual files.
    Returns a success message or an error message.
    WARNING: This action cannot be undone.
    """
    # Check safety
    is_safe, result = is_safe_path(file_path)
    if not is_safe:
        return result

    absolute_path = result

    # Check the file exists
    if not os.path.exists(absolute_path):
        return f"ERROR: File '{file_path}' does not exist."

    # Safety check: refuse to delete directories (use a different tool concept for that)
    if os.path.isdir(absolute_path):
        return f"ERROR: '{file_path}' is a directory. This tool can only delete files."

    try:
        # os.remove() deletes a file permanently
        os.remove(absolute_path)
        return f"Successfully deleted '{file_path}'."

    except PermissionError:
        return f"ERROR: Permission denied deleting '{file_path}'."
    except Exception as e:
        return f"ERROR deleting file: {str(e)}"


# ---------------------------------------------------------------------------
# COLLECT ALL TOOLS INTO A LIST
# ---------------------------------------------------------------------------
#
# The agent will have access to ALL these tools.
# It reads each tool's docstring and decides which one to use based on context.

tools = [
    read_file,        # Read file contents
    write_file,       # Write/create files
    list_files,       # List directory contents
    create_directory, # Create new directories
    delete_file,      # Delete files (with caution)
]

# ---------------------------------------------------------------------------
# INITIALIZE THE LLM
# ---------------------------------------------------------------------------

llm = ChatAnthropic(
    model="claude-opus-4-6",           # The model we use throughout this course
    anthropic_api_key=ANTHROPIC_API_KEY,
    temperature=0.1,                   # Low temperature for reliable, predictable behavior
    max_tokens=4096,                   # Room for detailed responses
)

# ---------------------------------------------------------------------------
# BUILD THE PROMPT TEMPLATE
# ---------------------------------------------------------------------------
#
# This prompt tells the agent:
# 1. What it is (a file manager)
# 2. The safety rule (workspace only)
# 3. How to think about file operations
# 4. The required ReAct format

FILE_MANAGER_PROMPT = PromptTemplate.from_template(
    """You are a helpful file management assistant. You help users manage files and
directories inside a designated workspace directory.

IMPORTANT SAFETY RULES:
- You can ONLY operate on files within the workspace directory
- Never attempt to access files outside the workspace
- When creating files, use simple relative paths like 'filename.txt'
- For DELETE operations, confirm what you're doing in your Thought before acting

You have access to these tools:

{tools}

When given a task:
1. Think about which tool(s) you need
2. Use tools in the right order (e.g., create directory before writing files into it)
3. Verify your work (e.g., after writing, you can read the file to confirm)
4. Report what you did clearly

Use the following format EXACTLY:

Question: the input question you must answer
Thought: think about what to do step by step
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a clear summary of what was done

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
)

# ---------------------------------------------------------------------------
# CREATE THE AGENT AND EXECUTOR
# ---------------------------------------------------------------------------

# Build the ReAct agent blueprint (same pattern as Project 4)
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=FILE_MANAGER_PROMPT,
)

# Create the executor that will run the agent loop
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,               # Show the Thought/Action/Observation loop
    max_iterations=15,          # Allow up to 15 steps for complex multi-file tasks
    handle_parsing_errors=True, # Recover gracefully from formatting errors
)

# ---------------------------------------------------------------------------
# THE MAIN INTERACTIVE LOOP
# ---------------------------------------------------------------------------

def run_file_manager():
    """
    Runs the file manager agent in an interactive loop.
    The user can type natural language commands and the agent figures out
    which tools to use and in what order.
    """

    # Print welcome message and show what the agent can do
    print("\n" + "="*60)
    print("   FILE MANAGER AGENT")
    print("   Powered by Claude + Custom LangChain Tools")
    print("="*60)
    print(f"\nWorkspace: {WORKSPACE_DIR}")
    print("\nThis agent can manage files using natural language.")
    print("Example commands:")
    print("  - 'Create a file called notes.txt with the text Hello World'")
    print("  - 'Show me all files in the workspace'")
    print("  - 'Create a folder called projects and put a README in it'")
    print("  - 'Read the file notes.txt'")
    print("  - 'Delete the file old_notes.txt'")
    print("  - 'Create a structured project with folders for src, tests, and docs'")
    print("\nType 'quit' to exit.")
    print("-"*60)

    # Run in a loop so the user can give multiple commands
    while True:

        # Get a command from the user
        print()  # blank line for readability
        command = input("What would you like to do? > ").strip()

        # Check if the user wants to quit
        if command.lower() in ("quit", "exit", "q", "bye"):
            print("\nGoodbye! Your files are saved in the workspace directory.")
            break

        # Skip empty input
        if not command:
            print("Please enter a command. (Type 'quit' to exit)")
            continue

        print(f"\nExecuting: '{command}'")
        print("-"*60)
        print("AGENT THINKING:\n")

        # Invoke the agent with the user's natural language command
        # The agent will figure out which tools to use and in what order
        try:
            result = agent_executor.invoke({"input": command})

            # Print the final answer cleanly
            print("\n" + "="*60)
            print("RESULT:")
            print("="*60)
            print(result["output"])

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nOperation cancelled by user.")
            continue
        except Exception as e:
            # Handle unexpected errors without crashing the whole program
            print(f"\nERROR: {e}")
            print("The agent encountered an issue. Try rephrasing your command.")
            continue


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_file_manager()
