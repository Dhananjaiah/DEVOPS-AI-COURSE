# Project 7: Personal Assistant with Persistent Memory

## What You Will Build

A command-line personal assistant that **remembers you across sessions**. Tell it your name today, close the app, reopen it tomorrow — and it still knows who you are. This project teaches the single most important concept in agentic AI: **memory**.

---

## The Big Idea: Why Does Memory Matter?

Imagine hiring a brilliant assistant who forgets everything at the end of each day. Every morning you have to re-introduce yourself, re-explain your preferences, re-list your ongoing projects. Maddening, right?

That's exactly what a standard LLM is. Each time you start a new conversation, it has zero memory of your previous interactions. For a casual chatbot, that's acceptable. For a *useful* agent — one that helps you manage tasks, track preferences, learn your working style — it's a fatal limitation.

Every major AI assistant in production has solved this problem:
- **Siri and Alexa** remember your name, home address, favorite contacts
- **GitHub Copilot** learns your coding patterns over time
- **Microsoft Copilot** has access to your calendar, email history, and documents
- **Notion AI** operates within your entire workspace context

This project shows you *exactly* how that works — from scratch, with code you write yourself.

---

## Three Types of Memory in AI Systems

Before writing a single line of code, let's understand the three types of memory that AI systems use. These concepts come from cognitive psychology, borrowed to describe how AI agents retain information.

### 1. Episodic Memory — "What happened?"

Episodic memory is the record of specific events and experiences. For humans: "I remember meeting Sarah at the conference last Tuesday." For an AI agent: "The user told me they prefer dark mode on March 12th."

**In this project:** The conversation history (last 10 messages) is episodic memory. It's a sequential record of what was said, in order.

**Analogy:** A diary. You can flip back through specific entries, but you don't read the whole diary every time you want to remember something.

### 2. Semantic Memory — "What do I know?"

Semantic memory is general facts, divorced from the specific experience of learning them. For humans: "I know Paris is the capital of France" — you don't remember *when* you learned that. For an AI agent: "User's name is Alex" — stored as a fact, not tied to the specific message where it was mentioned.

**In this project:** The facts stored in ChromaDB are semantic memory. They're extracted, abstracted, and stored without the original conversational context.

**Analogy:** An index card box. Each card has one fact. You can search the box for relevant cards without reading every card.

### 3. Procedural Memory — "How do I do this?"

Procedural memory is skill-based knowledge — how to do things. For humans: riding a bike (you do it without thinking). For an AI agent: the system prompt that defines behavior, personality, and rules.

**In this project:** The system prompt that defines how the assistant behaves is procedural memory. It's set by the developer, not learned from the user.

**Analogy:** A job description. It tells the assistant how to act, not what to know about a specific user.

---

## Short-Term vs. Long-Term Memory: The Two-Layer Architecture

This project implements a **two-layer memory architecture** that mirrors how human memory works.

### Short-Term Memory (Working Memory)

- **What it is:** The last 10 messages of the current conversation
- **Where it lives:** A Python list in RAM — vanishes when the app closes
- **Why it matters:** Claude needs recent context to give coherent replies. If you say "what did I just say?" Claude needs the last few messages to answer
- **Limit:** 10 messages (5 user + 5 assistant exchanges)
- **Cost:** Every message in history is sent to the Claude API with each call, consuming tokens (and money)

**Human analogy:** The things you're actively thinking about right now. Your short-term memory holds about 7 items and fades within minutes.

### Long-Term Memory (Persistent Memory)

- **What it is:** Important facts extracted from conversations and stored in ChromaDB on disk
- **Where it lives:** A `./memory_db/` folder that persists between app restarts
- **Why it matters:** Allows the assistant to remember facts from *previous sessions*, not just the current conversation
- **How it works:** After each conversation turn, Claude reads the exchange and extracts memory-worthy facts (name, preferences, tasks)

**Human analogy:** Facts you've committed to memory — your friend's birthday, your boss's coffee preference — available even days or weeks later.

---

## How Vector Databases Enable Memory Retrieval

Here's where it gets interesting. We don't retrieve *all* memories before responding — that would be expensive and noisy. Instead, we do **semantic search**: find only the memories that are *relevant to what the user just said*.

### The Problem with Exact Match Search

Traditional databases use exact keyword matching:
```sql
SELECT * FROM memories WHERE text LIKE '%coffee%'
```

This would miss "I prefer hot beverages" when searching for coffee preferences. Synonyms, paraphrases, and related concepts are invisible to keyword search.

### How Vector Search Works

Vector databases like ChromaDB convert text to numerical representations called **embeddings** (or vectors). A vector is a list of hundreds of numbers that encodes the *meaning* of a sentence.

The magic: **sentences with similar meanings produce similar vectors**, even if they use different words.

Example:
- "I love coffee in the morning" → vector [0.23, -0.41, 0.88, ...]
- "The user enjoys hot beverages" → vector [0.21, -0.39, 0.85, ...]
- "My car is red" → vector [-0.55, 0.12, -0.33, ...]

The first two vectors are close together (similar meaning). The third is far away (unrelated meaning).

When the user asks "What do I like to drink?", ChromaDB:
1. Converts the query to a vector
2. Finds the stored vectors that are closest to the query vector
3. Returns the text that those close vectors represent

This is how we retrieve "I love coffee in the morning" when asked about drinks — without any keywords matching.

### Why This Matters for Memory

This means the assistant can retrieve relevant memories even when:
- The user asks in different words than they originally used
- The memory was recorded with different terminology
- The concept is related but not identical

This is semantic search, and it's the technology powering every modern search engine, recommendation system, and AI assistant.

---

## Why Persistence Matters

Without persistence, every app restart is amnesia. With persistence:

1. User tells the assistant "I'm a DevOps engineer and I prefer concise answers" on Day 1
2. App is closed
3. User opens the app on Day 5
4. ChromaDB still has those facts on disk
5. When the user asks "What's my job?", the assistant searches ChromaDB, finds "User is a DevOps engineer", and answers correctly

This is what separates a toy demo from a real product. Every enterprise AI assistant stores context between sessions. Now you know how.

---

## Setup Instructions

### Step 1: Create and activate a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

The first run will automatically download the `all-MiniLM-L6-v2` embedding model (~80MB). This is a one-time download stored in your system's cache.

### Step 3: Set up your API key
```bash
cp .env.example .env
# Edit .env and replace sk-ant-your-key-here with your real key
```

### Step 4: Run the assistant
```bash
python personal_assistant.py
```

---

## How to Use the Assistant

```
============================================================
  PERSONAL ASSISTANT WITH PERSISTENT MEMORY
  Powered by Claude claude-opus-4-6 + ChromaDB
============================================================

  Hello! I'm your personal assistant.
  I'll remember important things you tell me, even after you close this app.

  Commands:
  'memories' — see all stored facts about you
  'clear'    — erase all memories
  'quit'     — exit the app
------------------------------------------------------------

  You: Hi! My name is Jordan and I'm a software engineer.
```

### Special Commands

| Command | What It Does |
|---------|-------------|
| `memories` | Shows all facts stored about you in ChromaDB |
| `clear` | Erases ALL memories (asks for confirmation) |
| `quit` or `exit` | Exits the application |

---

## The Memory Extraction Process

After each conversation turn, the app sends a separate request to Claude asking:

> "Extract important facts from this conversation that should be remembered for future reference."

Claude returns a JSON array like:
```json
["User's name is Jordan", "User is a software engineer", "User prefers dark mode"]
```

These facts are then stored in ChromaDB as separate documents. Each fact gets:
- A unique ID (UUID)
- A timestamp
- A type tag ("long_term_memory")

This extraction step costs one extra API call per turn but enables persistent knowledge.

---

## The Retrieval Process

Before Claude generates a response, the app:

1. Takes the user's current message as a search query
2. Converts it to a vector using the sentence-transformer model
3. Searches ChromaDB for the 5 most semantically similar memories
4. Injects those memories into Claude's system prompt

Example: User asks "What programming languages should I focus on?"

ChromaDB retrieves: "User is a software engineer", "User prefers Python"

Claude's system prompt now includes:
```
You have the following relevant memories:
- User is a software engineer
- User prefers Python
```

Claude uses this context to give a personalized answer.

---

## Understanding the Code Architecture

```
personal_assistant.py
│
├── get_chroma_client()          — Connect to ChromaDB on disk
├── get_or_create_collection()   — Get/create the memory collection
│
├── extract_memories()           — Ask Claude to extract facts from a turn
├── store_memories()             — Save extracted facts to ChromaDB
├── retrieve_relevant_memories() — Search ChromaDB for relevant facts
│
├── display_all_memories()       — Print all stored facts (for 'memories' command)
├── clear_all_memories()         — Erase all facts (for 'clear' command)
│
├── chat()                       — Main function: retrieve → respond → extract → store
│
└── main()                       — CLI loop: input → chat() → output
```

The `chat()` function is the heart of the application. Every user message flows through it:

```
User message
    ↓
[1] Retrieve relevant memories from ChromaDB
    ↓
[2] Build system prompt with memories injected
    ↓
[3] Call Claude with (system + short-term history + current message)
    ↓
[4] Update short-term memory (append to list, trim if > 10 messages)
    ↓
[5] Extract new memories from this exchange
    ↓
[6] Store new memories in ChromaDB
    ↓
Return Claude's reply
```

---

## Memory Persistence Demo

Here's exactly what happens across two sessions:

**Session 1:**
```
You: My name is Riley and I work at a startup called CloudBloom.
[Memory] Stored 2 new memories.

You: I'm building a CI/CD pipeline with GitHub Actions.
[Memory] Stored 2 new memories.

You: quit
Goodbye! Your memories are safely stored.
```

**Session 2 (new app run, days later):**
```
Welcome back! I remember 4 facts about you.
(Type 'memories' to see what I know)

You: memories
  [1] (2026-03-12) User's name is Riley
  [2] (2026-03-12) User works at a startup called CloudBloom
  [3] (2026-03-12) User is building a CI/CD pipeline
  [4] (2026-03-12) User is using GitHub Actions

You: Do you remember where I work?

  Assistant: Of course! You work at CloudBloom, a startup.
  Are you still working on that CI/CD pipeline with GitHub Actions?
```

The memories survived the app restart because ChromaDB stores them in the `./memory_db/` folder on disk.

---

## Where Is Data Stored?

After running the app, you'll see a new folder:
```
project7-personal-assistant/
├── memory_db/                ← ChromaDB creates this
│   ├── chroma.sqlite3        ← The database file
│   └── [uuid]/               ← Vector index files
├── personal_assistant.py
├── requirements.txt
└── .env
```

The `memory_db/` folder contains everything ChromaDB needs. You can:
- **Delete it** to erase all memories (same as the 'clear' command)
- **Copy it** to back up your memories
- **Move it** to a new machine and your memories go with you

---

## Common Issues

### "No module named 'chromadb'"
You forgot to install requirements or activate your virtual environment:
```bash
pip install -r requirements.txt
```

### Embedding model downloads on first run
The first time you run the app, it downloads `all-MiniLM-L6-v2` (~80MB). This takes 1-2 minutes with a good internet connection. Subsequent runs are instant.

### "ANTHROPIC_API_KEY not found"
Make sure you created `.env` (not `.env.example`) and put your real key in it.

### Memory extraction returns empty list
This is normal for small talk ("hi", "ok", "thanks"). The extraction prompt specifically asks for personal information, preferences, and tasks — not every message contains these.

---

## Real-World Applications

The pattern in this project is used in:

- **Enterprise chatbots** that remember employee preferences and past requests
- **Personal AI assistants** (think: a more capable Siri)
- **Customer support bots** that remember previous tickets and customer preferences
- **Developer tools** that learn your codebase and coding style
- **Education apps** that track what a student has learned and what they struggle with

Every one of these systems combines:
1. **Short-term context** (current conversation in the LLM's context window)
2. **Long-term retrieval** (relevant past knowledge fetched from a vector database)

You now know how to build both layers.

---

## What's Next

In Project 8, you'll take these concepts into a **FastAPI web server** — building a customer support bot with HTTP endpoints, session management, and the stateful conversation logic you learned here, but accessible over the internet.

In Project 9, you'll build a **knowledge base agent** that lets any company ingest their documents and query them with natural language — the foundation of enterprise AI search.
