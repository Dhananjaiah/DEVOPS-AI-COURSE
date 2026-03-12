# Project 9: Knowledge Base Agent

## What You Will Build

An AI agent that can answer questions about any set of documents. You feed it text files — HR policies, product manuals, FAQs, technical docs — and it can answer natural-language questions about them, citing the specific document it got each answer from.

This is the technology behind **enterprise AI search**: Confluence AI, SharePoint Copilot, Notion AI, Guru, and every other "ask a question about our docs" product.

---

## The Enterprise Knowledge Management Problem

Here's the situation at almost every company with more than 50 employees:

- Engineering has wiki pages in Confluence
- HR has policy documents in Google Drive
- Product has specs in Notion
- Customer support has runbooks in Zendesk
- Legal has contracts in SharePoint
- Sales has playbooks in Salesforce

**The problem:** Finding information is painful. An employee has a question — "What's our parental leave policy?" — and has to:
1. Remember which system the HR docs live in
2. Search for the right document
3. Read through a 40-page PDF to find the relevant section
4. Hope it's not outdated

Multiply this by every question every employee has every day. Companies estimate knowledge workers spend **20-30% of their time just searching for information**.

**The solution:** RAG (Retrieval-Augmented Generation). Store all documents in a vector database. When an employee asks a question, semantically search for relevant passages and send them to an LLM to generate a direct answer with citations.

That's exactly what this project builds.

---

## Why RAG Instead of Fine-Tuning?

When people first hear about "teaching AI about company documents," they often ask: "Why not just fine-tune Claude on our documents?"

Fine-tuning trains the model's weights to incorporate new knowledge. RAG retrieves relevant content at inference time. Here's why RAG wins for most enterprise use cases:

| Criterion | Fine-Tuning | RAG |
|-----------|------------|-----|
| **Cost** | Tens of thousands of dollars for large models | Minimal (just storage + embedding costs) |
| **Update frequency** | Re-train every time documents change | Add/update documents in seconds |
| **Explainability** | Black box — can't trace where answer came from | Cites specific source documents |
| **Hallucination risk** | Higher — model blends training with new knowledge | Lower — answer is grounded in retrieved text |
| **Document scope** | Fixed at training time | Any document added to the vector DB |
| **Setup complexity** | Weeks of ML engineering work | Hours of software engineering work |

The only case where fine-tuning clearly wins: **style and behavior** changes (making the model respond in a specific tone, follow specific formatting, etc.). For **knowledge**, RAG almost always wins.

---

## Chunking Strategy: Why and How

Documents can be thousands of pages long. We can't send an entire document to Claude in every query — context windows have limits, and even if they didn't, Claude would struggle to find the relevant needle in the haystack.

The solution: **chunking** — splitting documents into small, semantically coherent pieces before indexing.

### Why Chunk Size Matters

**Too small (50-100 characters):** Each chunk lacks enough context to be meaningful.
```
Chunk: "must receive manager approval before"
```
Approval for what? The context is lost.

**Too large (5000+ characters):** Each chunk is so long it introduces noise when retrieved.
If someone asks about vacation policy and you retrieve a 5000-character chunk about "Section 2: Benefits", only 1% of the content is relevant. Claude gets confused by the noise.

**Goldilocks zone (500-1000 characters):** Each chunk is one complete idea — a paragraph, a FAQ entry, a policy section.
```
Chunk: "2.4 Paid Time Off: Full-time employees receive 15 days of paid vacation per year,
increasing to 20 days after 3 years and 25 days after 7 years. TechCorp observes 11
federal holidays annually. Employees receive 7 sick days per year."
```
This chunk fully answers "how much vacation do employees get?"

This project uses **800 characters per chunk** with **100 characters of overlap**. This is a good default for business documents — adjust based on your specific content.

### Why Overlap Matters

Without overlap, a concept that spans a chunk boundary gets split:

```
Chunk 1: "...Employees are eligible for coverage beginning on the"
Chunk 2: "first day of the month following their hire date. Dental..."
```

If someone asks "when does health coverage start?", neither chunk contains the complete answer.

With 100-character overlap:
```
Chunk 1: "...Employees are eligible for coverage beginning on the first day of the month following"
Chunk 2: "following their hire date. Dental and vision coverage follows the same timeline..."
```

Both chunks now contain enough context to answer the question. The slight redundancy is worth the improved retrieval quality.

---

## Metadata in Vector Search

When you store a chunk in ChromaDB, you can attach **metadata** — arbitrary key-value pairs that describe the chunk:

```python
{
    "filename": "company_policy.txt",
    "chunk_index": 7,
    "total_chunks": 22,
    "timestamp": "2026-03-12T10:30:00"
}
```

Metadata enables powerful retrieval beyond raw semantic similarity:

### Filtering by Source
```python
# Find answers only in the HR policy document
collection.query(
    query_texts=["vacation days"],
    where={"filename": "company_policy.txt"}  # Filter!
)
```

### Filtering by Date
```python
# Only use documents ingested after a certain date
# (avoids returning outdated policy chunks)
collection.query(
    query_texts=["remote work policy"],
    where={"timestamp": {"$gte": "2026-01-01"}}  # Filter!
)
```

### Source Citation
Because we stored `filename` as metadata, we can tell users exactly where the answer came from:
```
"You receive 15 days of vacation per year (Source: company_policy.txt)"
```

This is critical for enterprise use — employees need to know if the answer came from the official HR policy or some old draft document.

---

## Source Citation: The Hallucination Defense

LLMs are prone to **hallucination** — generating confident-sounding statements that are simply wrong. This is particularly dangerous in enterprise settings where employees might make decisions based on AI answers.

Source citation is the primary defense against acting on hallucinated answers.

When Claude is forced to cite a source, several things happen:
1. The answer is grounded in retrieved text — it can't fabricate from whole cloth
2. The user can verify the answer by reading the cited document
3. If the cited document doesn't actually support the answer, the discrepancy is visible
4. Employees learn to check sources, not blindly trust AI

Our system prompt explicitly instructs Claude:
```
If the context contains the answer, use it and cite the source like: "(Source: filename.txt)"
If the context does NOT contain the answer, clearly say:
"I don't have information about that in the knowledge base"
```

This forces Claude to distinguish between:
- **Knowledge base answers** (grounded, trustworthy)
- **General knowledge answers** (Claude's training, potentially outdated or wrong)

In production, you might further constrain this: refuse to answer anything not in the knowledge base, redirecting users to ask a human instead.

---

## Idempotent Ingestion

The `ingest.py` script can be run multiple times without creating duplicate chunks. This is called **idempotency** — running an operation multiple times has the same effect as running it once.

How it works: We generate deterministic chunk IDs based on filename and chunk index:
```
policy.txt + chunk 0 → "policy_txt_chunk_0000"
policy.txt + chunk 1 → "policy_txt_chunk_0001"
```

Before adding a chunk, we check if that ID already exists in ChromaDB. If it does, we skip it.

**Why this matters in practice:**
- You can run `python ingest.py ./docs` after adding ONE new document and only the new document's chunks will be added
- Re-running after an interrupted ingestion won't create duplicates
- Scheduled runs (e.g., nightly cron jobs) can safely re-ingest the entire directory

To **update** an existing document, you'd need to first delete its old chunks (using the filename to filter) then re-ingest. This project doesn't implement updates, but the metadata structure makes it straightforward to add.

---

## Real-World Systems Using This Pattern

Every major "AI over documents" product uses the same fundamental pattern as this project:

**Confluence AI (Atlassian)**
- Ingests every Confluence page
- Answers questions about your wiki
- Cites the specific page and version

**Microsoft Copilot for SharePoint**
- Ingests SharePoint documents, Teams messages, emails
- Answers questions across your entire Microsoft 365 workspace
- Shows which documents were used to generate the answer

**Notion AI**
- Operates within a single Notion workspace
- Can summarize pages, answer questions about databases
- Grounded in the documents you've created

**Guru (enterprise knowledge base)**
- Purpose-built for customer support teams
- AI answers questions from support documentation
- Flags when answers might be outdated

**Amazon Kendra**
- Enterprise search service on AWS
- Ingests documents from S3, SharePoint, Salesforce, etc.
- Returns direct answers with source attribution

They're all doing what this project does: chunk → embed → store → retrieve → generate → cite. The enterprise versions have more sophisticated chunking, better metadata schemes, access control, and monitoring — but the core architecture is identical.

---

## Setup Instructions

### Step 1: Create virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

The first run downloads `all-MiniLM-L6-v2` (~80MB) for local embeddings.

### Step 3: Set up API key
```bash
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-your-real-key
```

### Step 4: Ingest documents
```bash
python ingest.py ./sample_docs
```

You'll see:
```
========================================================
  KNOWLEDGE BASE INGESTION TOOL
  Target directory: ./sample_docs
  Chunk size: 800 chars, Overlap: 100 chars
========================================================

Found 3 .txt file(s) in './sample_docs'

Connecting to ChromaDB...
Collection 'company_knowledge' ready.
Current chunk count: 0

Already ingested: 0 chunks (will skip these)

Ingesting file 1/3: company_policy.txt...
  Split into 8 chunks (800 chars each, 100 char overlap)
  Added: 8 new chunks, Skipped: 0 existing chunks

Ingesting file 2/3: faq.txt...
  Split into 7 chunks (800 chars each, 100 char overlap)
  Added: 7 new chunks, Skipped: 0 existing chunks

Ingesting file 3/3: product_manual.txt...
  Split into 9 chunks (800 chars each, 100 char overlap)
  Added: 9 new chunks, Skipped: 0 existing chunks

========================================================
INGESTION COMPLETE
========================================================
Files processed: 3
New chunks added: 24
Chunks skipped (already existed): 0
Total chunks in database: 24
Database location: /path/to/knowledge_db
```

### Step 5: Run the knowledge agent
```bash
python knowledge_agent.py
```

---

## Using the Knowledge Agent

```
Connecting to knowledge base...

========================================================
  KNOWLEDGE BASE AGENT
  Model: claude-opus-4-6
========================================================

  Knowledge base contains:
  - 24 chunks from 3 document(s)
  - company_policy.txt (8 chunks)
  - faq.txt (7 chunks)
  - product_manual.txt (9 chunks)

  Commands:
  'sources'  — list all documents in the knowledge base
  'quit'     — exit
----------------------------------------------------------

  Ask me anything about the documents in the knowledge base!

  You: How many vacation days do employees get?

  [Searching knowledge base...]

  Assistant: Full-time employees receive 15 days of paid vacation per year.
  This increases to 20 days after 3 years of service and 25 days after 7 years.
  TechCorp also observes 11 federal holidays annually and provides 7 sick days per year.
  (Source: company_policy.txt)
```

### Example Questions to Try

**HR Policy questions:**
- "What is the remote work policy?"
- "How does the 401k matching work?"
- "What are the progressive discipline steps?"
- "How much is the professional development budget?"

**Product manual questions:**
- "What ports does the TechCorp X1 have?"
- "What do I do if my X1 won't turn on?"
- "What are the technical specifications of the X1?"

**FAQ questions:**
- "What is TechCorp's refund policy?"
- "How do I reset my password?"
- "Is there a student discount?"
- "Can TechCorp Suite open Microsoft Word files?"

**Cross-document questions:**
- "What are all the ways I can contact TechCorp support?"
- "What products does TechCorp sell?"

**Testing the boundaries:**
- "What is the capital of France?" — should say it's not in the knowledge base
- "Who is the CEO of TechCorp?" — should say it's not in the knowledge base

---

## Understanding the Two-Script Architecture

This project is intentionally split into two scripts:

### ingest.py — Build the knowledge base
- Run once (or periodically to add new documents)
- No Claude API calls — just reads files and stores vectors
- Can process thousands of documents offline
- Idempotent — safe to re-run

### knowledge_agent.py — Query the knowledge base
- Run interactively to answer questions
- Reads from the pre-built ChromaDB database
- Uses Claude only for generating answers
- Fast because retrieval is pre-computed

**Why split them?**

In production, ingestion and querying are completely separate concerns:

- Ingestion runs on a schedule (e.g., every night to pick up new documents)
- Querying runs in real-time, responding to user requests
- They may run on different machines
- Ingestion can be slow (acceptable) — querying must be fast (required)

---

## The Semantic Search Advantage

To appreciate why vector search is so powerful, compare it to keyword search on the same question:

**Question:** "How many days off do employees get?"

**Keyword search** looks for documents containing "days off":
- Finds: nothing (the policy says "vacation days" not "days off")

**Vector search** finds documents with similar *meaning*:
- "15 days of paid vacation per year" — HIGH similarity (vacation = days off)
- "11 federal holidays annually" — MEDIUM similarity (holidays = days off)
- "7 sick days per year" — MEDIUM similarity (sick days = days off)

All three relevant passages are returned, even though none contain the exact phrase "days off."

This is what makes RAG systems genuinely useful for enterprise knowledge bases — employees don't need to know the exact terminology used in a document. They can ask in their own words.

---

## Adding Your Own Documents

To index your own documents:

1. Create a folder (e.g., `./my_docs/`)
2. Add `.txt` files to it
3. Run: `python ingest.py ./my_docs`
4. Start asking questions!

For documents in other formats (PDF, Word, HTML):
- PDFs: Use `pdfplumber` or `pypdf2` to extract text, save as .txt
- Word docs: Use `python-docx` to extract text, save as .txt
- HTML/web pages: Use `BeautifulSoup` to extract text, save as .txt

The ingestion pipeline only needs plain text — converting other formats is a preprocessing step.

---

## Troubleshooting

### "Collection 'company_knowledge' not found"
You haven't run `ingest.py` yet. Run:
```bash
python ingest.py ./sample_docs
```

### "No relevant documents found in the knowledge base"
The knowledge base is empty or the query is very unusual. Run `sources` to verify documents are loaded.

### Slow responses
The first query after starting is slow because the sentence-transformer model needs to be loaded into memory. Subsequent queries are much faster.

### Wrong answers
Check which chunks were retrieved — the issue may be in retrieval (relevant chunks not being found) or generation (Claude misinterpreting retrieved chunks). Increasing `TOP_K_CHUNKS` from 5 to 8-10 can improve recall.

---

## What's Next

You've now completed Phase 3! You've built:
- **Project 7**: Persistent memory with ChromaDB
- **Project 8**: Stateful API with FastAPI and session management
- **Project 9**: Enterprise knowledge base with RAG and source citation

Phase 4 introduces **multi-agent systems** — multiple AI agents working together, passing tasks between themselves, and operating as an autonomous team. This is where single AI assistants become AI organizations.
