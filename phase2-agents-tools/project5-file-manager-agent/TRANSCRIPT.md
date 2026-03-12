# Learning Session Transcript — Project 5: File Manager Agent

**Student:** Alex (DevOps engineer, completed Project 4)
**Instructor:** Jordan
**Session Goal:** Build custom tools with @tool decorator, understand docstring importance, run a grounded file management agent

---

## Part 1: Recap and Context

**Jordan:** How'd Project 4 go?

**Alex:** Really well. I ran it a few times on different topics. I gave it "Docker Swarm vs Kubernetes" and it did three searches and came back with a solid comparison.

**Jordan:** Did you watch the verbose output?

**Alex:** Yeah, that was the best part. Watching it decide to do a second search because it wanted more data on one specific thing — that clicked for me. The agent is actually reasoning.

**Jordan:** Perfect. So today we build on that. In Project 4 we handed the agent a pre-built tool — Tavily. Today you're going to build the tools yourself. From scratch.

**Alex:** So instead of importing someone else's tool, I write my own?

**Jordan:** Exactly. And this is the skill that actually matters in the real world. In enterprise settings, nobody has pre-built LangChain tools for your company's internal ticketing system, your deployment pipeline, your monitoring API. You have to write them.

**Alex:** How hard is it?

**Jordan:** It's going to be less code than you think, and more subtle than you expect. The hard part isn't the Python — it's writing good descriptions.

**Alex:** Descriptions?

**Jordan:** That's the whole session. Let's start there.

---

## Part 2: How the Agent Picks Tools

**Jordan:** I want you to think about this from the agent's perspective. When it receives "Create a file called notes.txt with Hello World," it sees a list of available tools. What does that list look like?

**Alex:** I guess just the tool names?

**Jordan:** Names AND descriptions. The agent sees something like:

```
read_file: Read the contents of a file and return them as a string.
           Use this when you need to see what is inside a file.

write_file: Write content to a file, creating it if it doesn't exist.
            Use this when you need to create or update a file.

list_files: List all files and directories.
            Use this when you need to see what files exist.
```

And it reasons: "The user wants to write a file. The `write_file` tool says 'use this to create a file.' That's the one."

**Alex:** So the description IS the decision-making logic?

**Jordan:** Completely. The agent doesn't read your Python code. It reads the description. The description tells it when to use the tool and how.

**Alex:** Where does the description come from?

**Jordan:** The docstring. The string in triple quotes right below the function definition. LangChain reads it and turns it into the tool description automatically.

**Alex:** So writing a bad docstring means the agent uses the wrong tool?

**Jordan:** Or doesn't use the tool at all. I've seen tools get completely ignored because the docstring was one vague sentence. The agent reads it and thinks "I have no idea what this is for."

---

## Part 3: Writing the First Tool

**Jordan:** Open `file_manager_agent.py`. Let's look at the `@tool` decorator and write one together.

**Alex:** I see the import: `from langchain.tools import tool`. So `tool` is a decorator?

**Jordan:** Right. In Python, a decorator is the `@something` line above a function. It wraps the function with extra behavior. In this case, `@tool` tells LangChain "this function should be available as an agent tool."

**Alex:** So I write a normal Python function and just put `@tool` above it?

**Jordan:** Almost. You also need type hints and a docstring. Let's look at `read_file`:

```python
@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file and return them as a string.
    Use this tool when you need to see what is inside a file.
    The file_path should be relative to the workspace (e.g., 'notes.txt').
    Returns the file contents, or an error message if the file doesn't exist.
    """
    # ... implementation ...
```

**Alex:** Okay, the type hint `file_path: str` tells LangChain the input is a string. And `-> str` says it returns a string.

**Jordan:** Correct. And look at the docstring — four things: what it does, when to use it, what the parameter means, and what it returns. Every tool should have all four.

**Alex:** What happens to errors? I see the function returns error strings instead of raising exceptions.

**Jordan:** Great catch. Tools should always return strings, including error cases. Why? Because the agent receives the return value as its "Observation." If you raise an exception, it crashes the loop. If you return an error string, the agent READS the error and can decide what to do next. "ERROR: File not found" is a useful observation. An exception is just noise.

---

## Part 4: The Safety System

**Jordan:** Notice this at the top of the file:

```python
WORKSPACE_DIR = os.path.abspath("./workspace")
```

Why do you think we need this?

**Alex:** So the agent can only work in that folder?

**Jordan:** Exactly. Without this, a file manager agent could theoretically read your `.env` file with API keys, delete system files, or overwrite your bash config. Have you heard the term "grounding"?

**Alex:** Vaguely. Like keeping the AI focused?

**Jordan:** In the safety context, grounding means limiting what the agent can do to a safe, controlled scope. This workspace restriction is grounding. Every tool checks that the target path is inside `./workspace/` before doing anything.

**Alex:** How does it prevent someone from typing `../../etc/passwd` to escape the folder?

**Jordan:** Great question. That's called a path traversal attack. The defense is `os.path.realpath()`. It resolves all the `../` sequences to the actual final path. So `workspace/../../etc/passwd` becomes `/etc/passwd`, and then the check "does this start with the workspace path?" fails. Refused.

**Alex:** That's a security concept I've seen in web vulnerabilities. Good that it applies here too.

**Jordan:** Same concept, different context. Any time you're using user-provided file paths, you need this check.

---

## Part 5: Building the Prompt

**Jordan:** Now look at the `FILE_MANAGER_PROMPT`. Compare it to the one in Project 4. What's the same?

**Alex:** Same four placeholders: `{tools}`, `{tool_names}`, `{input}`, `{agent_scratchpad}`. Same Thought/Action/Observation format.

**Jordan:** Exactly. The ReAct structure is the same — we're just changing the instructions and the tools. Look at this line in the prompt:

```
3. Verify your work (e.g., after writing, you can read the file to confirm)
```

**Alex:** That's telling the agent to double-check itself?

**Jordan:** Yes. And watch what happens when you run it — you'll see the agent spontaneously use `list_files` after creating things, even though you never asked it to verify. That instruction in the prompt is why.

**Alex:** So I can shape agent behavior through the system prompt?

**Jordan:** Completely. The system prompt is the agent's personality and operating procedure. You can tell it to be conservative, verbose, verifying, fast, thorough — whatever fits your use case.

---

## Part 6: Running It for the First Time

**Jordan:** Alright, let's run it.

```bash
python file_manager_agent.py
```

**Alex:** It printed the workspace path and some example commands. Now it's asking "What would you like to do?" Let me try something simple: "Show me what's in the workspace"

**Jordan:** Go for it.

**Alex:** It's thinking...

```
Thought: The user wants to see workspace contents. I'll use list_files.
Action: list_files
Action Input: .
Observation: Directory 'workspace (root)' is empty.
Final Answer: The workspace is currently empty.
```

Simple. Good. Now let me try something more complex: "Create a project structure for a Python app with src, tests, and docs folders, and a README in each"

**Jordan:** Watch carefully now.

**Alex:** Whoa. It's creating all three directories one by one:

```
Action: create_directory
Action Input: src
...
Action: create_directory
Action Input: tests
...
Action: create_directory
Action Input: docs
```

And now it's writing the README files:

```
Action: write_file
Action Input: {"file_path": "src/README.md", "content": "# Source Code\n\nPut your Python source files here."}
```

It wrote different content in each README! I didn't ask it to do that!

**Jordan:** It inferred that each folder should have an appropriate description. You said "a README in each" — it figured out what reasonable content would be.

**Alex:** And now it's verifying with `list_files`. Exactly like the prompt said it should.

**Jordan:** Watching the six-step plan execute automatically from one sentence... that's the power of a well-configured agent.

---

## Part 7: Testing Tool Selection

**Jordan:** Now let's test whether the docstrings are actually driving the tool selection. Ask it to do something that requires multiple different tools.

**Alex:** Okay: "Read the README in the src folder, then create a new file called notes.txt with a summary of what you read"

**Jordan:** This requires `read_file` then `write_file`. Let's see if it figures that out.

**Alex:** It's using `read_file` first:

```
Action: read_file
Action Input: src/README.md
Observation: Contents of 'src/README.md':
# Source Code
Put your Python source files here.
```

And now `write_file`:

```
Action: write_file
Action Input: {"file_path": "notes.txt", "content": "Summary of src/README.md:\nThe src folder is for Python source files."}
Observation: Successfully wrote 2 line(s) to 'notes.txt'.
```

It used the exact right tools in the right order without being told to.

**Jordan:** How did it know which tool to use?

**Alex:** The docstrings. `read_file` says "use this when you need to see what is inside a file." `write_file` says "use this when you need to create a new file." It matched the task to the descriptions.

**Jordan:** Exactly. You have just built the core skill of agent engineering. The agent's intelligence is in Claude. Your job is to give it good tools with good descriptions.

---

## Part 8: Testing the Safety System

**Jordan:** Before we wrap up, let's test the safety guardrail. Try to make it do something dangerous.

**Alex:** Okay, let me try: "Read the file /etc/passwd"

**Jordan:** Watch the observation.

**Alex:** It tried... and got:

```
Observation: SAFETY ERROR: Path '/etc/passwd' is outside the workspace directory.
             Only operations within ./workspace/ are allowed.
```

And then:

```
Final Answer: I cannot access '/etc/passwd' because it is outside the designated
              workspace directory. I can only work with files inside ./workspace/.
```

**Jordan:** The code-level safety check kicked in. Even though the agent received the request, the tool refused to execute it and returned an error string instead.

**Alex:** And the agent read that error and told the user it couldn't do it.

**Jordan:** Right. It didn't crash. It didn't escalate. It read the observation, understood what happened, and explained the constraint. That's robust agent behavior.

---

## Part 9: The Delete Tool

**Jordan:** Try one more thing. Ask it to delete a file.

**Alex:** "Delete the file notes.txt"

**Jordan:** Watch what it does.

**Alex:**

```
Thought: The user wants to delete notes.txt. This cannot be undone.
         I'll use delete_file.
Action: delete_file
Action Input: notes.txt
Observation: Successfully deleted 'notes.txt'.
Final Answer: Done — I deleted 'notes.txt' from the workspace.
```

Hmm, it just deleted it without asking me to confirm.

**Jordan:** Right. Notice the docstring says "WARNING: This action cannot be undone." But it doesn't say "ask for confirmation." The agent respects the warning by being thoughtful in its Thought step, but still executes.

**Alex:** So if I wanted it to always confirm, I'd change the docstring?

**Jordan:** Or add code inside the delete tool that returns a confirmation request. For example:

```python
@tool
def delete_file(file_path: str) -> str:
    """
    Delete a file. REQUIRES CONFIRMATION.
    Before deleting, this tool returns a confirmation request.
    Only deletes if called with 'CONFIRMED: filename'.
    """
    if not file_path.startswith("CONFIRMED: "):
        filename = file_path
        return f"CONFIRMATION REQUIRED: Type 'CONFIRMED: {filename}' to delete this file."
    actual_path = file_path.replace("CONFIRMED: ", "")
    # ... do the delete
```

**Alex:** That's clever. The tool itself enforces a two-step process.

**Jordan:** And the docstring tells the agent exactly how to use it. The agent will know to call it twice — once to get the confirmation message, once with the CONFIRMED prefix to actually delete.

---

## Part 10: Key Takeaways

**Jordan:** Let me ask you the key question from today: what makes a good tool?

**Alex:** A clear docstring that says what it does, when to use it, what the params mean, and any warnings. And it returns strings — even for errors.

**Jordan:** Perfect. And what is grounding?

**Alex:** Limiting what the agent can do to a safe scope. At two levels: code-level (the function refuses unsafe operations) and prompt-level (the agent is told not to try).

**Jordan:** What would you do if you wanted to build an agent that could query your company's internal database?

**Alex:** Write a custom tool. `@tool` decorator, clear docstring explaining what the query does and how to use it, SQL query goes in, results string comes out. Then add it to the tools list.

**Jordan:** That's it. You just described how to build a database agent. Everything we did with files — same pattern, different implementation.

**Alex:** The pattern is always the same: tools list, ReAct agent, AgentExecutor. Only the tools change.

**Jordan:** Exactly. That's the abstraction that makes LangChain powerful. You swap the tools, everything else stays the same.

**Alex:** What's Project 6?

**Jordan:** LangGraph. You're going to build an agent that doesn't just react — it has a structured plan with multiple stages. Think of it as going from "improvising" to "following a project plan."

**Alex:** I'm in.

---

## Session Summary

**What Was Covered:**
- How to create custom tools using the `@tool` decorator
- Why docstrings are the agent's decision-making guide (not the function body)
- The four elements of a good docstring: what, when, parameters, return value
- Why tools return strings instead of raising exceptions
- The workspace grounding pattern and `os.path.realpath()` for path safety
- Code-level vs. prompt-level grounding
- How the agent automatically sequences multi-step tasks

**Student Highlights:**
- Recognized that docstrings drive tool selection before being told explicitly
- Connected path traversal concepts from web security to file agent security
- Independently identified that the `delete_file` docstring could enforce confirmation behavior

**Next Session:** Project 6 — LangGraph Multi-Step Task Agent (Stateful Workflows with StateGraph)
