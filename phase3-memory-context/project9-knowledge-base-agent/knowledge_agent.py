# knowledge_agent.py
# A conversational RAG (Retrieval-Augmented Generation) agent over a ChromaDB knowledge base.
# Run ingest.py first to populate the knowledge base, then run this file.
# Usage: python knowledge_agent.py

# --- Standard library imports ---
import os           # For reading environment variables

# --- Third-party imports ---
from dotenv import load_dotenv          # Loads .env file into os.environ
import anthropic                        # Anthropic SDK for calling Claude
import chromadb                         # Vector database for storing/searching documents
from chromadb.utils import embedding_functions  # Text-to-vector conversion utilities

# --- Load environment variables ---
load_dotenv()  # Reads ANTHROPIC_API_KEY from .env file

# --- Constants ---
MODEL_NAME = "claude-opus-4-6"  # Claude model to use
MAX_TOKENS = 1024                # Max tokens in Claude's response
CHROMA_DB_PATH = "./knowledge_db"   # Path to the persisted ChromaDB (created by ingest.py)
COLLECTION_NAME = "company_knowledge"   # Must match the collection name in ingest.py
TOP_K_CHUNKS = 5             # How many relevant chunks to retrieve per query
HISTORY_TURNS = 5            # How many conversation turns to keep in context (5 = 10 messages)


# ==============================================================================
# SECTION 1: CHROMADB CONNECTION
# We're connecting to an EXISTING database (created by ingest.py).
# We don't create new collections here — we just read from them.
# ==============================================================================

def connect_to_knowledge_base():
    """
    Connects to the existing ChromaDB knowledge base created by ingest.py.
    Returns the ChromaDB collection, or None if the database doesn't exist.
    """

    # Check if the ChromaDB directory exists
    # If ingest.py was never run, this directory won't exist
    if not os.path.isdir(CHROMA_DB_PATH):
        print(f"ERROR: Knowledge base not found at '{CHROMA_DB_PATH}'")
        print("Please run ingest.py first to build the knowledge base:")
        print("  python ingest.py ./sample_docs")
        return None  # Return None to signal failure

    # Connect to the existing ChromaDB (PersistentClient reads from disk)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Use the same embedding function as ingest.py
    # IMPORTANT: Must be the same model, or vectors won't be comparable
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # Same model used in ingest.py
    )

    try:
        # get_collection (not get_or_create) raises an error if collection doesn't exist
        # This is intentional — we want to know if ingest.py was never run
        collection = client.get_collection(
            name=COLLECTION_NAME,            # Must match the name in ingest.py
            embedding_function=embedding_fn  # Same embedding function
        )

        return collection  # Return the collection for querying

    except Exception as e:
        # Collection doesn't exist — ingest.py hasn't been run
        print(f"ERROR: Collection '{COLLECTION_NAME}' not found.")
        print("Please run ingest.py first:")
        print("  python ingest.py ./sample_docs")
        return None  # Signal failure


# ==============================================================================
# SECTION 2: RETRIEVAL
# This is the "R" in RAG. Before asking Claude, we search for relevant passages.
# ChromaDB uses semantic similarity to find chunks related to the question.
# ==============================================================================

def retrieve_relevant_chunks(collection, query: str) -> list[dict]:
    """
    Searches ChromaDB for document chunks most relevant to the query.
    Returns a list of dicts, each containing the chunk text and its source metadata.

    Args:
        collection: The ChromaDB collection to search
        query: The user's question (used as the search query)

    Returns:
        List of dicts: [{"text": "...", "filename": "...", "chunk_index": 0}, ...]
    """

    # Don't search an empty collection
    if collection.count() == 0:
        return []  # Nothing to retrieve

    # Determine how many results to return (can't ask for more than we have)
    n_results = min(TOP_K_CHUNKS, collection.count())

    # query() is the semantic search function
    # ChromaDB converts the query to a vector and finds the closest stored vectors
    results = collection.query(
        query_texts=[query],                    # The search query (list because you can batch)
        n_results=n_results,                    # How many results to return
        include=["documents", "metadatas", "distances"]  # What data to return
    )

    # results structure (for a single query):
    # results["documents"][0] = list of document strings
    # results["metadatas"][0] = list of metadata dicts
    # results["distances"][0] = list of distance scores (lower = more similar)

    # Build a clean list of result dicts
    chunks = []
    documents = results["documents"][0] if results["documents"] else []    # List of texts
    metadatas = results["metadatas"][0] if results["metadatas"] else []    # List of metadata
    distances = results["distances"][0] if results["distances"] else []    # List of distances

    # Zip together the parallel lists
    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append({
            "text": doc,                                    # The chunk text
            "filename": meta.get("filename", "unknown"),   # Source document name
            "chunk_index": meta.get("chunk_index", 0),     # Chunk position in document
            "total_chunks": meta.get("total_chunks", 1),   # Total chunks in document
            "distance": dist                                # Similarity score (lower = better)
        })

    return chunks  # Return the list of relevant chunk dicts


def format_chunks_for_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a readable string for Claude's context.
    Each chunk is labeled with its source document for citation.

    Args:
        chunks: List of chunk dicts from retrieve_relevant_chunks()

    Returns:
        A formatted string to inject into Claude's prompt
    """

    if not chunks:
        return "No relevant documents found in the knowledge base."

    # Build the formatted context string
    context_parts = []  # Will hold each formatted chunk

    for i, chunk in enumerate(chunks, 1):
        # Format each chunk with its source information
        # This enables source citation in Claude's response
        formatted = f"[Source {i}: {chunk['filename']} (chunk {chunk['chunk_index']+1}/{chunk['total_chunks']})]\n{chunk['text']}"
        context_parts.append(formatted)

    # Join all chunks with double newlines for readability
    return "\n\n".join(context_parts)


# ==============================================================================
# SECTION 3: KNOWLEDGE BASE INVENTORY
# The user can type 'sources' to see all documents in the knowledge base.
# ==============================================================================

def get_all_sources(collection) -> dict:
    """
    Returns a summary of all documents in the knowledge base.
    Groups chunks by filename and counts chunks per document.

    Args:
        collection: The ChromaDB collection

    Returns:
        Dict mapping filename to chunk count: {"policy.txt": 5, "faq.txt": 3}
    """

    if collection.count() == 0:
        return {}  # Empty knowledge base

    # Get all documents with their metadata
    all_data = collection.get(include=["metadatas"])

    # Group chunks by filename
    sources = {}  # filename -> chunk count

    for meta in all_data["metadatas"]:
        filename = meta.get("filename", "unknown")  # Get filename from metadata

        if filename not in sources:
            sources[filename] = 0   # Initialize count for this file

        sources[filename] += 1  # Increment chunk count for this file

    return sources  # Return the filename -> chunk count mapping


def display_sources(collection):
    """
    Prints a formatted list of all documents in the knowledge base.
    Called when the user types 'sources'.
    """
    sources = get_all_sources(collection)  # Get filename -> count mapping

    if not sources:
        print("\n  [Knowledge Base] No documents ingested yet.")
        print("  Run: python ingest.py ./sample_docs")
        return

    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║       KNOWLEDGE BASE CONTENTS                    ║")
    print(f"  ║       Total chunks: {collection.count():<26} ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print()

    # Print each document with its chunk count
    for i, (filename, chunk_count) in enumerate(sorted(sources.items()), 1):
        print(f"  [{i}] {filename}")
        print(f"       Chunks: {chunk_count} ({chunk_count * 800} chars approx)")

    print()


# ==============================================================================
# SECTION 4: THE RAG CHAT FUNCTION
# This is the core: retrieve relevant chunks, inject into Claude's prompt,
# get a grounded answer that cites sources.
# ==============================================================================

def rag_chat(query: str, collection, conversation_history: list, client_ai) -> str:
    """
    Performs one RAG-powered conversation turn:
    1. Retrieve relevant document chunks from ChromaDB
    2. Build a prompt with retrieved context
    3. Ask Claude to answer based on the context
    4. Return the answer (with source citations)

    Args:
        query: The user's question
        collection: ChromaDB collection to search
        conversation_history: Recent conversation turns (last HISTORY_TURNS exchanges)
        client_ai: Anthropic API client

    Returns:
        Claude's answer as a string
    """

    # STEP 1: Retrieve relevant chunks from the knowledge base
    relevant_chunks = retrieve_relevant_chunks(collection, query)

    # STEP 2: Format the chunks into a context string for Claude
    context = format_chunks_for_context(relevant_chunks)

    # STEP 3: Build the system prompt
    # The system prompt tells Claude HOW to use the retrieved context
    system_prompt = f"""You are a helpful knowledge base assistant with access to company documents.

RETRIEVED CONTEXT FROM KNOWLEDGE BASE:
{context}

INSTRUCTIONS:
1. Answer the user's question based PRIMARILY on the retrieved context above.
2. If the context contains the answer, use it and cite the source like: "(Source: filename.txt)"
3. If the context does NOT contain the answer, clearly say: "I don't have information about that in the knowledge base" and then optionally provide general knowledge if relevant.
4. Be clear about the distinction: knowledge base information vs. your general knowledge.
5. Keep answers concise but complete.
6. If multiple sources support an answer, mention all of them."""

    # STEP 4: Build the messages list with conversation history + current question
    messages = conversation_history.copy()  # Copy to avoid modifying the original

    # Add the current user question
    messages.append({
        "role": "user",
        "content": query  # The question to answer
    })

    # STEP 5: Call Claude with the RAG context
    response = client_ai.messages.create(
        model=MODEL_NAME,         # claude-opus-4-6
        max_tokens=MAX_TOKENS,    # Max response length
        system=system_prompt,     # System prompt contains retrieved context
        messages=messages         # Conversation history + current question
    )

    # Extract Claude's response text
    answer = response.content[0].text

    return answer  # Return the answer string


# ==============================================================================
# SECTION 5: CONVERSATION HISTORY MANAGEMENT
# We keep the last HISTORY_TURNS exchanges (each turn = 1 user + 1 assistant message).
# This gives Claude context about what was asked before.
# ==============================================================================

def update_history(history: list, user_message: str, assistant_reply: str) -> list:
    """
    Adds a conversation turn to history and trims it to HISTORY_TURNS exchanges.

    Args:
        history: Current conversation history list
        user_message: The user's question
        assistant_reply: The assistant's answer

    Returns:
        Updated and trimmed history list
    """

    # Add the user message
    history.append({
        "role": "user",
        "content": user_message  # User's question
    })

    # Add the assistant reply
    history.append({
        "role": "assistant",
        "content": assistant_reply  # Claude's answer
    })

    # Trim to last HISTORY_TURNS * 2 messages (each turn has 2 messages)
    max_messages = HISTORY_TURNS * 2  # 5 turns * 2 = 10 messages

    if len(history) > max_messages:
        history = history[-max_messages:]  # Keep only the most recent messages

    return history  # Return updated history


# ==============================================================================
# SECTION 6: MAIN CLI INTERFACE
# ==============================================================================

def main():
    """
    Main function: connects to knowledge base and runs the conversational loop.
    """

    # --- Load API key ---
    api_key = os.getenv("ANTHROPIC_API_KEY")  # Read from .env file

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment.")
        print("Please create a .env file with: ANTHROPIC_API_KEY=sk-ant-your-key-here")
        return  # Exit

    # --- Initialize Anthropic client ---
    client_ai = anthropic.Anthropic(api_key=api_key)  # Create the API client

    # --- Connect to knowledge base ---
    print("\nConnecting to knowledge base...")
    collection = connect_to_knowledge_base()  # Connect to ChromaDB

    if collection is None:
        return  # Exit if knowledge base isn't available

    # --- Get knowledge base stats ---
    total_chunks = collection.count()  # Total chunks in the database
    sources = get_all_sources(collection)  # Documents in the database

    # --- Welcome message ---
    print()
    print("="*60)
    print("  KNOWLEDGE BASE AGENT")
    print(f"  Model: {MODEL_NAME}")
    print("="*60)
    print(f"\n  Knowledge base contains:")
    print(f"  - {total_chunks} chunks from {len(sources)} document(s)")

    # List each document
    for filename, count in sorted(sources.items()):
        print(f"  - {filename} ({count} chunks)")

    print()
    print("  Commands:")
    print("  'sources'  — list all documents in the knowledge base")
    print("  'quit'     — exit")
    print("-"*60)
    print("\n  Ask me anything about the documents in the knowledge base!")
    print()

    # --- Conversation history ---
    conversation_history = []  # Start with empty history

    # --- Main chat loop ---
    while True:

        # Get user input
        try:
            user_input = input("  You: ").strip()  # .strip() removes extra whitespace
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Goodbye!")
            break  # Exit loop

        # Skip empty input
        if not user_input:
            continue  # Go back to prompt

        # --- Handle special commands ---

        # Quit command
        if user_input.lower() in ["quit", "exit"]:
            print("\n  Goodbye! The knowledge base is saved and ready for next time.")
            break  # Exit the loop

        # Sources command — show all documents
        if user_input.lower() == "sources":
            display_sources(collection)  # Print the document list
            continue  # Back to prompt

        # --- Normal RAG query ---
        print("\n  [Searching knowledge base...]")  # Show that retrieval is happening

        try:
            # Perform RAG: retrieve + generate answer
            answer = rag_chat(
                query=user_input,                        # The user's question
                collection=collection,                   # ChromaDB collection
                conversation_history=conversation_history,  # Recent turns
                client_ai=client_ai                      # Anthropic client
            )

            # Print Claude's answer
            print(f"\n  Assistant: {answer}")
            print()  # Blank line for readability

            # Update conversation history with this exchange
            conversation_history = update_history(
                history=conversation_history,    # Current history
                user_message=user_input,         # What the user asked
                assistant_reply=answer           # What Claude answered
            )

        except anthropic.APIError as e:
            # Handle API errors
            print(f"\n  ERROR: Claude API error: {e}")
            print("  Please check your API key and internet connection.")

        except Exception as e:
            # Handle any other unexpected errors
            print(f"\n  ERROR: {e}")


# --- Entry point ---
if __name__ == "__main__":
    main()
