# Project 3: Coaching Session Transcript
## "Ask My Doc" — RAG Document Q&A System

**Session Type:** Live tutoring session (follow-up to Projects 1 and 2)
**Student:** Alex (completed Projects 1 and 2, growing in confidence)
**Coach:** Jamie
**Duration:** ~65 minutes

---

**[Session begins. Alex has just opened the project3 folder in VS Code and looks curious.]**

---

**Jamie:** Welcome to Project 3! This one is going to blow your mind. How are you feeling after Project 2?

**Alex:** Really good! I actually used smart_notes.py on some real meeting notes from work. My manager asked me how I summarized them so fast and I said "I have a tool." Felt pretty good.

**Jamie:** [laughs] That's exactly the right use case. You're already applying this stuff at work. Today's project is bigger. Have you heard the term RAG?

**Alex:** I saw it in the folder name but I don't know what it means.

**Jamie:** RAG stands for Retrieval-Augmented Generation. Don't worry about the full name for now — let me give you an analogy first. Have you ever taken an open-book test at school?

**Alex:** Yeah, where you can bring your notes.

**Jamie:** Right. And with your notes, you're probably more accurate than if you were relying on memory alone. RAG is exactly that for AI. Instead of asking Claude to answer from memory — which can lead to making things up — we say: "Here's the relevant page from the book. Answer based on THIS." Claude becomes more accurate because we're giving it the specific source material.

**Alex:** Oh! So the AI doesn't have to guess?

**Jamie:** Exactly. And here's why this matters in companies. Every company has documents — HR policies, legal contracts, technical manuals, product specs. When a new employee joins, they have to read hundreds of pages. When a customer asks "what does our service agreement say about refunds?", someone has to look it up. RAG lets you build a system where you can just ASK a question and the AI finds the answer in the right document.

**Alex:** That's... actually really useful. Like I could load our company's entire policy handbook and ask it questions?

**Jamie:** That's exactly what you're going to build today. Let me ask you something first — why can't you just paste the entire 500-page handbook into Claude's message and say "answer from this"?

**Alex:** Hm... is it because of that max_tokens thing? Would it be too big?

**Jamie:** Partly. There IS a maximum amount of text Claude can process at once — called the context window. But even if it fit, it would be extremely expensive because you'd be sending thousands of tokens with every single question. If you have a 100,000-word handbook and someone asks "how many vacation days do I get?", you don't need to send all 100,000 words. You only need to send the 3-4 sentences that actually answer the question.

**Alex:** So RAG finds just the relevant parts?

**Jamie:** Exactly. RAG finds the relevant parts and only sends those. And to do that searching, we use something called a vector database. Have you heard of ChromaDB?

**Alex:** No. What is it?

**Jamie:** Okay, this requires explaining one more concept: vector embeddings. Bear with me, this is the core concept of modern AI search. Imagine every piece of text can be described as a location in a giant invisible space. Similar-meaning texts are located CLOSE to each other in that space. So "vacation days" and "annual leave" are close together, because they mean the same thing. But "vacation days" and "coffee machine" are far apart.

**Alex:** How does a computer know they're close?

**Jamie:** Great question. It runs the text through a mathematical model that converts it into a long list of numbers — like a set of coordinates in that invisible space. These coordinates are called a "vector" or "embedding." The model was trained on massive amounts of text to learn that "vacation" and "leave" appear in similar contexts, so they get similar coordinates.

**Alex:** So it's like... turning words into a GPS location?

**Jamie:** That's a really good analogy. Each piece of text gets GPS coordinates. When you search, you convert your question to GPS coordinates and find the text chunks that have the closest coordinates. ChromaDB is the map that stores all those coordinates and can find the nearest ones very quickly.

**Alex:** And ChromaDB does all the math automatically?

**Jamie:** Automatically! You just give it text, it figures out the coordinates, and when you search, it finds the closest matches. You don't need to understand the math to use it.

**Alex:** Okay... I think I get it. Let me set up the project. Same steps as before?

**Jamie:** Same steps. Go ahead.

**Alex:** [a few minutes pass] Okay, venv created, activated, now installing... oh, this is taking a lot longer than before.

**Jamie:** Yeah, ChromaDB pulls in some bigger dependencies. It's downloading some machine learning models. Normal — just wait it out.

**Alex:** Okay... it's done. And I made the `.env` file. Can I just run it?

**Jamie:** Run it with: `python ask_my_doc.py sample_company_policy.txt`

**Alex:** Running... "Loading document: sample_company_policy.txt"... "Document loaded: 5842 characters"... "Split document into 13 chunks"... "Storing chunks in ChromaDB, this may take a moment"... it's taking a few seconds... "Stored 13 chunks in ChromaDB. Ready to answer questions!"

**Jamie:** The pause while storing is ChromaDB converting all the chunks to vectors. On a large document this would take longer — that's why production systems pre-process documents and save the database to disk. For now, it rebuilds on every run.

**Alex:** Okay it's showing the question prompt. Can I ask something?

**Jamie:** Ask it anything from the policy document.

**Alex:** Asking: "How many vacation days do I get per year?"... wow it's showing me the source chunks it found! "Source 1: chunk_5"... "Source 2: chunk_6"... and then the answer! It says: "Full-time employees at Acme Technologies receive 20 paid vacation days per calendar year, increasing to 25 days after 5 years and 30 days after 10 years."

**Jamie:** And is that accurate from the document?

**Alex:** Let me check... yes! That's exactly what the policy says! It even mentions the tenure bonuses.

**Jamie:** Now try asking something that's NOT in the document. Ask it what the dress code policy is.

**Alex:** "What is the dress code policy?"... it says: "I don't have that information in the document. The provided context does not contain any information about a dress code policy."

**Jamie:** That's the most important thing that just happened. Say it back to me — why is that response good?

**Alex:** Because... it told me it didn't know instead of making something up?

**Jamie:** Exactly! Without RAG and without that system prompt, Claude might say "most professional offices have business casual dress codes" — which would be completely made up for this specific company. With RAG, it only answers from the document and admits when it can't find the answer. This is called "grounding" the AI. You're tethering it to real source material.

**Alex:** What was that "hallucination" word I've seen? Is this related?

**Jamie:** Yes! Hallucination is when an AI makes up information that sounds confident and plausible but is completely wrong. It's one of the biggest problems with AI in enterprise settings. Imagine using an AI to answer legal questions, and it makes up a law that doesn't exist. Or answers patient medical questions with fabricated drug interactions. Those are dangerous hallucinations.

**Alex:** That's terrifying.

**Jamie:** It really is. RAG dramatically reduces this for document-specific questions by giving the AI real source material to work from. It's not perfect — AI can still misread context — but it's far better than relying on training memory alone.

**Alex:** Okay, let me ask a trickier question. "Can I work from home every day?"

**Jamie:** Go for it.

**Alex:** It says: "No. According to the Remote Work Policy, the number of remote work days depends on your role. Engineering, design, and marketing employees may work remotely up to 4 days per week. Sales, operations, and customer success employees may work remotely up to 2 days per week. Additionally, all employees must be present in the office on Tuesdays as the company-wide collaboration day."

**Jamie:** Notice how it gave you a nuanced answer — different rules for different roles. That's because the relevant chunk contained that detail, and Claude included it. This is way better than a simple keyword search would give you.

**Alex:** Yeah, a keyword search for "work from home" wouldn't capture the nuance about the role differences.

**Jamie:** Exactly! That's the power of semantic search. Your question "can I work from home every day?" doesn't literally contain the words "engineering" or "design" or "role" — but the embedding model understood that the answer to your question involves role-based remote work policies, and retrieved that chunk.

**Alex:** Okay I want to look at the code. Can you walk me through the chunking function?

**Jamie:** Open it up. Tell me what you see in `split_into_chunks`.

**Alex:** It's a `def` — a function! We haven't really used functions before. It has `text`, `chunk_size=500`, `overlap=50` as inputs.

**Jamie:** The `=500` and `=50` after the parameters are "default values." If you call the function without specifying those, it uses 500 and 50. You can override them: `split_into_chunks(text, chunk_size=200)` would use chunks of 200 characters instead. Default values make functions flexible without requiring every caller to specify every setting.

**Alex:** And then it does a `while` loop... `start = 0` at the beginning, then `end = start + chunk_size`... and it slices `text[start:end]`... then moves `start` to `end - overlap`. Oh! That's how the overlap works — it goes BACK a bit before starting the next chunk.

**Jamie:** Perfect understanding. If chunk 1 ends at position 500, the next chunk starts at 500 minus 50 = position 450. So characters 450-500 appear in both chunk 1 and chunk 2. That overlap zone ensures that information near a chunk boundary doesn't get cut off.

**Alex:** And then `return chunks` gives back the list.

**Jamie:** Right. `return` sends the function's output back to the code that called it. When we write `chunks = split_into_chunks(full_text)`, Python runs the function, hits `return chunks`, and puts that list of chunks into our `chunks` variable.

**Alex:** Why do we use a function for this? Why not just put that code in the main script?

**Jamie:** Great question. You could, technically. But there are two reasons to use a function. First, readability — when you see `chunks = split_into_chunks(full_text, chunk_size=500, overlap=50)`, you immediately understand what it does from the name alone. If that code was inline, you'd have to read 10 lines to understand it. Second, reusability — if you later want to use the same chunking logic in a different project, you can just copy the function. It's packaged and portable.

**Alex:** Okay that makes sense. What about `enumerate` — I saw that in the loop where we add chunks to ChromaDB.

**Jamie:** `enumerate` is one of those Python tricks that makes life easier. Without it, if you wanted to loop through a list AND know the position of each item, you'd have to do this:

```python
i = 0
for chunk in chunks:
    print(i, chunk)
    i += 1
```

With `enumerate`, it's just:
```python
for i, chunk in enumerate(chunks):
    print(i, chunk)
```

Same result, cleaner code. `i` is the index (0, 1, 2...) and `chunk` is the value at that position.

**Alex:** Nice. And we need `i` to create unique IDs — `chunk_0`, `chunk_1`, etc.

**Jamie:** Exactly. ChromaDB requires every stored item to have a unique ID. We construct them using `f"chunk_{i}"` — an f-string that puts the number into the string.

**Alex:** Okay, let me ask about the search part. `collection.query()` — what does that return?

**Jamie:** It returns a dictionary. And the structure is a bit nested. Here's what it looks like:

```python
{
  "documents": [["chunk text 1", "chunk text 2", "chunk text 3"]],
  "ids": [["chunk_5", "chunk_12", "chunk_3"]],
  "distances": [[0.23, 0.45, 0.67]]
}
```

The outer list exists because ChromaDB can handle batch queries. We only asked one question, so there's only one result set — hence the `[0]` to get the first (and only) result.

**Alex:** So `search_results["documents"][0]` gives us a list of 3 chunk text strings?

**Jamie:** Exactly. And `search_results["ids"][0]` gives us the IDs of those chunks. We use the IDs to show the user which chunk was retrieved: "Source 1: chunk_5".

**Alex:** The distances — I saw those in the code comments but they're not shown to the user right now?

**Jamie:** Right, we retrieve them but we display them for you in the README as an exercise. Distances are a relevance score — lower distance = more similar to your question. If you wanted to show confidence scores, you could convert them: `confidence = 1 - distance` (on a 0-1 scale). It's one of the extension ideas in the README.

**Alex:** Cool. Can I ask a meta-question? How do companies use this in real life? Like what does a production version of this look like?

**Jamie:** Great question. A production RAG system has a few extra pieces:

1. **Document loading pipeline** — instead of manually loading one file, there's a process that automatically indexes new documents when they're uploaded to a file system or SharePoint
2. **Persistent vector database** — ChromaDB saves to disk so you don't rebuild on every run. Some companies use enterprise vector databases like Pinecone or Weaviate
3. **An API layer** — instead of a terminal program, there's a REST API endpoint that receives questions and returns answers
4. **A frontend** — a nice web chat interface where employees type questions naturally
5. **Source citations** — the answer always includes a link to the original document section

The core logic — chunk, embed, retrieve, generate — is exactly what you built today. The rest is infrastructure wrapping.

**Alex:** So I just built the core of something that's worth millions to companies?

**Jamie:** The core logic, yes. The engineering work to make it production-scale, reliable, and maintainable is significant. But the conceptual foundation? You have it. That's what companies pay engineers for — understanding which pieces to use and how to connect them.

**Alex:** This is making me feel like I could actually get a job in this field.

**Jamie:** You could. And you will. Let me quiz you before we wrap up.

**Alex:** Ready.

**Jamie:** Question 1: What is hallucination in the context of AI, and how does RAG address it?

**Alex:** Hallucination is when the AI makes up information — gives a confident-sounding answer that's actually wrong or made up. RAG addresses it by giving the AI specific source material to work from and using a system prompt that says "only answer from the provided context." If the answer isn't there, the AI says so instead of inventing one.

**Jamie:** Perfect. Question 2: Why do we use chunks instead of the full document?

**Alex:** Cost and context window size. Sending the whole document every time would use thousands of tokens and cost a lot of money. Chunks let us send only the relevant 3 pieces. Also, some documents are too big for the context window.

**Jamie:** Excellent. And the third question is the conceptual one: In your own words, what is a vector embedding and why does it make search better than keyword matching?

**Alex:** Um... a vector embedding is when you convert text to a list of numbers that represent its meaning — like GPS coordinates for meaning. Similar meanings get similar coordinates. Vector search finds coordinates that are close together, so you can search by meaning rather than exact words. Keyword search would miss "annual leave" when you search for "vacation days," but vector search would find it because they have similar meaning-coordinates.

**Jamie:** That was an excellent explanation. Better than some engineers who've been in the field for years. You've got the concepts down.

**Alex:** I'm really starting to understand this stuff. What's in Phase 2?

**Jamie:** Phase 2 is where you build multi-step agents. Instead of asking one question and getting one answer, you'll build AI systems that can do sequences of tasks — like an agent that can search the web, write code, run the code, and report results. You'll also learn about tool use, where Claude can call external functions.

**Alex:** Agents that can run code? That sounds wild.

**Jamie:** It's the bleeding edge of what engineers are building right now. Companies are using agents to automate full workflows — things that would have required 5 people doing steps manually. You're going to build that.

**Alex:** I'm in. This has been an incredible session. I came in thinking RAG was some mysterious thing and now I feel like I actually understand it.

**Jamie:** You understand it because you built it. That's the difference between watching someone else swim and jumping in the pool yourself. Great work today, Alex. Phase 1 complete.

**Alex:** Thanks Jamie! See you in Phase 2.

---

**[End of Session]**

**Session Summary:**
- Covered: RAG concept (open-book analogy), hallucination and why it's dangerous, vector embeddings (GPS analogy), ChromaDB, semantic search vs. keyword search, chunking with overlap, Python functions and `def`, default parameter values, `enumerate()`, nested dictionary access with `[0]`, production RAG architecture overview
- Key student insight: "I just built the core of something that's worth millions to companies"
- Moment of realization: When the AI correctly said "I don't have that information" for the dress code question — student understood why grounding matters
- All three quiz questions answered correctly and articulately
- Student confidence level: 9/10 — ready for Phase 2
- Next session: Phase 2 — Multi-step AI agents, tool use, web search agents
