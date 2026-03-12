"""
=============================================================================
PROJECT 4: Web Research Agent
=============================================================================

WHAT THIS FILE TEACHES:
    - What an AI "agent" is and how it differs from a simple chatbot
    - What "tools" are in the context of AI agents
    - The ReAct pattern (Reason + Act) — the core loop that makes agents work
    - How to wire a real web search tool (Tavily) into an agent
    - How LangChain's create_react_agent() orchestrates the whole thing

BEFORE YOU RUN:
    1. Copy .env.example to .env
    2. Add your ANTHROPIC_API_KEY and TAVILY_API_KEY to .env
    3. pip install -r requirements.txt
    4. python web_research_agent.py

=============================================================================
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------

# os: used to read environment variables (like API keys stored in .env)
import os

# dotenv: reads the .env file and loads variables into the environment
# Without this, your API keys would have to be hardcoded (bad practice!)
from dotenv import load_dotenv

# sys: used for printing to stderr and exiting the program cleanly
import sys

# ChatAnthropic: the LangChain wrapper around Claude
# Instead of calling anthropic.Anthropic() directly, we use this class
# because LangChain agents expect a "LangChain-compatible" LLM object
from langchain_anthropic import ChatAnthropic

# TavilySearchResults: a pre-built LangChain tool that calls the Tavily web search API
# Tavily is an AI-optimized search engine — it returns clean, structured results
# instead of raw HTML like a normal search engine would
from langchain_community.tools.tavily_search import TavilySearchResults

# create_react_agent: the function that builds our ReAct agent
# It takes: (1) the LLM, (2) the list of tools, (3) a system prompt
# and returns an agent that can reason and act in a loop
from langchain.agents import create_react_agent, AgentExecutor

# hub: LangChain's prompt repository — we pull a pre-made ReAct prompt template
# The prompt template includes special placeholders the ReAct loop needs:
#   {tools}, {tool_names}, {agent_scratchpad}, {input}
from langchain import hub

# PromptTemplate: lets us build custom prompts with placeholders
# We'll use this to customize the system prompt while keeping the ReAct structure
from langchain.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# STEP 1: LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------

# load_dotenv() reads the .env file in the current directory
# and adds each KEY=VALUE pair to the environment
# After this call, os.environ["ANTHROPIC_API_KEY"] will work
load_dotenv()

# Read the API keys from environment variables
# These were loaded from your .env file by load_dotenv() above
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Validate that the keys actually exist — give helpful errors if not
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment.")
    print("Did you copy .env.example to .env and fill in your key?")
    sys.exit(1)  # Exit with error code 1

if not TAVILY_API_KEY:
    print("ERROR: TAVILY_API_KEY not found in environment.")
    print("Get a free key at: https://tavily.com")
    sys.exit(1)

# ---------------------------------------------------------------------------
# WHAT IS AN AGENT? (Read this before looking at the code below)
# ---------------------------------------------------------------------------
#
# A CHATBOT just responds to your message. It has no ability to take actions.
#
# An AGENT can:
#   1. Receive a goal ("Research quantum computing trends")
#   2. DECIDE what to do to achieve that goal
#   3. USE TOOLS to take real actions (like searching the web)
#   4. OBSERVE the results of those actions
#   5. DECIDE what to do next based on what it saw
#   6. Repeat steps 3-5 until the goal is achieved
#
# This "decide → act → observe → decide again" loop is called the AGENT LOOP.
#
# ---------------------------------------------------------------------------
# WHAT IS A TOOL?
# ---------------------------------------------------------------------------
#
# A TOOL is a function the agent is allowed to call.
# Each tool has:
#   - A NAME (e.g., "tavily_search_results_json")
#   - A DESCRIPTION (the agent reads this to know what the tool does)
#   - Input/Output schema (what to pass in, what comes back)
#
# The agent DECIDES which tool to use based on the descriptions.
# It never sees the tool's code — only its name and description.
#
# ---------------------------------------------------------------------------
# WHAT IS THE REACT PATTERN?
# ---------------------------------------------------------------------------
#
# ReAct = Reasoning + Acting (coined in a 2022 research paper)
#
# Each loop iteration looks like this:
#
#   Thought:  "I need to find recent news about quantum computing."
#   Action:   tavily_search_results_json
#   Action Input: "quantum computing 2024 breakthroughs"
#   Observation: [search results appear here]
#
#   Thought:  "The results mention IBM and Google. Let me search for more detail."
#   Action:   tavily_search_results_json
#   Action Input: "IBM quantum computing 2024"
#   Observation: [more results]
#
#   Thought:  "I now have enough information to write the summary."
#   Final Answer: [the structured research summary]
#
# The THOUGHT steps are pure reasoning — Claude thinking about what to do.
# The ACTION steps are the agent calling a tool.
# The OBSERVATION steps are the tool's response coming back.
# This repeats until Claude decides it has enough to give a Final Answer.
#
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# STEP 2: INITIALIZE THE LLM
# ---------------------------------------------------------------------------

# ChatAnthropic is LangChain's wrapper for Claude
# model: which Claude model to use
# temperature: 0.1 = mostly deterministic (good for research tasks where we want facts)
# max_tokens: maximum length of Claude's response per turn
llm = ChatAnthropic(
    model="claude-opus-4-6",          # The model we use throughout this course
    anthropic_api_key=ANTHROPIC_API_KEY, # Pass the key explicitly (extra safe)
    temperature=0.1,                  # Low temp = more factual, less creative
    max_tokens=4096,                  # Plenty of room for detailed research summaries
)

# ---------------------------------------------------------------------------
# STEP 3: DEFINE THE TOOLS
# ---------------------------------------------------------------------------

# TavilySearchResults is a pre-built tool that calls the Tavily search API
# max_results=3 means: return the top 3 search results per query
# Tavily is preferred over Google/Bing because:
#   1. It has a developer API (Google Search API is expensive)
#   2. It returns clean, structured data (not raw HTML)
#   3. It's built for LLM use cases (returns summaries, not just URLs)
search_tool = TavilySearchResults(
    max_results=3,                    # Top 3 results keeps context windows manageable
    tavily_api_key=TAVILY_API_KEY,    # Pass key explicitly
)

# Put all tools in a list — we'll pass this list to create_react_agent()
# An agent can have 1 tool or 100 tools. More tools = more capability + more complexity.
tools = [search_tool]

# ---------------------------------------------------------------------------
# STEP 4: BUILD THE PROMPT TEMPLATE
# ---------------------------------------------------------------------------
#
# The ReAct agent needs a VERY specific prompt format.
# The prompt must include these exact placeholders:
#   {tools}          — LangChain fills this with tool descriptions
#   {tool_names}     — LangChain fills this with tool names
#   {agent_scratchpad} — LangChain fills this with the Thought/Action/Observation history
#   {input}          — LangChain fills this with the user's message
#
# We pull a standard ReAct prompt from LangChain Hub and customize it.
# The hub prompt "hwchase17/react" is the standard starting point used by everyone.

# Pull the base ReAct prompt template from LangChain Hub
# This gives us a PromptTemplate with the correct structure
base_prompt = hub.pull("hwchase17/react")

# Let's look at what the base prompt template looks like:
# (You can uncomment this line to inspect it)
# print("Base prompt template:\n", base_prompt.template)

# We'll customize the system instructions by creating our own PromptTemplate
# that matches the same structure but with our research assistant instructions
RESEARCH_AGENT_PROMPT = PromptTemplate.from_template(
    """You are an expert research assistant. Your job is to research topics thoroughly
and provide clear, well-structured summaries.

When given a research topic, you will:
1. Search for recent and relevant information
2. Identify key themes, facts, and findings
3. Note your sources
4. Provide a structured summary

You have access to the following tools:

{tools}

Use the following format EXACTLY:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Structure your Final Answer as:
## Research Summary: [Topic]

### Overview
[2-3 sentence overview of the topic]

### Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]
- [More findings as needed]

### Sources
[List the URLs from your search results]

### Bottom Line
[1-2 sentence takeaway]

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
)

# ---------------------------------------------------------------------------
# STEP 5: CREATE THE REACT AGENT
# ---------------------------------------------------------------------------
#
# create_react_agent() wires everything together:
#   - It takes the LLM (Claude), the tools, and the prompt
#   - It returns an "agent" which is basically a configured reasoning engine
#
# The agent itself is NOT yet runnable — it's like a blueprint.
# We still need AgentExecutor to actually RUN it.

agent = create_react_agent(
    llm=llm,            # The language model that does the reasoning
    tools=tools,        # The tools the agent can use
    prompt=RESEARCH_AGENT_PROMPT,  # The prompt that defines behavior
)

# ---------------------------------------------------------------------------
# STEP 6: CREATE THE AGENT EXECUTOR
# ---------------------------------------------------------------------------
#
# AgentExecutor is the "runtime" that:
#   1. Takes user input
#   2. Runs the agent loop (Thought → Action → Observation → repeat)
#   3. Calls the tools when the agent decides to
#   4. Feeds tool results back to the agent
#   5. Stops when the agent writes "Final Answer:"
#
# verbose=True is IMPORTANT for learning: it prints every Thought, Action,
# and Observation so you can SEE the agent's reasoning process in real-time.

agent_executor = AgentExecutor(
    agent=agent,              # The agent blueprint we created above
    tools=tools,              # Same tools list (executor needs it too)
    verbose=True,             # Print the full Thought/Action/Observation loop
    max_iterations=10,        # Safety limit: stop after 10 loops (prevents infinite loops)
    handle_parsing_errors=True,  # If Claude formats a response incorrectly, retry gracefully
    return_intermediate_steps=True,  # Return the full reasoning chain in the output dict
)

# ---------------------------------------------------------------------------
# STEP 7: THE MAIN FUNCTION
# ---------------------------------------------------------------------------

def run_research_agent():
    """
    Main function that:
    1. Gets a research topic from the user
    2. Runs the ReAct agent on that topic
    3. Prints the structured results
    """

    # Print a welcome banner
    print("\n" + "="*60)
    print("   WEB RESEARCH AGENT")
    print("   Powered by Claude + Tavily + LangChain ReAct")
    print("="*60)
    print("\nThis agent will:")
    print("  1. Search the web for your topic")
    print("  2. Analyze the results")
    print("  3. Give you a structured research summary")
    print("\nWatch the agent's THINKING PROCESS appear in real-time!")
    print("  > Lines starting with 'Thought:' = Claude reasoning")
    print("  > Lines starting with 'Action:' = Claude calling a tool")
    print("  > Lines starting with 'Observation:' = Tool results")
    print("-"*60)

    # Get the research topic from the user
    # input() pauses the program and waits for the user to type something
    topic = input("\nEnter a research topic: ").strip()

    # If the user just pressed Enter without typing anything, use a default
    if not topic:
        topic = "latest developments in artificial intelligence 2024"
        print(f"No topic entered. Using default: '{topic}'")

    print(f"\nResearching: '{topic}'")
    print("-"*60)
    print("AGENT THINKING (verbose output):\n")

    # ---------------------------------------------------------------------------
    # STEP 8: INVOKE THE AGENT
    # ---------------------------------------------------------------------------
    #
    # agent_executor.invoke() starts the agent loop.
    # We pass a dict with "input" key — this maps to {input} in our prompt.
    #
    # What happens internally:
    #   1. The prompt is filled in with our topic
    #   2. Claude receives the prompt and writes "Thought: ..."
    #   3. If Claude writes "Action: tavily_search", the executor calls Tavily
    #   4. The search results become the "Observation"
    #   5. Claude sees the observation and writes another "Thought: ..."
    #   6. This repeats until Claude writes "Final Answer: ..."
    #   7. invoke() returns with the final answer

    try:
        result = agent_executor.invoke({
            "input": f"Research this topic and provide a comprehensive summary: {topic}"
        })
    except Exception as e:
        # If something goes wrong (network error, API limit, etc.), tell the user
        print(f"\nERROR: The agent encountered a problem: {e}")
        print("Possible causes:")
        print("  - Invalid API key")
        print("  - Network connectivity issue")
        print("  - Tavily API limit reached")
        sys.exit(1)

    # ---------------------------------------------------------------------------
    # STEP 9: DISPLAY THE RESULTS
    # ---------------------------------------------------------------------------

    print("\n" + "="*60)
    print("   RESEARCH COMPLETE")
    print("="*60)

    # result["output"] contains the agent's Final Answer
    print(result["output"])

    # Show a summary of how many steps the agent took
    # result["intermediate_steps"] is a list of (action, observation) tuples
    steps_taken = len(result.get("intermediate_steps", []))
    print(f"\n--- Agent used {steps_taken} search step(s) to gather this information ---")

    print("\n" + "="*60)
    print("   TIP: Run again with a different topic to see the agent")
    print("   adapt its search strategy each time!")
    print("="*60 + "\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
#
# This is a Python convention: code inside `if __name__ == "__main__":` only
# runs when you execute this file directly (python web_research_agent.py).
# It does NOT run if another file imports this file as a module.

if __name__ == "__main__":
    run_research_agent()
