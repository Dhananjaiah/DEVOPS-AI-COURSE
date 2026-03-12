# Learning Session Transcript — Project 4: Web Research Agent

**Student:** Alex (DevOps engineer, 3 years experience, learning AI integration)
**Instructor:** Jordan
**Session Goal:** Understand agents vs. chatbots, learn the ReAct pattern, run first agent

---

## Part 1: Setting the Stage

**Jordan:** Alright Alex, before we touch any code today — close your laptop for a second. I want to ask you something.

**Alex:** Sure, what's up?

**Jordan:** You've been using ChatGPT, right? For work stuff, documentation, whatever?

**Alex:** Yeah, all the time. It's great for writing Terraform docs and explaining error messages.

**Jordan:** Perfect. So here's my question: have you ever asked ChatGPT something like "find me the latest Kubernetes security vulnerabilities from this week"?

**Alex:** Oh yeah. And it always says something like "I don't have access to real-time information" or it just makes things up.

**Jordan:** Exactly. And do you know WHY it does that?

**Alex:** Because it was trained on data up to a certain date? Like a knowledge cutoff?

**Jordan:** Partly. But more fundamentally: because it's a chatbot. It generates text. It does not take actions. It cannot open a browser, call an API, or look anything up. It's a very smart text predictor that was trained on the internet — but it's frozen in time and it's isolated from the world.

**Alex:** Right. So what are we changing today?

**Jordan:** Today you're going to build something that CAN search the web. Autonomously. Without you telling it exactly what to search for or how many searches to do. It figures that out on its own.

**Alex:** Okay that sounds cool. Is that what an "agent" is?

**Jordan:** That's exactly what an agent is. Open your laptop — let's dig in.

---

## Part 2: Agents vs. Chatbots

**Jordan:** Here's the simplest way I can explain the difference. A chatbot is like a very knowledgeable colleague who is locked in a room with no internet, no phone, and no tools. You can slip a note under the door, they write back an answer from memory, and that's it.

**Alex:** And an agent is...?

**Jordan:** An agent is that same colleague, but now they have a computer, internet access, access to your company's database, and the ability to run scripts. You give them a goal — not a specific command, a goal — and they figure out how to achieve it.

**Alex:** Huh. So the difference is really about taking actions?

**Jordan:** Yes. And the ability to DECIDE which actions to take. That decision-making is the key part. You're not scripting every step. You're giving it a goal and tools, and it figures out the how.

**Alex:** What kind of tools are we talking about?

**Jordan:** In this project, just one tool: web search. But tools can be anything. Database queries. File operations. API calls. Running shell commands. Sending emails. Basically anything you can write as a Python function can become a tool.

**Alex:** So you could theoretically give it a tool to run `kubectl` commands?

**Jordan:** Yes, absolutely. That's exactly the kind of thing we'll build in later projects. For now we're starting simple — web search only.

---

## Part 3: The ReAct Pattern

**Jordan:** Okay let me draw you something. Have you heard of "chain of thought" prompting?

**Alex:** I've heard the term. Like getting Claude to think through problems step by step?

**Jordan:** Right. You've probably done it accidentally — you ask Claude to "think step by step" and suddenly it's way better at hard problems. ReAct is that idea taken further.

**Jordan:** ReAct stands for Reasoning + Acting. It's a loop. Every single iteration of the loop has this shape:

```
Thought:        "I need to find information about X. I'll search for it."
Action:         [name of the tool to call]
Action Input:   [what to pass to the tool]
Observation:    [what the tool returned]
```

**Alex:** And that repeats?

**Jordan:** Until the agent decides it has enough to answer. Then instead of writing "Action:", it writes "Final Answer:" and the loop stops.

**Alex:** So the "Thought" is just Claude talking to itself?

**Jordan:** Exactly. And this is the critical insight. Before acting, it reasons about what to do. This "thinking out loud" dramatically improves the quality of decisions. It's the difference between someone blurting out an answer versus taking a breath and thinking "okay what do I actually know here, what do I need, and what's my plan?"

**Alex:** That's surprisingly... human.

**Jordan:** Right? And it works. The research paper that introduced ReAct showed significant accuracy improvements on complex tasks just from adding this Thought step.

**Alex:** What does this look like in the actual terminal output?

**Jordan:** That's the fun part — let's look at the code and then run it so you can see for yourself.

---

## Part 4: Reading the Code Together

**Jordan:** Open `web_research_agent.py`. Don't be overwhelmed — we're going to read it top to bottom.

**Alex:** Okay, first import I see is `from langchain_anthropic import ChatAnthropic`. So this is like... a wrapped version of the Claude API?

**Jordan:** Exactly. In Phase 1 you used `anthropic.Anthropic()` directly. Here we use LangChain's wrapper because the agent framework expects a "LangChain-compatible" LLM. Same Claude, different packaging.

**Alex:** Makes sense. Next: `TavilySearchResults`. This is the web search tool?

**Jordan:** Yes. This is a pre-built tool — someone already wrote the code to call the Tavily API and format the results correctly. We just import it and configure it. `max_results=3` means we get the top 3 search results per query.

**Alex:** Why Tavily? Why not just use Google?

**Jordan:** Two reasons. First, Google's API is expensive for development — around $5 per 1000 queries. Tavily has a free tier. Second, and more importantly, Tavily is designed FOR LLM applications. It returns clean structured JSON. Google returns raw HTML that you'd have to parse. Tavily also returns pre-extracted summaries of each page. It's just way easier to feed into an LLM.

**Alex:** Oh that makes sense. Okay, next I see `create_react_agent` and `AgentExecutor`. What's the difference between those?

**Jordan:** Great question. `create_react_agent` is like the blueprint. It takes the LLM, the tools, and the prompt and produces an "agent object" — but that object doesn't DO anything yet. It's just configured.

**Alex:** And AgentExecutor is what actually runs it?

**Jordan:** Exactly. AgentExecutor is the runtime engine. It takes the blueprint, and when you call `.invoke()`, it actually runs the loop. It calls the LLM, parses the "Action:" text to know which tool to call, calls the tool, takes the result back to the LLM as an "Observation", and keeps going until it sees "Final Answer:".

**Alex:** So `create_react_agent` is the car, and `AgentExecutor` is the driver?

**Jordan:** I like that analogy. Or `create_react_agent` is the recipe, and `AgentExecutor` is the cook. Either way: blueprint vs. runtime.

**Alex:** And `verbose=True` — that's the one that prints all the thinking steps?

**Jordan:** Yes. NEVER remove that while you're learning. That visibility is everything. Once you can see the agent's reasoning, you can debug it, improve it, and understand why it does what it does. In production you'd turn it off, but for now — leave it on.

---

## Part 5: The Prompt Structure

**Jordan:** Let's look at the `RESEARCH_AGENT_PROMPT`. What do you notice about it?

**Alex:** It has these curly brace things. `{tools}`, `{tool_names}`, `{input}`, `{agent_scratchpad}`. Those are the placeholders?

**Jordan:** Yes. Those four are required for ANY ReAct agent to work. Let me explain each one:

**Jordan:** `{tools}` gets replaced with the descriptions of all your tools. So the LLM can see what tools are available and what they do.

**Alex:** So the agent literally reads the description to know what each tool is for?

**Jordan:** Exactly! That's why tool descriptions are so important. The agent has no other way to know what a tool does. We'll explore that deeply in Project 5 when you write your own tools.

**Jordan:** `{tool_names}` is just the list of tool names, used in the "Action should be one of [...]" part of the prompt.

**Jordan:** `{input}` is where your user's message goes.

**Jordan:** `{agent_scratchpad}` — this is the interesting one. This is where LangChain inserts all the previous Thought/Action/Observation history. So in each loop iteration, the LLM can see everything it's already done and found.

**Alex:** Without that, it would forget its previous searches?

**Jordan:** Completely. Every LLM call is stateless by default. The scratchpad is what creates the illusion of memory within a single run.

---

## Part 6: Running It

**Jordan:** Okay let's actually run it. You got your `.env` set up?

**Alex:** Yeah, I grabbed a free Tavily API key just now. Took like two minutes. I've got both keys in `.env`.

**Jordan:** Perfect. Run it.

```bash
python web_research_agent.py
```

**Alex:** Okay it's asking for a topic... let me type "Docker security best practices 2024"...

**Jordan:** Watch closely now.

**Alex:** Whoa. It printed:

```
> Entering new AgentExecutor chain...
Thought: I need to search for current Docker security best practices in 2024.
Action: tavily_search_results_json
Action Input: Docker security best practices 2024
```

And then it's calling the API...

**Alex:** And now there's this big block of JSON — these are the actual search results?

**Jordan:** Real search results, live from the web. Right now.

**Alex:** That's crazy. And now it's thinking again:

```
Thought: The results mention several practices including rootless containers
and image scanning. Let me search for more specific implementation details.
Action: tavily_search_results_json
Action Input: Docker rootless containers security implementation guide
```

**Jordan:** It decided to do a second search on its own! You didn't tell it to. It looked at the first results, realized it wanted more depth on a specific topic, and searched again.

**Alex:** I'm watching it decide. In real time.

**Jordan:** That's the agent loop. That's ReAct. The Thought step, the Action, the Observation, and then reasoning about whether it has enough or needs more.

**Alex:** And now... "Final Answer:" — oh it's writing the whole structured report. Overview, key findings, sources, everything.

**Jordan:** Just like the system prompt told it to. It followed the format instructions AND figured out how to gather the information. You just gave it the topic and stood back.

---

## Part 7: What Just Happened (Debrief)

**Alex:** Okay let me make sure I understand what just happened. I typed a topic. The agent searched the web twice — the second search it decided to do on its own. Then it compiled a structured report. And I can see all the thinking that happened in between.

**Jordan:** Perfect summary. What made you most surprised?

**Alex:** Honestly? That it decided to search a second time. I expected it to just take the first results and run with them. But it read the results, thought "I want more detail on this specific thing," and went back for more.

**Jordan:** That's the power of the ReAct pattern. The Thought step lets it evaluate what it has versus what it needs. A simple chain would just search once and be done. An agent reasons about whether it has enough.

**Alex:** What would happen if I gave it a super vague topic?

**Jordan:** Try it. Run it again and give it something like "AI".

**Alex:** Interesting — it generated several more focused search queries from that one word. It interpreted "AI" as a research goal and broke it down into sub-queries.

**Jordan:** Because the system prompt says "research this topic comprehensively." It's using its reasoning to figure out what a comprehensive research task looks like, even with minimal input.

---

## Part 8: Key Takeaways

**Jordan:** Before we wrap up, let me ask you this: how would you explain what we built today to a colleague who isn't technical?

**Alex:** I'd say... we built a program that can search the internet on its own and put together a research report. You give it a topic, it figures out what to search for, searches multiple times if it needs to, and gives you back a structured summary. You don't have to micromanage it.

**Jordan:** That's a great explanation. You just described an AI agent to a non-technical person.

**Alex:** I also want to say — seeing the `verbose=True` output made everything click. I've read about "chain of thought" and "ReAct" before but seeing it actually happen, watching the Thoughts and Actions print in real time... it became concrete instead of abstract.

**Jordan:** That's exactly why we leave verbose on when learning. The agent's reasoning is not magic — it's a structured loop you can read and follow.

**Alex:** What's next?

**Jordan:** Project 5. You've used a pre-built tool today. Next you're going to BUILD your own tools from scratch. Custom Python functions that the agent can use. That's where you go from "I can use existing agents" to "I can build any agent I need."

**Alex:** Let's go.

---

## Session Summary

**What Was Covered:**
- The difference between a chatbot (text generation, no actions) and an agent (decides and takes actions)
- What tools are in the agent context (callable functions with names and descriptions)
- The ReAct pattern: Thought → Action → Action Input → Observation → repeat
- Why Tavily is preferred over Google for LLM applications
- LangChain components: `ChatAnthropic`, `TavilySearchResults`, `create_react_agent`, `AgentExecutor`
- The four required prompt placeholders: `{tools}`, `{tool_names}`, `{input}`, `{agent_scratchpad}`
- Why `verbose=True` is essential for learning

**Student Highlights:**
- "I'm watching it decide. In real time." (seeing the agent's multi-step reasoning)
- Surprise that the agent autonomously decided to run a second search
- Connected the abstract concept of "chain of thought" to the concrete Thought steps in the output

**Next Session:** Project 5 — Building Custom Tools with the `@tool` decorator
