# Session Transcript: Project 10 — Research-Writer Multi-Agent Team

**Course:** DevOps AI Course — Phase 4: Multi-Agent Systems
**Session Date:** Day 22 of the course
**Duration:** Approximately 75 minutes
**Student Background:** Completed Phases 1–3 (Claude API, RAG, LangChain agents, FastAPI, ChromaDB)

---

## Session Start

**Instructor:** Today is a big day. You have been building single AI agents so far — one model, one job, one response. Today you are going to build a team of agents that work together. This is called a multi-agent system, and it is the architecture that most serious AI applications use in production.

**Student:** When you say "team of agents" — do you mean multiple separate AI instances running at the same time?

**Instructor:** Exactly right. Each agent is its own call to the Claude API with its own system prompt, its own personality, its own specialization. The agents do not talk to each other directly — they communicate through a shared data structure we call "state."

**Student:** So it is like a shared database between them?

**Instructor:** That is a great analogy. Think of state as a shared whiteboard in a meeting room. The Researcher writes their notes on the whiteboard. The Writer walks in, reads those notes, and writes the article. They never had a face-to-face conversation — they communicated through the whiteboard.

**Student:** That makes sense. And LangGraph is the thing that manages the whiteboard?

**Instructor:** LangGraph manages the whiteboard AND the schedule — it decides who works when, in what order, and what happens when one agent finishes and the next one needs to start.

---

## Setting Up the Environment

**Instructor:** Let's start by installing the dependencies.

```bash
pip install -r requirements.txt
```

**Student:** It is installing... done. I see it installed LangGraph, LangChain, and something called tavily-python. What is Tavily?

**Instructor:** Tavily is a search engine built specifically for AI agents. Unlike Google, which returns a web page you have to navigate, Tavily returns clean, structured text that an AI can immediately read and process. It is perfect for the Researcher agent.

**Student:** Got it. So I need a Tavily API key too?

**Instructor:** Yes. Go to tavily.com, create a free account, and grab your API key. The free tier gives you 1,000 searches a month — more than enough for this course.

*[Student gets both API keys and sets up .env file]*

---

## Understanding the State

**Instructor:** Before we look at the agents, let us look at the state definition. Open `research_writer_team.py` and find the `ResearchWriterState` class.

**Student:** Okay, I see it. It is a TypedDict with: topic, research_notes, draft_article, final_article, review_feedback, revision_count, approved. What is TypedDict?

**Instructor:** TypedDict is Python's way of defining a dictionary with specific expected keys and types. It is like a contract — you are saying "this dictionary will always have these fields." LangGraph uses it to understand the shape of your state.

**Student:** And every agent can read and write to all of these fields?

**Instructor:** Yes, but by convention, each agent only touches the fields it is responsible for. The Researcher writes to `research_notes`. The Writer writes to `draft_article`. The Reviewer writes to `approved` and `review_feedback`. This discipline keeps the system predictable.

---

## The "Aha Moment" — Different Personalities

**Instructor:** Now look at the system prompts. Find `RESEARCHER_SYSTEM_PROMPT` and `WRITER_SYSTEM_PROMPT`.

**Student:** Okay... The Researcher's prompt says "be thorough and cite sources" and "format your notes clearly." The Writer's prompt says "write an engaging introduction" and "smooth transitions between ideas." These are completely different instructions.

**Instructor:** That is the key insight of this whole project. Same underlying model — Claude claude-opus-4-6. Different instructions = different behavior = different specialization. The Researcher will be dry, factual, structured. The Writer will be engaging, flowing, literary.

**Student:** Oh wow. So the "agent" is basically just the system prompt?

**Instructor:** The system prompt is the agent's *identity*. Combined with the tools it has access to — the Researcher has a search tool, the Writer has no tools — you get a fully specialized worker.

**Student:** That is kind of mind-blowing. I thought there would be more to it. Like different model weights or something.

**Instructor:** Nope. System prompt + tools = agent specialization. The power is in how you define the identity and what capabilities you give it. This is why prompt engineering is so important for multi-agent systems.

---

## Running the System for the First Time

**Instructor:** Let's run it. Execute the script and enter a topic when prompted.

```bash
python research_writer_team.py
```

**Student:** It is asking for a topic. I will try... "The rise of electric vehicles in 2024."

*[System begins running]*

```
🚀 RESEARCH-WRITER MULTI-AGENT TEAM 🚀

Starting research and writing pipeline for topic:
   "The rise of electric vehicles in 2024"

============================================================
🔍 Researcher is searching...
   Topic: The rise of electric vehicles in 2024
============================================================
   Searching the web for information...
   Found search results (9847 characters of data)
```

**Student:** It found almost 10,000 characters of search results! Tavily returns that much?

**Instructor:** Tavily aggregates multiple search results and returns the full text content, not just snippets. That is why it is better for AI agents than a regular search API.

*[Research continues...]*

```
📋 Research Notes Preview (first 500 chars):
----------------------------------------
## Research Notes: The Rise of Electric Vehicles in 2024

### Key Facts
- Global EV sales reached 14 million units in 2023, up 35% year-over-year
- China leads with 60% of global EV sales
- Tesla remains the largest EV manufacturer by revenue globally
- Battery costs have fallen 90% since 2010, now averaging $139/kWh
- The EU announced a ban on new petrol and diesel car sales by 2035
----------------------------------------
```

**Student:** Those are real statistics! The agent actually found and organized real data.

**Instructor:** That is the Researcher doing its job. Notice the format — headers, bullet points, statistics with numbers. That is exactly what the system prompt told it to produce.

---

## Watching the Handoff

*[Workflow continues to the Writer node]*

```
============================================================
✍️  Writer is drafting...
============================================================
   Writing first draft from research notes...

📄 Draft Article Preview (first 400 chars):
----------------------------------------
# Electric Vehicles Are Reshaping the World's Roads

Something remarkable is happening on the world's streets. Quietly, steadily,
and with increasing speed, electric vehicles are replacing the internal
combustion engines that have powered transportation for over a century.
In 2024, that shift is accelerating faster than most experts predicted.
----------------------------------------
```

**Student:** Oh this is really different! The Researcher wrote in bullet points and the Writer wrote like a magazine article. Same data, completely different presentation.

**Instructor:** That is the handoff in action. The Researcher structured information for clarity and factual accuracy. The Writer transformed that structure into narrative prose designed for human readers. Each agent played to its strengths.

**Student:** And they never actually talked to each other?

**Instructor:** Never directly. The Researcher wrote to `state["research_notes"]`. The Writer read from `state["research_notes"]`. The state was the middleman.

---

## The Review Loop

*[Workflow continues to Review node]*

```
============================================================
🔎 Review Agent is checking quality...
============================================================
```

**Student:** Wait, there is a third agent I did not notice — the Review Agent?

**Instructor:** Yes! This is what separates a good multi-agent system from a great one. Quality control. The Review Agent reads both the research notes AND the draft article, then decides if the article adequately covers the research.

**Student:** What happens if it fails the review?

**Instructor:** The conditional edge kicks in. The routing function checks `state["approved"]` — if False, it routes to the Revise node, which sends it back to the Writer with feedback. The Writer then revises with the specific feedback in mind.

*[Review result appears]*

```
   ✅ Article APPROVED by reviewer!

   ➡️  Routing: Article approved → going to FINISH
```

**Student:** It passed on the first try. What would have happened if it failed?

**Instructor:** Let us look at the conditional routing code:

```python
def should_revise(state: ResearchWriterState) -> str:
    if state.get("approved", False):
        return "finish"
    else:
        return "revise"
```

If `approved` is False, it returns the string `"revise"`. LangGraph looks that up in the edge mapping and goes to the revise node. The revise node routes back to write. The write node detects `revision_count > 0` and writes a revised version using the feedback.

**Student:** And the `revision_count >= 2` check prevents an infinite loop?

**Instructor:** Exactly. That is a circuit breaker. Even if the reviewer is never satisfied, after 2 revisions we force approval and move on. Without that, the system could loop forever and consume your entire API budget.

---

## Reading the Final Output

*[Workflow finishes]*

```
============================================================
🎉 Finalizing and saving article...
============================================================

📁 Article saved to: output/the_rise_of_electric_vehicles_in_2024_20260312_143022.txt

============================================================
FINAL ARTICLE:
============================================================

# Electric Vehicles Are Reshaping the World's Roads

Something remarkable is happening on the world's streets. Quietly, steadily,
and with increasing speed, electric vehicles are replacing the internal
combustion engines that have powered transportation for over a century.
In 2024, that shift is accelerating faster than most experts predicted.

Global sales of electric vehicles reached 14 million units in 2023 — a 35%
jump from the previous year — and 2024 looks set to surpass even that
milestone. China continues to lead the charge, accounting for 60% of global
EV purchases, driven by aggressive government incentives and a domestic
industry that has matured faster than anyone anticipated.

The economics are increasingly compelling. Battery costs, which stood at
roughly $1,200 per kilowatt-hour in 2010, have plummeted by 90% to around
$139 today. That decline has been the single most important factor in making
EVs price-competitive with conventional vehicles...

[Article continues for 400 words]
============================================================
```

**Student:** That is a genuinely good article. It reads like something from a technology magazine.

**Instructor:** And it only took about 45 seconds total. Think about what a team of human researchers and writers would need to produce something comparable.

---

## Understanding the Business Value

**Student:** I can see how this would be useful for content marketing. But where else is this used?

**Instructor:** Automated journalism is the clearest example. The Associated Press uses AI to generate thousands of financial reports per year. When a company publishes quarterly earnings, an AI system researches the data and writes the article within seconds of the data being released.

**Student:** Humans could not keep up with that volume.

**Instructor:** Exactly. The other big use case is internal knowledge management. Imagine a company where every meeting is transcribed, and after each meeting, a Researcher agent extracts action items and decisions, and a Writer agent produces a clean meeting summary that goes into the company wiki. Zero human effort, perfect documentation.

**Student:** That is something I could actually build for my current job.

---

## Debugging a Revision Loop

**Instructor:** Let me show you what happens when the review fails. Change the review prompt temporarily to always return `NEEDS_REVISION` and run again. Watch what happens.

*[Student modifies the review_node temporarily to always return "NEEDS_REVISION"]*

*[Runs system again...]*

```
============================================================
🔎 Review Agent is checking quality...
============================================================
   ⚠️  Article needs revision
   ➡️  Routing: Needs revision → going to REVISE (count: 1)

============================================================
🔄 Sending back for revision #1...
============================================================
   The writer will now revise the article based on the feedback.

============================================================
✍️  Writer is drafting...
============================================================
   Revision #1 - incorporating feedback...

============================================================
🔎 Review Agent is checking quality...
============================================================
   ⚠️  Article needs revision
   ➡️  Routing: Needs revision → going to REVISE (count: 2)

============================================================
🔄 Sending back for revision #2...
============================================================

============================================================
✍️  Writer is drafting...
============================================================
   Revision #2 - incorporating feedback...

============================================================
🔎 Review Agent is checking quality...
============================================================
   Max revisions reached (2). Approving article as-is.
   ✅ Article APPROVED by reviewer!
```

**Student:** The circuit breaker kicked in after exactly 2 revisions. It stopped the loop.

**Instructor:** That is what `if current_revision_count >= 2: return {"approved": True}` does. In production systems, you would also log when the circuit breaker trips so you can review those cases later and improve your agents.

---

## Wrap-Up

**Instructor:** What is your biggest takeaway from today?

**Student:** Honestly, the thing that surprised me most is how simple the "specialization" is. I was expecting something complex — separate models, different weights, maybe separate API calls to different services. But it is just... different system prompts.

**Instructor:** That simplicity is the insight. The system prompt is incredibly powerful. In Phase 1, we used it to set basic behavior. But when you combine it with tool access and graph routing, you can create genuinely specialized workers.

**Student:** And LangGraph is what makes the coordination possible?

**Instructor:** LangGraph provides the infrastructure: shared state, defined workflow, conditional routing. Without it, you would have to write all of that coordination logic yourself. LangGraph handles the plumbing so you can focus on the agents.

**Student:** I want to try adding a fourth agent — an SEO optimizer that takes the final article and adds headings and keywords.

**Instructor:** That is exactly the right next experiment. Add a node, wire it in after `finish`, write a new system prompt. You already know everything you need to do it.

---

## Homework

1. Run the system with three different topics and compare the outputs
2. Read the saved `.txt` files in `output/` and evaluate quality
3. Add an Editor agent between Writer and Reviewer that focuses on grammar and style
4. Modify the review criteria to check for minimum word count
5. Try making the review always fail once to observe the revision loop in action

---

*End of Session — Project 10 Complete*
*Next: Project 11 — Code Review Pipeline (three agents, security vulnerabilities, CI/CD patterns)*
