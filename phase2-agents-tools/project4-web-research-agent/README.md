# Project 4: Web Research Agent

## Phase 2 — Agents and Tools | Lesson 1 of 3

---

## What You Will Build

A fully autonomous web research agent. You give it a topic — it searches the web, reads the results, decides if it needs more information, searches again if necessary, and then hands you a structured research report. All on its own. No hand-holding.

This is your first real AI **agent**.

---

## Prerequisites

- Completed Phase 1 (basic Claude API calls, system prompts, ChromaDB RAG)
- Python 3.9 or higher installed
- A free Tavily API key (https://tavily.com — takes 30 seconds to sign up)
- Your Anthropic API key

---

## Setup

```bash
# Navigate to this project
cd phase2-agents-tools/project4-web-research-agent

# Install dependencies
pip install -r requirements.txt

# Copy the example env file
cp .env.example .env

# Open .env and add your real API keys
# ANTHROPIC_API_KEY=sk-ant-...
# TAVILY_API_KEY=tvly-...

# Run it
python web_research_agent.py
```

---

## Part 1: What Is an AI Agent?

### The Chatbot Model (What You Already Know)

In Phase 1, you built chatbots. Here is how they work:

```
You:     "What is DevOps?"
Claude:  "DevOps is a set of practices that combines..."
Done.
```

The chatbot responds and stops. It has **no ability to take actions**. It cannot search the web, open files, run code, or call APIs. It only generates text.

### The Agent Model (What This Project Teaches)

An agent is different. It can:

1. **Receive a goal** ("Research Kubernetes trends in 2024")
2. **Reason** about what to do ("I should search for recent articles")
3. **Take action** (call the Tavily search API)
4. **Observe the results** (read the search results)
5. **Reason again** ("I found some data but need more detail on X")
6. **Take another action** (search again with a refined query)
7. **Repeat** until it has enough information
8. **Deliver the final answer**

In plain English: **an agent is a program that can decide what actions to take and then take them.**

The key word is "decide." The agent is not following a fixed script. It is reasoning about the best next step at each moment.

### The Analogy

Think of the difference between:

- A **calculator** — you give it an exact formula, it computes it. (Chatbot)
- A **research assistant** — you give them a topic, they figure out where to look, search, read, decide if they need more, and come back with a report. (Agent)

You hire a research assistant because they can figure out **how** to do the task, not just execute a command.

---

## Part 2: What Are Tools?

In the agent world, a **tool** is any function the agent is allowed to call.

```
Tool Name:        tavily_search_results_json
Tool Description: Search the internet for current information on any topic.
                  Use this when you need recent facts, news, or data.
Tool Input:       A search query string
Tool Output:      A list of search results with titles, URLs, and content
```

The agent **reads the tool description** and decides when and how to use it. The agent never sees the tool's code — only its name and description. This is important: **the description IS the instruction manual for the tool.**

### Why Tavily Instead of Google?

| Feature | Google Search | Tavily |
|---------|--------------|--------|
| Developer API | Yes, but expensive ($5/1000 queries) | Free tier available |
| Response format | Raw HTML pages | Clean structured JSON |
| LLM-friendly | No — you'd have to parse HTML | Yes — designed for AI |
| Result quality | High | High (AI-optimized) |
| Rate limits | Strict | Generous on free tier |

Tavily returns results like:
```json
[
  {
    "url": "https://example.com/article",
    "content": "A clean summary of the article content...",
    "score": 0.95
  }
]
```

No HTML parsing needed. Perfect for feeding into an LLM.

---

## Part 3: The ReAct Pattern

ReAct was introduced in a 2022 research paper by Google and Stanford. The name stands for **Re**asoning + **Act**ing.

### The Loop

Every iteration of the ReAct loop has four parts:

```
Thought:        "I need to find information about X. I'll search for it."
Action:         tavily_search_results_json
Action Input:   "X recent developments 2024"
Observation:    [the actual search results appear here]
```

Then it loops:

```
Thought:        "The results mention Y. I should dig deeper into Y."
Action:         tavily_search_results_json
Action Input:   "Y detailed explanation"
Observation:    [more search results]
```

Until finally:

```
Thought:        "I now have enough information to write the summary."
Final Answer:   [the complete research report]
```

### Why This Works

The **Thought** step is pure reasoning — Claude is thinking out loud about what to do next. This "chain of thought" reasoning dramatically improves decision quality compared to just asking Claude to act without thinking first.

The **Action + Observation** cycle is how the agent stays grounded in real data. Instead of hallucinating facts, it actually retrieves them from the web.

### Visualizing the Loop

```
┌─────────────────────────────────────────┐
│              USER INPUT                  │
│   "Research quantum computing trends"    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│              THOUGHT                     │
│   "I should search for recent news      │
│    about quantum computing breakthroughs"│
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│              ACTION                      │
│   Tool: tavily_search_results_json      │
│   Input: "quantum computing 2024 news"  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│            OBSERVATION                   │
│   [Search results come back here]       │
│   - IBM releases 1000-qubit processor   │
│   - Google achieves quantum supremacy   │
└──────────────────┬──────────────────────┘
                   │
          ┌────────┴────────┐
          │  Need more info? │
          └────────┬────────┘
         YES       │        NO
          │        │         │
          ▼        │         ▼
     Loop back     │    FINAL ANSWER
     to THOUGHT    │    (structured summary)
                   │
```

---

## Part 4: Code Walkthrough

### The Full Architecture

```python
# 1. LLM: Claude does the reasoning
llm = ChatAnthropic(model="claude-opus-4-6", temperature=0.1)

# 2. Tools: What the agent can do
tools = [TavilySearchResults(max_results=3)]

# 3. Prompt: Instructions for how to behave and format responses
prompt = PromptTemplate.from_template("...")

# 4. Agent: The reasoning engine (blueprint)
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# 5. Executor: The runtime that runs the agent loop
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. Run it
result = agent_executor.invoke({"input": "Research AI trends"})
```

### Key Parameter: `verbose=True`

This is the most educational parameter in this project. When `verbose=True`, you see every Thought, Action, and Observation printed to your terminal as they happen. You watch the agent think.

Turn it off (`verbose=False`) for production. Keep it on when learning.

### Key Parameter: `max_iterations=10`

This prevents the agent from looping forever if something goes wrong. After 10 iterations, it stops and returns whatever it has. Most research tasks complete in 2-4 iterations.

### Key Parameter: `handle_parsing_errors=True`

Sometimes Claude will format its response slightly wrong (e.g., missing a newline). This parameter tells the executor to retry gracefully instead of crashing. Essential for production use.

### The Prompt Template

The ReAct prompt has four required placeholders:

```
{tools}              — replaced with tool descriptions
{tool_names}         — replaced with the list of tool names
{input}              — replaced with the user's question
{agent_scratchpad}   — replaced with the Thought/Action/Observation history so far
```

Never remove these placeholders. The agent loop breaks without them.

### Temperature: Why 0.1?

For research tasks, you want **accurate and consistent** answers, not creative ones. A temperature of 0.1 makes Claude stick close to the facts in its search results. Use higher temperatures (0.7-0.9) for creative writing tasks.

---

## Part 5: Sample Output

Here is what a real run looks like (with `verbose=True`):

```
============================================================
   WEB RESEARCH AGENT
   Powered by Claude + Tavily + LangChain ReAct
============================================================

Enter a research topic: Kubernetes in 2024

Researching: 'Kubernetes in 2024'
------------------------------------------------------------
AGENT THINKING (verbose output):

> Entering new AgentExecutor chain...
 Thought: I need to find recent and relevant information about Kubernetes in 2024.
 Let me search for the latest developments.
Action: tavily_search_results_json
Action Input: Kubernetes 2024 latest developments trends

Observation: [
  {
    "url": "https://kubernetes.io/blog/2024/...",
    "content": "Kubernetes 1.30 was released in April 2024, featuring..."
  },
  {
    "url": "https://thenewstack.io/kubernetes-2024...",
    "content": "In 2024, Kubernetes adoption continues to grow with..."
  }
]
 Thought: I have some good information. Let me search for more specific trends
 and adoption statistics.
Action: tavily_search_results_json
Action Input: Kubernetes adoption statistics enterprise 2024

Observation: [
  {
    "url": "https://cncf.io/reports/...",
    "content": "According to the CNCF survey, 96% of organizations are..."
  }
]
 Thought: I now have enough information to write a comprehensive summary.

Final Answer:
## Research Summary: Kubernetes in 2024

### Overview
Kubernetes remains the dominant container orchestration platform in 2024,
with continued growth in enterprise adoption and significant new features
in the 1.30 and 1.31 releases.

### Key Findings
- Kubernetes 1.30 (April 2024) introduced sidecar containers as stable
- 96% of organizations surveyed by CNCF are using or evaluating Kubernetes
- Platform engineering teams are increasingly abstracting Kubernetes complexity
- AI/ML workloads are driving new scheduling and resource management features
- Security hardening (Pod Security Admission) is now the default

### Sources
- https://kubernetes.io/blog/2024/...
- https://thenewstack.io/kubernetes-2024...
- https://cncf.io/reports/...

### Bottom Line
Kubernetes in 2024 is maturing from a "new technology" to foundational
infrastructure, with the focus shifting from adoption to operational
excellence and platform engineering.

> Finished chain.
============================================================
   RESEARCH COMPLETE
============================================================

--- Agent used 2 search step(s) to gather this information ---
```

---

## Part 6: Real World Use Cases

### 1. Competitive Intelligence

```
"Research what our top 3 competitors announced last week"
```

An agent can search for news about each competitor, aggregate findings, and deliver a briefing — a task that would take a human analyst 30-60 minutes.

### 2. Technology Evaluation

```
"Compare Kubernetes vs. Nomad for container orchestration:
 pros, cons, performance, and adoption"
```

Multiple searches, aggregated into a comparison table.

### 3. Incident Post-Mortem Research

```
"Find information about the recent CloudFlare outage and
 similar incidents in the past year"
```

The agent can find incident reports, identify patterns, and summarize lessons learned.

### 4. Learning Acceleration

```
"Explain Terraform best practices and find the top
 community resources for learning it"
```

Instant curated learning materials.

### 5. Client Briefings

Before a client meeting, run the agent on the client's company, industry trends, and recent news. Get a briefing doc in 60 seconds.

---

## Part 7: How LangChain Fits In

LangChain is a framework that makes it easier to build applications with LLMs. Think of it as "the plumbing" that connects all the pieces.

Without LangChain, you would have to:
- Manually format the ReAct prompt
- Parse Claude's "Action: ..." text to know which tool to call
- Call the tool yourself and format the result as an "Observation"
- Loop this manually until Claude says "Final Answer"
- Handle all the edge cases

LangChain handles all of that for you. `AgentExecutor` is the engine that runs the loop. `create_react_agent` sets up the prompt structure. You just define the tools and the goal.

---

## Part 8: Extend This Project

### Idea 1: Multiple Tools

Add more tools alongside `TavilySearchResults`:

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
tools = [search_tool, wiki_tool]
```

Now the agent can decide whether to search the web or search Wikipedia based on the query type.

### Idea 2: Save Reports to File

After the agent finishes, save the output:

```python
result = agent_executor.invoke({"input": topic})
filename = f"research_{topic[:30].replace(' ', '_')}.md"
with open(filename, "w") as f:
    f.write(result["output"])
print(f"Report saved to {filename}")
```

### Idea 3: Batch Research

Research multiple topics automatically:

```python
topics = [
    "Kubernetes 2024",
    "Terraform best practices",
    "DevOps trends 2024"
]
for topic in topics:
    result = agent_executor.invoke({"input": f"Research: {topic}"})
    # save each result to a separate file
```

---

## Part 9: What You Learned

By completing this project, you now understand:

**The Agent Model**
- The difference between a chatbot (responds) and an agent (decides and acts)
- The agent loop: goal → reason → act → observe → repeat

**Tools**
- What a tool is in the agent context (a callable function with a description)
- Why the tool description matters (the agent reads it to know when/how to use the tool)
- Why Tavily is preferred for web search in LLM applications

**The ReAct Pattern**
- Thought → Action → Action Input → Observation → repeat
- Why "thinking out loud" (the Thought step) improves agent performance
- How `verbose=True` lets you watch the agent's reasoning in real-time

**LangChain Mechanics**
- `ChatAnthropic` — LangChain's Claude wrapper
- `TavilySearchResults` — pre-built web search tool
- `create_react_agent()` — assembles the agent blueprint
- `AgentExecutor` — runs the agent loop
- `PromptTemplate` — structures the prompt with required placeholders

---

## Part 10: Quiz

Test your understanding. Try to answer before revealing the answers.

**Question 1:** What is the key difference between a chatbot and an agent?

<details>
<summary>Click to reveal answer</summary>

A chatbot generates a text response and stops. An agent can decide what actions to take, execute those actions using tools, observe the results, and repeat the cycle until a goal is achieved. The key difference is that an agent takes actions in the real world (or digital world), not just generates text.

</details>

---

**Question 2:** In the ReAct pattern, what is the purpose of the "Thought" step? Why not just skip straight to the Action?

<details>
<summary>Click to reveal answer</summary>

The "Thought" step is where the agent reasons about what to do next before doing it. Research shows this "chain of thought" reasoning significantly improves decision quality. Without it, the agent would act impulsively without thinking through whether its action is appropriate. The Thought step is the agent planning: "I need to search for X because I need information about Y to answer Z."

</details>

---

**Question 3:** What would happen if you removed the `{agent_scratchpad}` placeholder from the ReAct prompt template?

<details>
<summary>Click to reveal answer</summary>

The agent would lose its memory between iterations. The `{agent_scratchpad}` is where all previous Thought/Action/Observation steps are inserted. Without it, Claude would start each iteration not knowing what it had already done or found. It would repeat the same searches, lose track of its progress, and never be able to build toward a final answer.

</details>

---

## Vocabulary Reference

| Term | Plain English Definition |
|------|--------------------------|
| Agent | A program that can decide what actions to take and take them autonomously |
| Tool | A function the agent is allowed to call (has a name and description) |
| ReAct | Reasoning + Acting — the loop of Thought → Action → Observation |
| Agent Loop | The cycle of deciding, acting, and observing that repeats until the goal is done |
| AgentExecutor | The runtime engine that manages the agent loop in LangChain |
| Scratchpad | The growing history of all Thoughts, Actions, and Observations in a run |
| Verbose | A setting that prints the agent's internal reasoning so you can see it |
| max_iterations | A safety limit on how many loops the agent can run before stopping |
| temperature | How creative vs. factual Claude's responses are (0=factual, 1=creative) |
| Tavily | An AI-optimized web search API that returns clean structured results |

---

*Next Project: Project 5 — File Manager Agent (Building Custom Tools)*
