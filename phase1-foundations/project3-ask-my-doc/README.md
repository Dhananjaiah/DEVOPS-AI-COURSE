# Project 3: Ask My Doc — Build a RAG Document Q&A System

**Difficulty:** Intermediate Beginner (builds on Projects 1 and 2)
**Time to Complete:** 60–90 minutes
**Prerequisite:** Completed Project 1 (Hello AI) and Project 2 (Smart Notes)

---

## 1. Project Overview

This is the most powerful project in Phase 1, and it introduces a concept that is reshaping how companies use AI: **RAG — Retrieval-Augmented Generation**.

In Projects 1 and 2, you asked Claude general questions and Claude answered from its own training knowledge. That works great for general topics. But what if you want Claude to answer questions about *your specific documents* — like your company's HR policy, a 200-page product manual, or a legal contract?

You can't just paste a 10,000-word document into every message — it would cost a fortune in tokens and Claude has a limit on how much text it can process at once. More importantly, Claude might mix up its general knowledge with what's in your document. That's called **hallucination** — and it's a big problem for enterprise use.

RAG solves all of this. Here's what `ask_my_doc.py` does:

1. Loads your document
2. Splits it into small chunks
3. Stores those chunks in ChromaDB (a special searchable database)
4. When you ask a question, finds only the relevant chunks
5. Sends ONLY those chunks + your question to Claude
6. Claude answers ONLY from the provided chunks

The result: a Q&A system that is accurate, cheap, and won't make things up.

**Why does this matter for real jobs?**

Every company has documents: policy manuals, technical specs, legal agreements, product documentation, knowledge bases. RAG is the technology that turns those documents into queryable AI assistants. This is a skill that companies are paying premium salaries for right now. Startups have been valued at hundreds of millions of dollars for building products that are fundamentally just well-engineered RAG systems.

---

## 2. What You Are Building

`ask_my_doc.py` takes a text file and creates an interactive Q&A session:

```bash
python ask_my_doc.py sample_company_policy.txt
```

Then you can ask questions like:

```
Your question: How many vacation days do I get?
Your question: Can I work from home every day?
Your question: What happens if I submit an expense after 60 days?
Your question: quit
```

And Claude will answer accurately, citing the relevant part of the document, without making anything up.

---

## 3. Understanding the Key Concepts (Read This First!)

Before you set up the project, let's make sure you understand what's actually happening. These three concepts are foundational.

### What is RAG? (Retrieval-Augmented Generation)

Let's use an analogy. Imagine you are taking an exam, and it's an "open book" test. You're allowed to bring a textbook.

- **Without RAG:** The AI is like a student who memorized everything — but sometimes remembers things wrong (hallucination), and can only answer about topics in its training data.
- **With RAG:** The AI is like a student with an open book. Instead of relying on memory, it can look up the right answer in the actual document. It's more accurate and stays within the information it's given.

RAG = Open Book Test for AI.

The three parts of the name explain what it does:
- **Retrieval** — find the relevant parts of the document
- **Augmented** — enrich the AI's context with that information
- **Generation** — the AI generates an answer based on that context

### What Are Vector Embeddings? (The Magic Behind the Search)

This is the trickiest concept, but it's fundamental to RAG. Let's break it down.

A normal database search works like this: if you type "vacation days," it looks for those exact words. But what if the document says "annual leave entitlement" instead? A keyword search would miss it.

**Vector embeddings solve this problem by converting text to numbers.**

An "embedding" is when you take a piece of text and run it through a mathematical model that converts it into a long list of numbers — called a vector. For example:

```
"vacation days"  → [0.23, -0.87, 0.44, 0.12, ..., 0.91]   (768 numbers)
"annual leave"   → [0.21, -0.89, 0.46, 0.11, ..., 0.89]   (768 numbers)
"coffee machine" → [-0.55, 0.32, -0.11, 0.78, ..., -0.43]  (768 numbers)
```

Notice that "vacation days" and "annual leave" produce very similar numbers (they're conceptually close), while "coffee machine" produces very different numbers (it means something completely different).

When you ask a question, your question is ALSO converted to a vector. Then we find the document chunks whose vectors are most similar to your question's vector. That's semantic search — searching by meaning, not just words.

**The analogy:** Imagine every concept lives in a huge 3D space. Similar concepts are close together. "Dog" and "puppy" are very close. "Dog" and "aircraft" are very far apart. Vector search finds what's nearby.

ChromaDB does all of this automatically — you just give it text and it handles the math.

### What is ChromaDB?

ChromaDB is a vector database. A database is just a place to store and search data. ChromaDB specifically is designed for storing and searching text using the vector embedding technique described above.

Regular database (SQL): "Find all rows where name = 'vacation'"
ChromaDB: "Find all chunks that are conceptually similar to 'how much time off do I get?'"

ChromaDB is:
- Free and open source
- Easy to run locally (no server needed for simple use)
- Has a simple Python API
- Automatically generates embeddings using a built-in model

For this project, we use ChromaDB as an in-memory database — it only exists while the program runs. When you restart the program, it reloads the document and rebuilds the database. In a real production system, you would use persistent storage so you only have to load the document once.

### What is Hallucination and Why Does RAG Fix It?

AI hallucination is when an AI confidently states something that is false. This happens because AI models are trained to produce plausible-sounding text — but "plausible" is not the same as "accurate."

For example, if you ask Claude "What is Acme Technologies' vacation policy?" without giving it the actual policy document, Claude might say something like "Most companies offer 15 days of vacation..." — which is a reasonable guess, but completely wrong for your specific company.

RAG fixes this by:
1. **Grounding the AI** — giving it the actual source text to work from
2. **Constraining the AI** — using the system prompt to say "Only answer from the provided context"
3. **Making errors detectable** — if the answer isn't in the context, the AI says "I don't have that information" instead of guessing

RAG doesn't completely eliminate hallucination, but it dramatically reduces it for document-specific questions.

---

## 4. Setup Instructions

### Step 1: Navigate to the project folder

```bash
cd C:\Users\techi\Downloads\2026\DEVOPS-AI-COURSE\phase1-foundations\project3-ask-my-doc
```

### Step 2: Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

**Note:** This project installs `chromadb==0.5.0` which is larger than the previous projects. The installation may take 2–5 minutes. You'll see it downloading several packages. This is normal.

**Possible issue on Windows:** ChromaDB requires Microsoft C++ build tools. If you see an error about `chroma-hnswlib`, you may need to install the Visual C++ Redistributable from:
[https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Step 4: Create your `.env` file

```bash
copy .env.example .env
```

Add your Anthropic API key to `.env`. (Same key as Projects 1 and 2.)

### Step 5: Run the program

```bash
python ask_my_doc.py sample_company_policy.txt
```

### Step 6: Ask questions

The program will load the document and set up the ChromaDB database. Then you can ask questions:

```
Your question: How many vacation days do new employees get?
Your question: Can I use public Wi-Fi for work?
Your question: What is the meal allowance for dinner?
Your question: What happens if I break the code of conduct?
Your question: quit
```

---

## 5. Complete Code Walkthrough

### Part 1: Reading the Document from sys.argv

```python
if len(sys.argv) < 2:
    print("Usage: python ask_my_doc.py <path_to_text_file>")
    sys.exit(1)

doc_path = sys.argv[1]
```

`sys.argv` is a Python list of everything the user typed when running the script. When you type `python ask_my_doc.py sample_company_policy.txt`:

```
sys.argv[0] = "ask_my_doc.py"
sys.argv[1] = "sample_company_policy.txt"
```

`len(sys.argv) < 2` checks if there are fewer than 2 items. If the user just types `python ask_my_doc.py` with no filename, `sys.argv` has only one item, so `len` is 1, which is less than 2 — and we print a usage message and exit.

This is a simpler alternative to argparse — good for scripts that only need one argument.

### Part 2: The Chunking Function

```python
def split_into_chunks(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks
```

**What is a function?**

A function is a named, reusable block of code. You "define" it once with `def`, then you can "call" it (run it) as many times as you want. Functions are one of the most fundamental building blocks of programming.

The `def` keyword says "I'm defining a function." The function name (`split_into_chunks`) is how you call it later. The values in parentheses (`text`, `chunk_size=500`, `overlap=50`) are the inputs (called "parameters"). `chunk_size=500` means the default value is 500 — if you call `split_into_chunks(my_text)` without specifying `chunk_size`, it will automatically use 500.

`return chunks` is how the function gives its result back to whoever called it. When you write `chunks = split_into_chunks(full_text)`, Python runs the function, reaches `return`, and puts the return value into your `chunks` variable.

**Why 500-character chunks?**

It's a balance. Too small and you lose context (important information might be split across chunks). Too big and each search returns massive amounts of text, wasting tokens. 500 characters is roughly 2-4 sentences — enough to contain an idea, small enough to be targeted.

**Why overlap?**

Imagine a sentence is split exactly at a chunk boundary: "Employees receive 20 vac" / "ation days per year." Neither chunk alone makes sense. Overlap ensures the important idea (vacation days) appears in at least one complete chunk.

### Part 3: Setting Up ChromaDB

```python
client_chroma = chromadb.Client()
collection = client_chroma.create_collection(name="document_chunks")
```

`chromadb.Client()` creates an in-memory database. Think of this like creating a fresh, empty spreadsheet in RAM.

`create_collection()` creates a "table" inside that database to store our chunks. We name it `"document_chunks"`.

```python
for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk],
        ids=[f"chunk_{i}"]
    )
```

The `for i, chunk in enumerate(chunks):` loop goes through every chunk. `enumerate()` gives us both the INDEX number (`i`) and the VALUE (`chunk`) at each step. Without `enumerate`, we'd only get the values and would have to track the counter manually.

`collection.add()` stores one chunk. The `ids` parameter needs a unique string ID for each item. We use `f"chunk_{i}"` to create IDs like `chunk_0`, `chunk_1`, `chunk_2`, etc.

Behind the scenes, ChromaDB is converting each chunk to a vector and storing it. This is why it might take a moment.

### Part 4: Searching ChromaDB

```python
search_results = collection.query(
    query_texts=[question],
    n_results=3
)
retrieved_chunks = search_results["documents"][0]
```

`collection.query()` takes your question, converts it to a vector, and finds the 3 (`n_results=3`) chunks whose vectors are most similar.

`search_results["documents"][0]` extracts the text chunks from the result. The result is nested in lists because ChromaDB supports batch queries (asking multiple questions at once). Since we only asked one question, we use `[0]` to get the results for that single question.

### Part 5: Building the Prompt with Retrieved Context

```python
context = "\n\n---\n\n".join(retrieved_chunks)

user_message = f"""Here is the relevant context from the document:

CONTEXT:
{context}

QUESTION:
{question}

Please answer the question based only on the context provided above."""
```

We join the 3 retrieved chunks into one block of text with `---` separators between them. Then we build a clear user message that explicitly labels what is CONTEXT and what is the QUESTION.

This clear structure helps Claude understand the format: "Here is the evidence. Here is the question. Answer using only the evidence."

### Part 6: The System Prompt for RAG

```python
system_prompt = """You are a document assistant. Answer questions ONLY based on the provided context.
If the answer is not in the provided context, say 'I don't have that information in the document.'"""
```

This is the most important line for preventing hallucination. The phrase "ONLY based on the provided context" is the instruction that tells Claude to stay within bounds. The fallback phrase ("I don't have that information") gives Claude a graceful way to admit when the answer isn't in the document — instead of guessing.

---

## 6. Sample Session

```
$ python ask_my_doc.py sample_company_policy.txt

Loading document: sample_company_policy.txt
Document loaded: 5842 characters
Split document into 13 chunks
Storing chunks in ChromaDB... (this may take a moment)
Stored 13 chunks in ChromaDB. Ready to answer questions!

============================================================
  Ask My Doc — Document Question Answering System
============================================================
Document loaded: sample_company_policy.txt
Type your question and press Enter. Type 'quit' to exit.
============================================================

Your question: How many vacation days do I get per year?

Searching document for relevant sections...

--- Relevant sections found in document ---

[Source 1: chunk_5]
Annual Vacation Days: Full-time employees receive 20 paid vacation days per calendar year. Employees with more than 5 years of service receive 25 days...

[Source 2: chunk_6]
Vacation Carryover: Employees may carry over a maximum of 10 unused vacation days from one calendar year to the next...

[Source 3: chunk_4]
Acme Technologies believes that time away from work is essential for employee wellbeing, creativity, and long-term performance...
--- End of retrieved sections ---

Asking Claude...

============================================================
ANSWER:
------------------------------------------------------------
Based on the document, full-time employees at Acme Technologies receive 20 paid vacation days per calendar year. The number increases with tenure: employees with more than 5 years of service receive 25 days, and those with more than 10 years receive 30 days. Vacation days are front-loaded at the start of each calendar year.

The relevant section is: "Annual Vacation Days: Full-time employees receive 20 paid vacation days per calendar year..."
============================================================
(Tokens used: 512 input, 89 output)

Your question: Can I use public WiFi at a coffee shop for work?

Searching document for relevant sections...
...

ANSWER:
------------------------------------------------------------
No, you cannot use public Wi-Fi for work. The document states in the Remote Work Policy section: "The use of public Wi-Fi in coffee shops, airports, or other public spaces is prohibited when accessing company systems." You are required to use a secure, password-protected internet connection and connect through the company VPN when accessing internal tools or customer data.
============================================================

Your question: What is the budget for buying a new laptop?

Searching document for relevant sections...
...

ANSWER:
------------------------------------------------------------
I don't have that information in the document. The document mentions that equipment purchases over $100 require pre-approval from your manager, but it does not specify a budget amount for laptops or other specific devices.
============================================================

Your question: quit
Goodbye! Thanks for using Ask My Doc.
```

Notice the last answer: the document doesn't say the laptop budget, so Claude correctly says "I don't have that information" instead of making something up.

---

## 7. Real World Use Cases

### Example 1: Enterprise HR Chatbot
A company with 3,000 employees gets 200+ HR questions every month: "How many sick days do I get?", "What's the expense limit for hotels?", "Can I work from home on Mondays?" An HR team member can now build an internal chatbot by loading the HR policy PDF into a RAG system. Employees ask questions and get accurate, instant answers 24/7. The HR team can focus on complex cases. This is one of the most common enterprise AI deployments today.

### Example 2: Legal Contract Review
A law firm or procurement team needs to review hundreds of vendor contracts. Instead of reading every contract line by line to find the termination clause or liability cap, a lawyer uploads the contract to a RAG system and asks: "What is the termination notice period?", "Is there an auto-renewal clause?", "What are the data processing obligations?" The AI finds the relevant sections and summarizes them. A contract review that would take 2 hours now takes 15 minutes.

### Example 3: Technical Documentation Q&A for Engineers
A software product has 500 pages of technical documentation. New engineers joining the team spend weeks learning how the system works. A senior engineer builds a RAG tool that indexes all the documentation. New engineers can ask: "How does the authentication service work?", "What's the retry logic for the payment queue?", "Where are environment variables documented?" They find answers in seconds instead of hours. Senior engineers spend less time answering the same questions repeatedly.

---

## 8. Extend This Project

### Idea 1: Load Multiple Documents
Instead of loading one file, accept a folder and load all `.txt` files:

```python
import glob
doc_files = glob.glob("documents/*.txt")
for doc_file in doc_files:
    with open(doc_file, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = split_into_chunks(text)
    for i, chunk in enumerate(chunks):
        # Use the filename + index as the ID to keep them unique
        collection.add(documents=[chunk], ids=[f"{doc_file}_chunk_{i}"])
```

Now you can ask questions across an entire library of documents.

### Idea 2: Show Confidence Scores
ChromaDB returns "distances" — how similar each result is to your question. Lower distance = more similar. Display this to the user:

```python
distances = search_results["distances"][0]
for chunk_id, chunk_text, distance in zip(retrieved_ids, retrieved_chunks, distances):
    confidence = round((1 - distance) * 100, 1)  # Convert distance to a percentage
    print(f"[Relevance: {confidence}%] {chunk_text[:100]}...")
```

This teaches you about semantic similarity scoring — useful for filtering out low-quality matches.

### Idea 3: Persistent Storage
Right now, the database is rebuilt every time you run the program. For a large document, this is slow. Use ChromaDB's persistent client to save it to disk:

```python
# Replace chromadb.Client() with:
client_chroma = chromadb.PersistentClient(path="./chroma_db")

# Then only add documents if the collection doesn't exist yet:
try:
    collection = client_chroma.get_collection("document_chunks")
    print("Loaded existing database.")
except:
    collection = client_chroma.create_collection("document_chunks")
    # ... add chunks here
```

Now the database is saved to a folder called `chroma_db` and only needs to be built once.

---

## 9. What You Learned

| Concept | What It Means |
|---------|--------------|
| RAG | Retrieval-Augmented Generation — finding relevant document pieces and using them as AI context |
| Hallucination | When an AI confidently states something false because it's generating "plausible" text rather than recalling facts |
| Vector embedding | Converting text to a list of numbers that represents its meaning — similar meanings produce similar numbers |
| Semantic search | Searching by meaning rather than exact keyword matching |
| ChromaDB | An open-source vector database that stores text chunks as embeddings and supports similarity search |
| In-memory database | A database that only exists while the program runs; not saved to disk |
| Chunking | Splitting a large document into smaller pieces so relevant parts can be retrieved individually |
| Overlap | Sharing characters between adjacent chunks to prevent information loss at boundaries |
| `def` function | A named, reusable block of code defined with `def` and called by its name |
| Function parameters | Input values a function receives, defined in the parentheses of `def` |
| `return` statement | Sends the function's output back to the caller |
| `enumerate()` | A Python built-in that gives both the index and value when looping over a list |
| `sys.argv` | A list of command-line arguments — what the user typed to run the script |
| Grounding | Connecting an AI to specific source material to reduce hallucination |
| Context window | The maximum amount of text an AI can process in one request |

---

## 10. Quiz Questions

**Question 1:** In plain English, explain what happens between when a user types a question and when they see an answer. Walk through every step.

<details>
<summary>Click to reveal the answer</summary>

**Answer:** Here is the complete flow:

1. The user types a question and presses Enter.
2. Python stores their input in the `question` variable.
3. The program calls `collection.query()` on ChromaDB, passing the question.
4. ChromaDB converts the question into a vector (list of numbers representing its meaning) using a built-in embedding model.
5. ChromaDB compares that vector to all the stored chunk vectors and finds the 3 most similar ones.
6. The program receives those 3 chunk texts from ChromaDB.
7. The program builds a user message that combines the 3 chunks (as "CONTEXT") with the original question.
8. The program calls `anthropic_client.messages.create()`, sending the system prompt + user message to Claude.
9. Claude reads the system prompt ("only answer from the context"), reads the 3 retrieved chunks, reads the question, and generates an answer.
10. The program receives Claude's response, extracts the text, and prints it.

The whole process from question to answer typically takes 2–5 seconds.

</details>

---

**Question 2:** Why would a company use RAG instead of just sending the whole document to Claude every time?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** There are three main reasons:

**Cost:** Claude (and all AI models) charge per token — every word in your input costs money. Sending a 500-page document with every question would cost hundreds of times more than sending just 3 relevant chunks. For a system processing hundreds of questions per day, this difference is enormous.

**Context window limits:** AI models have a maximum amount of text they can process at once (called the "context window"). Claude's context window is large but not unlimited. A truly long document (100,000+ words) might not fit at all. RAG works around this by only ever sending a small relevant slice.

**Accuracy:** Paradoxically, sending less but more targeted information often produces better answers. When you send an entire document, the AI has to search through all of it to find the relevant part — and sometimes gets confused by irrelevant sections. Sending pre-retrieved relevant chunks gives the AI a cleaner, focused context, which leads to more accurate answers.

</details>

---

**Question 3:** What does the system prompt `"Answer ONLY based on the provided context. If the answer is not in the context, say 'I don't have that information in the document.'"` actually accomplish? What would happen if you removed it?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** This system prompt accomplishes two things:

**Prevents hallucination on document-specific questions:** Without it, if a user asks "What is the overtime pay policy?" and that topic isn't in the document, Claude might answer from general knowledge — "Most companies pay 1.5x for overtime" — which would be wrong for this specific company. With the system prompt, Claude is constrained to only use the retrieved chunks. If the chunks don't contain overtime policy information, Claude says "I don't have that information."

**Creates a reliable fallback:** The phrase "If the answer is not in the context, say 'I don't have that information in the document'" is critical. Without a specific fallback instruction, Claude might still try to be "helpful" and answer from general knowledge, which defeats the purpose of RAG. By giving it an explicit, graceful fallback phrase, we ensure users know the difference between "Claude answered from the document" and "Claude couldn't find it."

If you removed the system prompt entirely, Claude would still try to answer questions — but it would freely mix document information with general knowledge, making it impossible for users to know which parts of an answer came from the actual document vs. Claude's training data.

</details>
