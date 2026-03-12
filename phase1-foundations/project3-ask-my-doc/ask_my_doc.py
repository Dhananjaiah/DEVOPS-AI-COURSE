# ask_my_doc.py
# A basic RAG (Retrieval-Augmented Generation) system.
# RAG means: instead of asking the AI to answer from memory,
# we give it specific chunks from a document and say "answer ONLY from this."
#
# How it works in simple terms:
#   1. Load a text file
#   2. Split it into small chunks (pieces)
#   3. Store those chunks in ChromaDB (a special searchable database)
#   4. When the user asks a question, find the most relevant chunks
#   5. Send those chunks + the question to Claude
#   6. Claude answers based ONLY on those chunks
#
# Run it like this:
#   python ask_my_doc.py sample_company_policy.txt

# ── Import Section ──────────────────────────────────────────────────────────

import os           # Lets Python talk to the operating system — we use it to read the API key.
import sys          # Lets us exit the program cleanly if something goes wrong.

from dotenv import load_dotenv  # Reads the .env file and loads secret values like API keys.
import anthropic                # The official library for talking to Claude AI.
import chromadb                 # ChromaDB: a vector database that can search by meaning, not just keywords.


# ── Step 1: Load API key ─────────────────────────────────────────────────────

load_dotenv()  # Read the .env file and load values into Python's memory.

api_key = os.getenv("ANTHROPIC_API_KEY")  # Get the API key from environment variables.

if not api_key:  # If no API key found, stop and tell the user.
    print("ERROR: ANTHROPIC_API_KEY not found in .env file.")
    print("Please create a .env file with your key. Copy from .env.example.")
    sys.exit(1)  # Exit the program with an error code.


# ── Step 2: Read the document file from command-line argument ────────────────
# We expect the user to pass a filename when running the program:
#   python ask_my_doc.py sample_company_policy.txt
# sys.argv is a list of everything the user typed. sys.argv[0] is the script name.
# sys.argv[1] would be the first argument they typed after the script name.

if len(sys.argv) < 2:
    # len() counts items in a list. If there's only 1 item (the script name itself),
    # the user forgot to provide the filename argument.
    print("Usage: python ask_my_doc.py <path_to_text_file>")
    print("Example: python ask_my_doc.py sample_company_policy.txt")
    sys.exit(1)  # Exit because we can't continue without a file.

doc_path = sys.argv[1]  # sys.argv[1] is the second item — the filename the user typed.
                         # Example: if user typed "python ask_my_doc.py policy.txt"
                         # then sys.argv = ["ask_my_doc.py", "policy.txt"]
                         # and sys.argv[1] = "policy.txt"

if not os.path.exists(doc_path):  # Check if the file actually exists on disk.
    print(f"ERROR: File not found: {doc_path}")
    print("Please check the file path and try again.")
    sys.exit(1)  # Exit if the file doesn't exist.

print(f"Loading document: {doc_path}")

with open(doc_path, "r", encoding="utf-8") as f:
    # "r" = read mode. encoding="utf-8" handles all characters including special ones.
    # "with" automatically closes the file when we're done — even if an error occurs.
    full_text = f.read()  # Read the entire file into one big string called full_text.

print(f"Document loaded: {len(full_text)} characters")  # Tell the user how big the document is.
# len(full_text) counts the number of characters in the string.


# ── Step 3: Split the document into chunks ───────────────────────────────────
# Why do we need chunks? Claude can only read so much text at once (its "context window").
# Also, if we send the whole document every time, we'd use thousands of tokens per question.
# Instead, we find only the RELEVANT parts of the document and send those.
#
# We split the document into overlapping chunks of about 500 characters.
# "Overlapping" means each chunk shares 50 characters with the next chunk.
# This prevents information from being "lost" at the boundary between chunks.
#
# Example: If the document is "ABCDEFGHIJ" and chunk size is 4 with overlap 2:
# Chunk 1: "ABCD"
# Chunk 2: "CDEF"  (starts 2 before the end of chunk 1)
# Chunk 3: "EFGH"
# Chunk 4: "GHIJ"

def split_into_chunks(text, chunk_size=500, overlap=50):
    # This is a FUNCTION. A function is a reusable block of code.
    # "def" means "define a function". "split_into_chunks" is the name.
    # The parentheses hold the inputs (called "parameters"):
    #   text: the full document text string
    #   chunk_size: how many characters each chunk should be (default 500)
    #   overlap: how many characters to share between adjacent chunks (default 50)
    # The function will RETURN a list of chunk strings.

    chunks = []      # Start with an empty list to hold our chunks.
    start = 0        # "start" is the position in the text where the current chunk begins.
                     # We start at position 0 (the very beginning of the text).

    while start < len(text):
        # Keep going as long as "start" hasn't passed the end of the text.
        # len(text) gives the total number of characters.

        end = start + chunk_size  # "end" is where this chunk stops.
                                   # Example: if start=0 and chunk_size=500, end=500.

        chunk = text[start:end]   # text[start:end] is "slicing" — it extracts the substring
                                   # from position start up to (but not including) position end.
                                   # Example: "Hello World"[0:5] = "Hello"

        chunk = chunk.strip()     # .strip() removes extra spaces and newlines from the beginning
                                   # and end of the chunk. This cleans up any leftover whitespace.

        if chunk:                 # "if chunk:" means "if chunk is not empty"
            chunks.append(chunk)  # Add this non-empty chunk to our list.

        start = end - overlap     # Move the start position BACK by "overlap" characters.
                                   # This creates the overlap between chunks.
                                   # Example: if end=500 and overlap=50, next start=450.
                                   # So the next chunk starts at 450, overlapping with this one.

    return chunks  # Return the complete list of chunks back to the caller.
                   # When you call split_into_chunks(text), you get this list.


chunks = split_into_chunks(full_text, chunk_size=500, overlap=50)
# Call our function with the full document text.
# The result (a list of chunk strings) is stored in the variable "chunks".

print(f"Split document into {len(chunks)} chunks")  # Tell the user how many chunks were made.


# ── Step 4: Set up ChromaDB and store the chunks ─────────────────────────────
# ChromaDB is a "vector database". A regular database stores data and lets you search by exact keywords.
# A vector database converts text into "vectors" (lists of numbers that represent meaning)
# and lets you search by SEMANTIC SIMILARITY — meaning similar concepts match,
# even if they use different words.
#
# Example: In a regular database, "car" and "automobile" are completely different.
# In a vector database, they would be very close to each other because they mean the same thing.
#
# ChromaDB does the conversion automatically using a built-in embedding function.

client_chroma = chromadb.Client()
# chromadb.Client() creates an in-memory ChromaDB database.
# "In-memory" means it only exists while the program is running — it's not saved to disk.
# When you stop the program, the database disappears. This is fine for our learning project.
# In a real production system, you'd use chromadb.PersistentClient(path="./db") to save to disk.

collection = client_chroma.create_collection(
    # A "collection" in ChromaDB is like a table in a regular database — it holds related data.
    # We create one collection to hold all the chunks from our document.
    name="document_chunks"  # Give the collection a name. Can be anything descriptive.
)

print("Storing chunks in ChromaDB... (this may take a moment)")

for i, chunk in enumerate(chunks):
    # "for i, chunk in enumerate(chunks):" is a loop that goes through every chunk.
    # "enumerate" gives us both the INDEX (position number) and the VALUE of each item.
    # i = 0, 1, 2, 3... (the position number)
    # chunk = the actual text of each chunk

    collection.add(
        # .add() stores one item in the collection.
        documents=[chunk],           # "documents" is the actual text content. Must be a list.
                                      # ChromaDB will automatically convert this to a vector.
        ids=[f"chunk_{i}"]           # Every item in ChromaDB needs a unique ID string.
                                      # We use f"chunk_0", f"chunk_1", f"chunk_2", etc.
                                      # f-strings let us insert the variable i into the string.
    )

print(f"Stored {len(chunks)} chunks in ChromaDB. Ready to answer questions!")


# ── Step 5: Set up Claude client and system prompt ───────────────────────────

anthropic_client = anthropic.Anthropic(api_key=api_key)
# Create the Anthropic client to communicate with Claude.
# We name it anthropic_client (not just "client") to avoid confusion with client_chroma above.

system_prompt = """You are a document assistant. Your job is to answer questions about a document.

IMPORTANT RULES:
1. Answer questions ONLY based on the provided context from the document.
2. If the answer is not in the provided context, say exactly: "I don't have that information in the document."
3. Do not use any outside knowledge. Only use what is in the context.
4. When you give an answer, briefly mention which part of the document supports your answer.
5. Be concise and helpful.
"""
# This system prompt is critical for RAG. It prevents Claude from "hallucinating" — making up
# information that isn't in the document. By saying "ONLY based on the provided context",
# we force Claude to stick to what the document actually says.


# ── Step 6: Interactive question-answering loop ──────────────────────────────
# Now the program waits for the user to ask questions.
# For each question, we:
#   1. Search ChromaDB for the most relevant chunks
#   2. Send those chunks + the question to Claude
#   3. Print Claude's answer
# The user types 'quit' to exit.

print("\n" + "="*60)
print("  Ask My Doc — Document Question Answering System")
print("="*60)
print(f"Document loaded: {doc_path}")
print("Type your question and press Enter. Type 'quit' to exit.")
print("="*60 + "\n")

while True:
    # "while True:" starts an infinite loop. The user keeps asking questions
    # until they type "quit", which triggers "break" to exit the loop.

    question = input("Your question: ")  # Wait for the user to type a question and press Enter.
                                          # Whatever they type is stored in the variable "question".

    question = question.strip()  # Remove any extra spaces or newlines from the input.

    if question.lower() == "quit":
        # .lower() converts the string to lowercase. This means "QUIT", "Quit", "quit" all work.
        # We check if the lowercased question equals the string "quit".
        print("Goodbye! Thanks for using Ask My Doc.")
        break  # Exit the while True loop. The program will end.

    if not question:  # If the user just pressed Enter without typing anything...
        print("Please type a question first.")
        continue      # "continue" skips the rest of this loop iteration and goes back to the top.
                       # So we go back to asking for a question without doing anything else.

    # ── Step 6a: Search ChromaDB for relevant chunks ──────────────────────
    print("\nSearching document for relevant sections...")

    search_results = collection.query(
        # .query() searches the ChromaDB collection for chunks similar to our question.
        # ChromaDB converts the question into a vector and finds the most similar document vectors.
        query_texts=[question],   # The question we want to find answers for. Must be a list.
        n_results=3               # Return the top 3 most relevant chunks.
                                   # More chunks = more context for Claude, but also more tokens used.
    )

    # search_results is a dictionary with this structure:
    # {
    #   "documents": [["chunk text 1", "chunk text 2", "chunk text 3"]],
    #   "ids": [["chunk_5", "chunk_12", "chunk_3"]],
    #   "distances": [[0.23, 0.45, 0.67]]   <-- lower = more similar
    # }
    # The outer list and the inner list are because ChromaDB can handle multiple queries at once.
    # Since we only asked one question, we take [0] to get the results for our single question.

    retrieved_chunks = search_results["documents"][0]
    # "documents" is the key for the text content.
    # [0] gets the first (and only, in our case) query's results.
    # retrieved_chunks is now a list of 3 text strings — the 3 most relevant chunks.

    retrieved_ids = search_results["ids"][0]
    # "ids" are the chunk IDs. [0] again for the first query's results.
    # retrieved_ids is a list like ["chunk_5", "chunk_12", "chunk_3"]

    # ── Step 6b: Show the user which chunks were found ────────────────────
    print("\n--- Relevant sections found in document ---")
    for idx, (chunk_id, chunk_text) in enumerate(zip(retrieved_ids, retrieved_chunks)):
        # zip(retrieved_ids, retrieved_chunks) pairs each ID with its text.
        # enumerate() gives us the position number too.
        # So for each iteration: idx=position, chunk_id=ID string, chunk_text=text string.
        print(f"\n[Source {idx + 1}: {chunk_id}]")  # idx+1 because we want to show 1, 2, 3 not 0, 1, 2.
        print(f"{chunk_text[:200]}...")              # Show just the first 200 characters of the chunk as a preview.
                                                      # [:200] is slicing — characters 0 through 200.
                                                      # "..." indicates the chunk was truncated for display.
    print("--- End of retrieved sections ---\n")

    # ── Step 6c: Build the context string for Claude ──────────────────────
    # We combine all retrieved chunks into one block of text to send to Claude.
    context = "\n\n---\n\n".join(retrieved_chunks)
    # "\n\n---\n\n".join(list) joins the list items with "---" separator lines between them.
    # This makes it visually clear where one chunk ends and the next begins.
    # Example result:
    # "Chunk 1 text here...
    #
    # ---
    #
    # Chunk 2 text here...
    #
    # ---
    #
    # Chunk 3 text here..."

    # ── Step 6d: Build the user message for Claude ────────────────────────
    user_message = f"""Here is the relevant context from the document:

CONTEXT:
{context}

QUESTION:
{question}

Please answer the question based only on the context provided above."""
    # We clearly separate the context from the question with labels.
    # This helps Claude understand the structure of the request.

    # ── Step 6e: Send to Claude and get the answer ────────────────────────
    print("Asking Claude...")

    response = anthropic_client.messages.create(
        model="claude-opus-4-6",     # Which Claude model to use.
        max_tokens=1024,              # Maximum length of Claude's answer.
        system=system_prompt,         # The rules: only answer from context.
        messages=[
            {
                "role": "user",           # This message is from the user (us).
                "content": user_message   # The context + question we built above.
            }
        ]
    )

    answer = response.content[0].text  # Extract Claude's answer text from the response.
                                         # response.content is a list; [0] is the first item; .text is the string.

    # ── Step 6f: Print the answer ─────────────────────────────────────────
    print("\n" + "="*60)
    print("ANSWER:")
    print("-"*60)
    print(answer)           # Print Claude's full answer.
    print("="*60)
    print(f"(Tokens used: {response.usage.input_tokens} input, {response.usage.output_tokens} output)\n")
    # Show token usage after each question so students can see the cost building up.

# ── Program ends here when the user types 'quit' ────────────────────────────
# The "break" statement in the loop above will cause the while loop to stop,
# and then the program reaches this point and exits naturally.
