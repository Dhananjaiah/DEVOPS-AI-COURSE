# Project 10: Research-Writer Multi-Agent Team

## Welcome to Multi-Agent AI Systems

You have just crossed a major threshold. In Phase 1 through 3, you built single AI agents — one model doing one job. In this project, you are building a **team of AI agents** that collaborate, each specialized for a different part of the work.

This is how real AI systems are built in production today. The company Anthropic uses multi-agent architectures internally. OpenAI's products use them. Every major AI lab and most AI startups are moving toward agent teams because a team of specialists consistently outperforms one generalist.

---

## What You Will Build

A content production pipeline with two AI agents:

- **Researcher Agent** — searches the web for information, compiles structured notes with sources
- **Writer Agent** — takes those notes and transforms them into a polished 400-word article

These agents hand off work to each other. The Researcher does not write. The Writer does not search. Each does exactly one job, and they do it extremely well.

You will also build:
- A **Review Agent** that evaluates article quality
- A **revision loop** that sends work back if quality is insufficient
- A **safety mechanism** that prevents infinite revision loops

---

## Why Multi-Agent? The Core Concept

### The Specialization Problem

Imagine asking one employee to be a doctor, lawyer, accountant, and chef. They will be mediocre at all four. But hire a specialist for each role and suddenly you have excellent work across the board.

AI agents are the same. A single large language model asked to "research and write an article" will produce something decent. But if you give it a dedicated research persona and a dedicated writing persona, each with different instructions and different tools, the output quality increases dramatically.

### The Four Reasons Companies Use Multi-Agent Systems

**1. Specialization**
Each agent has a focused system prompt and specific tools. The Researcher has a search tool and is instructed to be factual and cite sources. The Writer has no tools but is instructed to be engaging and well-structured. They cannot bleed into each other's job.

**2. Parallel Work**
In more complex systems, agents can work simultaneously. While one agent searches for economic data, another searches for political context, and another searches for social trends. The results merge back together. This is the same efficiency gain as hiring multiple researchers instead of one.

**3. Quality Control**
You can add dedicated reviewer agents whose only job is to catch mistakes. In software, you have code review. In content, you have editors. In data science, you have QA. Multi-agent systems let you automate this entire quality control layer.

**4. Auditable Process**
With a single agent, you get one output. With a multi-agent pipeline, you can inspect each stage: what did the Researcher find? What did the first draft look like? What did the reviewer flag? This makes debugging and improvement dramatically easier.

---

## Architecture: The Supervisor vs. Peer-to-Peer Pattern

There are two main patterns for organizing multiple agents:

### Pattern 1: Supervisor Pattern
```
            [Supervisor Agent]
           /        |          \
    [Agent A]   [Agent B]   [Agent C]
```
One "boss" agent receives all tasks, breaks them down, assigns work to specialist agents, and synthesizes the results. The supervisor knows the big picture; the workers know their domain.

**Best for:** Complex tasks where the decomposition itself is non-trivial. When you are not sure upfront how to break down the work.

**Example:** A software project manager agent that breaks down a feature request and assigns subtasks to a coding agent, a testing agent, and a documentation agent.

### Pattern 2: Peer-to-Peer / Pipeline Pattern
```
[Agent A] → [Agent B] → [Agent C] → [Output]
```
Agents are arranged in a sequence like an assembly line. Each agent does its part and passes the result to the next. No boss agent needed.

**Best for:** Tasks where you know the steps in advance. Assembly lines, pipelines, workflows with clear stages.

**Example:** Research → Write → Review → Publish (exactly what you are building in this project).

### Which Did We Use?

We used the **Pipeline Pattern** with a feedback loop:

```
[Research] → [Write] → [Review] → [Finish]
                ↑           |
                └── [Revise]←┘  (only if review fails)
```

The feedback loop is what makes this more powerful than a simple linear pipeline. Quality control with the ability to correct mistakes is a hallmark of professional-grade systems.

---

## How LangGraph Works

LangGraph is a library that lets you define AI workflows as directed graphs. Think of it like drawing a flowchart and then having Python execute it.

### The Three Core Concepts

**1. State**
A shared dictionary that every agent reads from and writes to. Like a shared whiteboard in a meeting room. Every agent can see everything previous agents have written.

```python
class ResearchWriterState(TypedDict):
    topic: str
    research_notes: Optional[str]
    draft_article: Optional[str]
    final_article: Optional[str]
    revision_count: int
    approved: bool
```

When the Researcher finishes, it writes `research_notes` to state. When the Writer starts, it reads `research_notes` from state. This is how agents communicate — through shared state.

**2. Nodes**
Python functions that take state as input and return state updates as output. Each node represents one step in the workflow.

```python
def research_node(state: ResearchWriterState) -> dict:
    # Do research work...
    return {"research_notes": notes}  # Update only what changed
```

Notice: nodes return a dictionary with only the keys they want to update. LangGraph merges this back into the full state. You do not need to return unchanged fields.

**3. Edges**
Connections between nodes that define the execution order. Can be:
- **Fixed edges**: always go from A to B
- **Conditional edges**: go to different places depending on state

```python
# Fixed edge: always go from research to write
workflow.add_edge("research", "write")

# Conditional edge: go to revise or finish based on approval
workflow.add_conditional_edges("review", should_revise, {
    "revise": "revise",
    "finish": "finish"
})
```

---

## The Handoff Pattern Explained

The "handoff" is the moment one agent passes work to another. In human teams, this is when the researcher hands their notes to the writer. In our system, this happens through shared state.

```
Researcher runs → writes to state["research_notes"] → Researcher done
                                                              ↓
Writer starts → reads from state["research_notes"] → writes to state["draft_article"]
```

The beauty of this pattern: the Writer does not need to know anything about how the research was done. It just reads the notes. You could swap out the Researcher for a different research method (a database lookup, a PDF parser, a human input) and the Writer would not change at all.

This is called **decoupled architecture** — agents are independent and communicate only through the shared state interface.

---

## Code Walkthrough

### System Prompts Create Personalities

The most important line in any agent definition is the system prompt. It is the agent's identity:

```python
RESEARCHER_SYSTEM_PROMPT = """You are an expert researcher. Your job is to find
information and compile factual notes. Be thorough and cite sources..."""

WRITER_SYSTEM_PROMPT = """You are a professional content writer. Your job is to
take research notes and transform them into polished, well-structured articles..."""
```

Same underlying model (Claude). Completely different behavior because of different instructions. This is the essence of agent specialization.

### The Revision Loop and Safety Mechanisms

Without safety mechanisms, agents can loop forever. The review agent might always find something to fix. The writer might never fully satisfy the reviewer. You need to break the loop:

```python
# In review_node:
if current_revision_count >= 2:
    print("Max revisions reached. Approving article as-is.")
    return {"approved": True, ...}
```

This is called a **circuit breaker** pattern. All production multi-agent systems need them.

### How Conditional Edges Work

```python
def should_revise(state: ResearchWriterState) -> str:
    if state.get("approved", False):
        return "finish"   # Return the string name of the next node
    else:
        return "revise"   # Return the string name of the next node
```

The routing function returns a string. LangGraph looks up that string in the mapping you provided and goes to the corresponding node. The function has full access to state, so it can make decisions based on any data in the workflow.

---

## Project File Structure

```
project10-research-writer-team/
├── research_writer_team.py    # Main multi-agent system
├── requirements.txt           # Python dependencies
├── .env.example               # Template for API keys
├── .env                       # Your actual API keys (never commit this!)
├── output/                    # Generated articles are saved here
│   └── [topic_timestamp].txt  # Each run creates a new file
├── README.md                  # This file
└── TRANSCRIPT.md              # Session transcript
```

---

## Setup and Running

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Get Your API Keys

You need two API keys for this project:

**Anthropic API Key:**
1. Go to https://console.anthropic.com
2. Create an account or log in
3. Go to API Keys section
4. Create a new key

**Tavily API Key (for web search):**
1. Go to https://tavily.com
2. Create a free account
3. Get your API key from the dashboard
4. Free tier gives you 1,000 searches/month

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your real API keys:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
TAVILY_API_KEY=tvly-your-actual-key-here
```

### Step 4: Run the System

```bash
python research_writer_team.py
```

You will be prompted to enter a topic:
```
Enter research topic: The impact of AI on healthcare
```

Watch as each agent does its job in sequence.

---

## Sample Output

When you run the system, you will see output like this:

```
🚀 RESEARCH-WRITER MULTI-AGENT TEAM 🚀

Starting research and writing pipeline for topic:
   "The impact of artificial intelligence on healthcare"

This will use TWO specialized AI agents:
   1. 🔍 Researcher - finds and organizes information
   2. ✍️  Writer     - transforms research into an article
   3. 🔎 Reviewer   - checks quality and gives feedback

============================================================
🔍 Researcher is searching...
   Topic: The impact of artificial intelligence on healthcare
============================================================
   Searching the web for information...
   Found search results (8432 characters of data)

📋 Research Notes Preview (first 500 chars):
----------------------------------------
## Research Notes: AI in Healthcare

### Key Facts
- AI diagnostic systems achieve 94.5% accuracy in detecting diabetic retinopathy...
----------------------------------------
   Total research notes: 3241 characters

============================================================
✍️  Writer is drafting...
============================================================
   Writing first draft from research notes...

📄 Draft Article Preview (first 400 chars):
----------------------------------------
# How Artificial Intelligence is Transforming Modern Healthcare

The operating room of tomorrow may look very different from today's...
----------------------------------------

============================================================
🔎 Review Agent is checking quality...
============================================================
   ✅ Article APPROVED by reviewer!

============================================================
🎉 Finalizing and saving article...
============================================================

📁 Article saved to: output/the_impact_of_artificial_intelligence_on_healthcare_20260312_143022.txt
```

---

## Real World Applications

### Automated Journalism
Organizations like the Associated Press use AI to automatically generate financial earnings reports. When a company reports quarterly results, an AI system researches the data and writes the article — thousands of articles per day, impossible for human journalists to match in volume.

### Content Marketing at Scale
Companies need blog posts, social media content, email newsletters, product descriptions. A research-writer team can generate first drafts that human editors then refine. This reduces content production time from hours to minutes.

### Research Departments
Investment firms use AI research teams to scan thousands of documents, extract key data points, and produce market summaries. The AI reads everything; the analyst reads only the AI's curated output.

### Technical Documentation
Software companies use AI pipelines to read codebases, understand what the code does, and write documentation. The "code reader" agent is the researcher; the "documentation writer" agent is the writer.

---

## Extend This Project

Once you have the basic system working, here are ways to make it more sophisticated:

### Add an Editor Agent

Between the Writer and the Reviewer, add an Editor who specifically focuses on grammar, style, and word choice:

```python
# Add to the graph
workflow.add_node("edit", edit_node)
workflow.add_edge("write", "edit")    # Write → Edit
workflow.add_edge("edit", "review")   # Edit → Review
```

### Add a Fact-Checker Agent

After the Writer, add a Fact-Checker who cross-references the article claims against the original research notes:

```python
FACT_CHECKER_PROMPT = """You are a fact-checker. Compare the article claims
against the provided research notes. Flag any claim that is not supported
by the research notes."""
```

### Add an SEO Optimizer Agent

After approval, add an SEO agent who optimizes the article for search engines:

```python
SEO_PROMPT = """You are an SEO specialist. Given a finished article,
add appropriate headings, meta description, and keyword density improvements
without changing the article's substance."""
```

### Add Parallel Research

Instead of one researcher, use two or three researching different aspects simultaneously using LangGraph's parallel execution feature:

```python
# Research economic AND social AND technical aspects simultaneously
workflow.add_node("research_economic", economic_research_node)
workflow.add_node("research_social", social_research_node)
workflow.add_node("merge_research", merge_research_node)
```

### Save to a Database

Instead of writing to a text file, save articles to a database and track which topics have been covered. Build a content calendar management system.

---

## Key Terms Glossary

| Term | Meaning |
|------|---------|
| Multi-agent system | Multiple AI agents working together on a shared task |
| State | The shared dictionary that agents communicate through |
| Node | A function in the LangGraph workflow |
| Edge | A connection between nodes defining execution order |
| Conditional edge | An edge where the destination depends on state |
| Handoff | When one agent finishes and passes work to the next |
| System prompt | Instructions that define an agent's identity and behavior |
| Circuit breaker | A safety mechanism that prevents infinite loops |
| Pipeline pattern | Agents arranged in a linear sequence like an assembly line |
| Supervisor pattern | One boss agent that coordinates multiple worker agents |

---

## Common Errors and Solutions

### Error: "TAVILY_API_KEY not found"
**Solution:** Make sure you created a `.env` file (not just `.env.example`) and added your real Tavily key.

### Error: "anthropic.AuthenticationError"
**Solution:** Your Anthropic API key is missing or incorrect. Double-check it in the `.env` file.

### Error: "ModuleNotFoundError: No module named 'langgraph'"
**Solution:** Run `pip install -r requirements.txt` again. Make sure you are in the right virtual environment.

### Error: "RecursionError" or infinite loop
**Solution:** The circuit breaker in `review_node` should prevent this. If you modified the code, make sure `revision_count >= 2` check is still in place.

### Article quality seems low
**Solution:** Try more specific topics. Instead of "AI" try "AI applications in cancer detection 2024". More specific queries give better search results which give better articles.

---

## What You Learned in This Project

1. How to define shared state using TypedDict
2. How to create specialized agents with different system prompts
3. How to connect agents using LangGraph edges
4. How to create feedback loops with conditional edges
5. How to implement circuit breakers to prevent infinite loops
6. The handoff pattern for agent communication
7. How to save workflow outputs to files

---

## Next Project Preview

In Project 11, you will build a **Code Review Pipeline** — three agents that review code for bugs and security issues, write test cases, and then fix the code. You will see a real SQL injection vulnerability get detected and fixed automatically. This is the kind of system that DevOps teams are deploying in CI/CD pipelines today.

---

*Phase 4 | Project 10 of 12 | Multi-Agent Systems with LangGraph*
