# research_writer_team.py
# Project 10: Multi-Agent Research and Writer Team
# This file demonstrates how two specialized AI agents work together:
# Agent 1 (Researcher) finds information, Agent 2 (Writer) turns it into an article.
# This is the "handoff" pattern - one agent's output becomes another agent's input.

# Standard library imports
import os           # Used to create directories and manage file paths
import json         # Used to parse structured data from agent responses
from datetime import datetime  # Used to timestamp the output file

# Load environment variables from the .env file (API keys)
from dotenv import load_dotenv
load_dotenv()  # This reads ANTHROPIC_API_KEY and TAVILY_API_KEY from .env

# TypedDict lets us define the exact shape of our shared state object
from typing import TypedDict, Optional

# LangGraph is the framework that connects multiple agents into a workflow
from langgraph.graph import StateGraph, END  # StateGraph = the workflow, END = terminal node

# ChatAnthropic is the LangChain wrapper around Claude API
from langchain_anthropic import ChatAnthropic

# HumanMessage and SystemMessage define how we talk to Claude
from langchain_core.messages import HumanMessage, SystemMessage

# TavilySearchResults is a tool that lets agents search the web
from langchain_community.tools.tavily_search import TavilySearchResults

# ============================================================
# STEP 1: DEFINE THE SHARED STATE
# ============================================================
# State is the "shared memory" that all agents read from and write to.
# Think of it like a shared Google Doc - every agent can see the full history.

class ResearchWriterState(TypedDict):
    # The topic that the user wants researched and written about
    topic: str

    # The research notes produced by the Researcher agent
    # Optional because it starts empty - gets filled in during the workflow
    research_notes: Optional[str]

    # The first draft article produced by the Writer agent
    draft_article: Optional[str]

    # The final polished article after any revisions
    final_article: Optional[str]

    # Feedback from the Review node explaining what needs improvement
    review_feedback: Optional[str]

    # How many times we have gone through the revision loop
    # We use this to prevent infinite loops (max 2 revisions)
    revision_count: int

    # Whether the review node approved the article (True = done, False = needs revision)
    approved: bool


# ============================================================
# STEP 2: INITIALIZE THE AI MODEL AND TOOLS
# ============================================================

# Create the Claude model instance that all agents will use
# claude-opus-4-6 is the most capable model - good for complex reasoning
llm = ChatAnthropic(
    model="claude-opus-4-6",           # The model to use
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),  # API key from .env file
    max_tokens=2048                    # Maximum length of each response
)

# Create the Tavily web search tool
# Tavily is an AI-optimized search engine - much better than raw Google results
# k=5 means we get 5 search results per query
search_tool = TavilySearchResults(
    api_key=os.getenv("TAVILY_API_KEY"),  # Tavily API key from .env file
    max_results=5                          # Get 5 search results per search
)


# ============================================================
# STEP 3: DEFINE AGENT SYSTEM PROMPTS (PERSONALITIES)
# ============================================================
# A system prompt is like a job description for an agent.
# It defines who they are, what they do, and how they think.
# This is what makes each agent "specialized" - different instructions = different behavior.

# Researcher agent's identity and instructions
RESEARCHER_SYSTEM_PROMPT = """You are an expert researcher. Your job is to find information and compile factual notes. Be thorough and cite sources.

When given a topic to research:
1. Think about what key aspects need to be covered
2. Use the information provided to compile structured research notes
3. Include: key facts, statistics, important names/dates, multiple perspectives
4. Always cite where information came from
5. Format your notes clearly with sections and bullet points
6. Be objective and accurate - do not editorialize

Your output should be detailed research notes that another writer can use to create an article."""

# Writer agent's identity and instructions
WRITER_SYSTEM_PROMPT = """You are a professional content writer. Your job is to take research notes and transform them into polished, well-structured articles.

When given research notes:
1. Write a compelling introduction that hooks the reader
2. Organize information into logical paragraphs with clear flow
3. Use smooth transitions between ideas
4. Write in an engaging but informative style (not academic, not sensational)
5. Include a strong conclusion with key takeaways
6. Target length: approximately 400 words
7. Do NOT invent facts - only use what is in the research notes

Your output should be a complete, polished article ready for publication."""


# ============================================================
# STEP 4: DEFINE THE AGENT NODES
# ============================================================
# Each "node" in LangGraph is a function that:
# - Receives the current state
# - Does some work (calls an AI agent)
# - Returns updates to the state
# The graph calls these nodes in the order defined by the edges.

def research_node(state: ResearchWriterState) -> dict:
    """
    This node runs the Researcher agent.
    It takes the topic from state, searches the web, and produces research notes.
    Returns: updated state with research_notes filled in
    """
    # Tell the user which agent is working right now
    print("\n" + "="*60)
    print("🔍 Researcher is searching...")
    print(f"   Topic: {state['topic']}")
    print("="*60)

    # Use the search tool to find real information about the topic
    # search_tool.run() calls the Tavily API and returns search results
    print("   Searching the web for information...")
    try:
        # Perform the web search using the topic as the search query
        search_results = search_tool.run(state["topic"])
        print(f"   Found search results ({len(str(search_results))} characters of data)")
    except Exception as e:
        # If search fails (e.g., no API key), use a placeholder
        print(f"   Search failed: {e}")
        print("   Using placeholder data for demonstration...")
        search_results = f"[Search unavailable - demonstrating with placeholder] Topic: {state['topic']}"

    # Now ask the Researcher agent to analyze the search results and write structured notes
    # We pass the search results as context so the agent has real data to work with
    researcher_prompt = f"""Please research the following topic and compile thorough research notes.

TOPIC: {state['topic']}

SEARCH RESULTS FROM THE WEB:
{search_results}

Using the search results above, please compile detailed research notes including:
- Key facts and main points
- Important statistics or data
- Historical context or background
- Current state or recent developments
- Multiple perspectives if relevant
- Source citations from the search results

Format your notes clearly with headers and bullet points."""

    # Send the request to Claude (the Researcher agent)
    # We pass both the system prompt (who the agent is) and the human message (what to do)
    response = llm.invoke([
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),  # Agent's identity
        HumanMessage(content=researcher_prompt)            # The task
    ])

    # Extract the text content from the response
    research_notes = response.content

    # Show a preview of the research notes in the terminal
    print("\n📋 Research Notes Preview (first 500 chars):")
    print("-" * 40)
    print(research_notes[:500] + "..." if len(research_notes) > 500 else research_notes)
    print("-" * 40)
    print(f"   Total research notes: {len(research_notes)} characters")

    # Return the update to state - only return what changed
    return {
        "research_notes": research_notes,  # The new research notes
        "revision_count": 0,               # Reset revision counter at the start
        "approved": False                   # Article not yet approved
    }


def write_node(state: ResearchWriterState) -> dict:
    """
    This node runs the Writer agent.
    It takes the research notes from state and produces a draft article.
    Returns: updated state with draft_article filled in
    """
    # Tell the user which agent is working right now
    print("\n" + "="*60)
    print("✍️  Writer is drafting...")
    print("="*60)

    # Check if this is a revision pass (revision_count > 0 means we've been here before)
    is_revision = state.get("revision_count", 0) > 0

    if is_revision:
        # This is a revision - include the feedback so the writer knows what to fix
        print(f"   Revision #{state['revision_count']} - incorporating feedback...")
        writer_prompt = f"""Please write a polished article based on these research notes.

RESEARCH NOTES:
{state['research_notes']}

PREVIOUS DRAFT:
{state.get('draft_article', 'No previous draft')}

REVISION FEEDBACK:
{state.get('review_feedback', 'No feedback provided')}

Please revise the article to address all the feedback points while keeping the strengths of the previous draft.
Write a complete, polished article of approximately 400 words."""
    else:
        # This is the first draft - just write from the research notes
        print("   Writing first draft from research notes...")
        writer_prompt = f"""Please write a polished article based on these research notes.

RESEARCH NOTES:
{state['research_notes']}

Write a complete, engaging article of approximately 400 words that covers the key points from the research.
Make it informative, well-structured, and suitable for a general audience."""

    # Send the request to Claude (the Writer agent)
    response = llm.invoke([
        SystemMessage(content=WRITER_SYSTEM_PROMPT),  # Writer's identity
        HumanMessage(content=writer_prompt)            # The task
    ])

    # Extract the draft article from the response
    draft_article = response.content

    # Show a preview of the draft article in the terminal
    print("\n📄 Draft Article Preview (first 400 chars):")
    print("-" * 40)
    print(draft_article[:400] + "..." if len(draft_article) > 400 else draft_article)
    print("-" * 40)
    print(f"   Total draft length: {len(draft_article)} characters")

    # Return the updated state with the new draft
    return {"draft_article": draft_article}


def review_node(state: ResearchWriterState) -> dict:
    """
    This node performs quality review of the draft article.
    It checks if the article is good enough to publish or needs revision.
    Returns: updated state with approved=True/False and feedback
    """
    # Tell the user which agent is working right now
    print("\n" + "="*60)
    print("🔎 Review Agent is checking quality...")
    print("="*60)

    # Get the current revision count to decide if we should force approval
    current_revision_count = state.get("revision_count", 0)

    # If we have already done 2 revisions, force approval to prevent infinite loops
    # This is an important safety mechanism in all multi-agent systems
    if current_revision_count >= 2:
        print("   Max revisions reached (2). Approving article as-is.")
        return {
            "approved": True,
            "final_article": state["draft_article"],
            "review_feedback": "Max revisions reached. Article approved."
        }

    # Ask Claude to review the article quality
    # We give it specific criteria to check against
    review_prompt = f"""Please review this article for quality. The article is about: {state['topic']}

RESEARCH NOTES (what facts should be in the article):
{state['research_notes'][:1000]}...

DRAFT ARTICLE:
{state['draft_article']}

Please evaluate:
1. Does the article cover the key facts from the research notes?
2. Is it well-structured with clear introduction, body, and conclusion?
3. Is it approximately 400 words (check length)?
4. Is it engaging and readable for a general audience?
5. Are there any factual errors or missing important information?

Respond in this exact format:
VERDICT: APPROVED or NEEDS_REVISION
FEEDBACK: [Your specific feedback here - be constructive and specific]
STRENGTHS: [What the article does well]"""

    # Use Claude to review the article
    response = llm.invoke([
        SystemMessage(content="You are a senior editor reviewing content for quality and accuracy."),
        HumanMessage(content=review_prompt)
    ])

    review_text = response.content

    # Parse the verdict from the review response
    # We look for "APPROVED" or "NEEDS_REVISION" in the response text
    if "VERDICT: APPROVED" in review_text or "APPROVED" in review_text.upper():
        approved = True
        print("   ✅ Article APPROVED by reviewer!")
    else:
        approved = False
        print("   ⚠️  Article needs revision")

    # Extract the feedback section from the review
    # This will be passed to the Writer if revision is needed
    feedback_start = review_text.find("FEEDBACK:")
    if feedback_start != -1:
        feedback = review_text[feedback_start:]  # Everything from FEEDBACK: onwards
    else:
        feedback = review_text  # Use full review if we can't find the FEEDBACK: marker

    print(f"   Review feedback: {feedback[:200]}...")

    # If approved, set the final article
    if approved:
        return {
            "approved": True,
            "final_article": state["draft_article"],
            "review_feedback": feedback
        }
    else:
        # Increment revision count so we track how many times we've revised
        return {
            "approved": False,
            "review_feedback": feedback,
            "revision_count": current_revision_count + 1  # Increment the counter
        }


def revise_node(state: ResearchWriterState) -> dict:
    """
    This node handles the revision path.
    It simply logs that we are going back to the writer for revision.
    The actual revision happens in write_node when revision_count > 0.
    Returns: state unchanged (write_node handles the actual revision)
    """
    # Tell the user we are going back for revision
    print("\n" + "="*60)
    print(f"🔄 Sending back for revision #{state.get('revision_count', 1)}...")
    print("="*60)
    print("   The writer will now revise the article based on the feedback.")

    # Return empty dict - no state changes needed here
    # The write_node will detect revision_count > 0 and use the feedback
    return {}


def finish_node(state: ResearchWriterState) -> dict:
    """
    This node is the final step in the workflow.
    It saves the finished article to a file and displays it.
    Returns: state with final_article confirmed
    """
    # Tell the user we are finishing up
    print("\n" + "="*60)
    print("🎉 Finalizing and saving article...")
    print("="*60)

    # Get the final article (either from approval or from draft if not yet set)
    final_article = state.get("final_article") or state.get("draft_article", "No article generated")

    # Create the output directory if it doesn't exist
    # exist_ok=True means no error if the directory already exists
    os.makedirs("output", exist_ok=True)

    # Create a safe filename from the topic
    # Replace spaces with underscores and remove special characters
    safe_topic = "".join(c if c.isalnum() or c in "_- " else "" for c in state["topic"])
    safe_topic = safe_topic.replace(" ", "_").lower()[:50]  # Limit to 50 chars

    # Add a timestamp so multiple runs don't overwrite each other
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/{safe_topic}_{timestamp}.txt"

    # Write the complete output to the file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"TOPIC: {state['topic']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Revisions: {state.get('revision_count', 0)}\n")
        f.write("\n" + "="*60 + "\n")
        f.write("RESEARCH NOTES\n")
        f.write("="*60 + "\n\n")
        f.write(state.get("research_notes", "No research notes") + "\n\n")
        f.write("="*60 + "\n")
        f.write("FINAL ARTICLE\n")
        f.write("="*60 + "\n\n")
        f.write(final_article + "\n")

    # Display the final article in the terminal
    print(f"\n📁 Article saved to: {filename}")
    print("\n" + "="*60)
    print("FINAL ARTICLE:")
    print("="*60)
    print(final_article)
    print("="*60)

    # Return the final article in state
    return {"final_article": final_article}


# ============================================================
# STEP 5: DEFINE THE ROUTING FUNCTION
# ============================================================
# This function decides which node to go to after the review node.
# This is called a "conditional edge" in LangGraph.

def should_revise(state: ResearchWriterState) -> str:
    """
    Routing function: decides whether to revise or finish.
    Called after review_node to determine the next step.
    Returns: "revise" to go back for revision, "finish" to end
    """
    # If the reviewer approved the article, we are done
    if state.get("approved", False):
        print("\n   ➡️  Routing: Article approved → going to FINISH")
        return "finish"  # This string must match the edge names we define below
    else:
        # Article needs revision - go back to the writer
        print(f"\n   ➡️  Routing: Needs revision → going to REVISE (count: {state.get('revision_count', 0)})")
        return "revise"  # This string must match the edge names we define below


# ============================================================
# STEP 6: BUILD THE LANGGRAPH WORKFLOW
# ============================================================
# Now we connect all the nodes together into a directed graph.
# Think of this like drawing a flowchart - boxes (nodes) connected by arrows (edges).

def build_workflow() -> StateGraph:
    """
    Builds and compiles the LangGraph workflow.
    Returns: a compiled graph ready to run
    """
    # Create a new StateGraph using our state type
    # This tells LangGraph what the shared state looks like
    workflow = StateGraph(ResearchWriterState)

    # ADD NODES: Register each function as a node in the graph
    workflow.add_node("research", research_node)  # Node name "research" → research_node function
    workflow.add_node("write", write_node)          # Node name "write" → write_node function
    workflow.add_node("review", review_node)        # Node name "review" → review_node function
    workflow.add_node("revise", revise_node)        # Node name "revise" → revise_node function
    workflow.add_node("finish", finish_node)        # Node name "finish" → finish_node function

    # SET ENTRY POINT: The workflow starts at the "research" node
    workflow.set_entry_point("research")

    # ADD EDGES: Define the flow between nodes (arrows in the flowchart)
    # research → write: after researching, the writer creates a draft
    workflow.add_edge("research", "write")

    # write → review: after writing, the reviewer checks quality
    workflow.add_edge("write", "review")

    # review → ??? : this is a CONDITIONAL edge - it depends on the review result
    # We call should_revise() to decide: "revise" or "finish"
    workflow.add_conditional_edges(
        "review",           # Starting node
        should_revise,      # The function that decides where to go
        {
            "revise": "revise",  # If should_revise returns "revise", go to "revise" node
            "finish": "finish"   # If should_revise returns "finish", go to "finish" node
        }
    )

    # revise → write: after the revise node, go back to the writer
    # This creates a loop: write → review → revise → write → review → ...
    workflow.add_edge("revise", "write")

    # finish → END: after finishing, the workflow is done
    workflow.add_edge("finish", END)

    # COMPILE: Turn the graph definition into an executable workflow
    compiled_workflow = workflow.compile()

    print("\n✅ Workflow built successfully!")
    print("   Graph: research → write → review → [revise → write]* → finish")

    return compiled_workflow


# ============================================================
# STEP 7: MAIN ENTRY POINT
# ============================================================

def run_research_writer_team(topic: str):
    """
    Main function to run the research-writer team for a given topic.
    This is the function you call to start the whole multi-agent process.
    """
    print("\n" + "🚀 "*20)
    print("RESEARCH-WRITER MULTI-AGENT TEAM")
    print("🚀 "*20)
    print(f"\nStarting research and writing pipeline for topic:")
    print(f"   \"{topic}\"")
    print("\nThis will use TWO specialized AI agents:")
    print("   1. 🔍 Researcher - finds and organizes information")
    print("   2. ✍️  Writer     - transforms research into an article")
    print("   3. 🔎 Reviewer   - checks quality and gives feedback")
    print("   4. 🔄 Reviser    - (if needed) sends back for improvement")

    # Build the workflow graph
    app = build_workflow()

    # Create the initial state to pass into the workflow
    # We only set topic - everything else starts as None/empty
    initial_state = {
        "topic": topic,              # The user's requested topic
        "research_notes": None,      # Will be filled by research_node
        "draft_article": None,       # Will be filled by write_node
        "final_article": None,       # Will be filled by finish_node
        "review_feedback": None,     # Will be filled by review_node
        "revision_count": 0,         # Start at 0 revisions
        "approved": False            # Not yet approved
    }

    # Run the workflow by invoking it with the initial state
    # LangGraph will automatically execute each node in the correct order
    print("\n⏳ Running multi-agent workflow... (this may take 30-60 seconds)")
    final_state = app.invoke(initial_state)

    # Workflow is complete - show summary
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETE!")
    print("="*60)
    print(f"   Topic: {final_state['topic']}")
    print(f"   Revisions made: {final_state.get('revision_count', 0)}")
    print(f"   Article length: {len(final_state.get('final_article', ''))} characters")
    print("   Check the output/ directory for the saved article.")

    return final_state


# ============================================================
# STEP 8: RUN IF EXECUTED DIRECTLY
# ============================================================

if __name__ == "__main__":
    # This block runs when you execute: python research_writer_team.py
    # Get the topic from the user
    print("Research-Writer Multi-Agent Team")
    print("-" * 40)
    print("Enter a topic for research and article writing.")
    print("Examples:")
    print("  - The history of artificial intelligence")
    print("  - How renewable energy works")
    print("  - The benefits of meditation")
    print()

    # Ask the user to enter a topic
    topic = input("Enter research topic: ").strip()

    # Validate that they entered something
    if not topic:
        print("No topic entered. Using default: 'The impact of artificial intelligence on healthcare'")
        topic = "The impact of artificial intelligence on healthcare"

    # Run the multi-agent team
    run_research_writer_team(topic)
