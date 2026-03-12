# personal_assistant.py
# A personal AI assistant with persistent memory using ChromaDB.
# This is the core of Phase 3: learning how agents remember things across sessions.

# --- Standard library imports ---
import os           # For reading environment variables and checking file paths
import json         # For converting Python dicts to strings (to store in ChromaDB)
import uuid         # For generating unique IDs for each memory entry
import datetime     # For timestamping when memories were created

# --- Third-party imports ---
from dotenv import load_dotenv          # Reads the .env file so we can access ANTHROPIC_API_KEY
import anthropic                        # The official Anthropic Python SDK for Claude
import chromadb                         # The vector database that stores our memories on disk
from chromadb.utils import embedding_functions  # Pre-built functions that turn text into vectors

# --- Load environment variables from .env file ---
# This reads ANTHROPIC_API_KEY=sk-ant-... from the .env file into os.environ
load_dotenv()

# --- Constants ---
# The directory where ChromaDB will persist data to disk
# Using a relative path — ChromaDB creates this folder automatically
MEMORY_DB_PATH = "./memory_db"

# The name of the ChromaDB collection (like a "table" in a regular database)
COLLECTION_NAME = "personal_memories"

# How many messages to keep in short-term context (the last N messages)
SHORT_TERM_LIMIT = 10

# Claude model to use — claude-opus-4-6 is powerful and great at extracting facts
MODEL_NAME = "claude-opus-4-6"

# Maximum tokens Claude can return in a single response
MAX_TOKENS = 1024

# How many relevant memories to retrieve from ChromaDB for each message
TOP_K_MEMORIES = 5


# ==============================================================================
# SECTION 1: CHROMADB SETUP
# ChromaDB is our long-term memory storage. It stores text as vectors on disk.
# "Vectors" are lists of numbers that represent the meaning of text.
# Similar meanings → similar vectors → ChromaDB can find related memories.
# ==============================================================================

def get_chroma_client():
    """
    Creates and returns a persistent ChromaDB client.
    'Persistent' means data is saved to disk so it survives app restarts.
    """
    # PersistentClient saves data to MEMORY_DB_PATH folder on disk
    # Every time you restart the app, this data is still there
    client = chromadb.PersistentClient(path=MEMORY_DB_PATH)
    return client  # Return the client so other functions can use it


def get_or_create_collection(client):
    """
    Gets an existing ChromaDB collection or creates a new one.
    A 'collection' is like a folder where we store related memories.
    We use a sentence-transformer model to convert text into vectors.
    """
    # SentenceTransformerEmbeddingFunction converts text → numbers (vectors)
    # "all-MiniLM-L6-v2" is a small, fast model that runs locally (no API needed)
    # It will be downloaded automatically the first time you run this
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # A lightweight local embedding model
    )

    # get_or_create_collection:
    # - If "personal_memories" collection exists → return it
    # - If it doesn't exist → create it with our embedding function
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,           # The name of our memory store
        embedding_function=embedding_fn  # How to turn text into vectors
    )

    return collection  # Return the collection for use in memory functions


# ==============================================================================
# SECTION 2: MEMORY EXTRACTION
# After each user message, we ask Claude to extract important facts.
# These facts get stored as long-term memories in ChromaDB.
# Example: "My name is Alex" → fact: "User's name is Alex"
# ==============================================================================

def extract_memories(client_ai, conversation_turn: str) -> list[str]:
    """
    Asks Claude to extract memory-worthy facts from a single conversation turn.
    A "conversation turn" is one user message + one assistant reply combined.

    Args:
        client_ai: The Anthropic client (used to call Claude)
        conversation_turn: A string combining the user message and assistant reply

    Returns:
        A list of fact strings, e.g. ["User's name is Alex", "User likes Python"]
    """

    # This special prompt tells Claude to act as a memory extractor, not a conversationalist
    # We're using Claude as a tool here — a fact-extraction utility
    extraction_prompt = f"""You are a memory extraction system. Your job is to identify important facts from a conversation turn that should be remembered for future reference.

Extract ONLY facts that are:
1. Personal information (name, job, location, age)
2. Preferences (likes, dislikes, hobbies, favorite things)
3. Important tasks or goals mentioned
4. Technical preferences (programming languages, tools, systems they use)
5. Any strong opinions expressed

From this conversation turn, extract memorable facts as a JSON array of strings.
If there are no memorable facts, return an empty array: []

Conversation turn:
{conversation_turn}

Return ONLY a JSON array, nothing else. Example: ["User's name is Alex", "User prefers Python over JavaScript"]"""

    # Call Claude to extract memories — this is a quick, focused call
    response = client_ai.messages.create(
        model=MODEL_NAME,            # The Claude model to use
        max_tokens=512,              # Short response expected (just a JSON array)
        messages=[
            {
                "role": "user",      # We're sending a user message to Claude
                "content": extraction_prompt  # The prompt asking for memory extraction
            }
        ]
    )

    # Extract the text content from Claude's response
    raw_response = response.content[0].text.strip()

    # Try to parse the JSON array Claude returned
    try:
        # json.loads converts the string like '["fact1", "fact2"]' into a Python list
        memories = json.loads(raw_response)

        # Make sure it's actually a list (not some other JSON type)
        if isinstance(memories, list):
            return memories  # Return the list of memory strings
        else:
            return []  # Return empty list if Claude returned something unexpected

    except json.JSONDecodeError:
        # If Claude's response wasn't valid JSON, return empty list
        # This can happen if Claude adds explanation text before/after the JSON
        return []  # Safe fallback — don't crash, just skip memory extraction


# ==============================================================================
# SECTION 3: STORING MEMORIES IN CHROMADB
# We store each extracted fact as a separate document in ChromaDB.
# ChromaDB automatically converts the text to a vector using our embedding function.
# ==============================================================================

def store_memories(collection, memories: list[str]):
    """
    Stores a list of memory strings in ChromaDB.
    Each memory is stored as a separate document with a unique ID and timestamp.

    Args:
        collection: The ChromaDB collection to store memories in
        memories: List of fact strings to store
    """

    # If no memories were extracted, nothing to store — return early
    if not memories:
        return  # Nothing to do, exit the function

    # Get the current timestamp to record when this memory was created
    timestamp = datetime.datetime.now().isoformat()  # e.g. "2026-03-12T10:30:00"

    # Prepare the data structures ChromaDB needs:
    ids = []         # Unique ID for each memory (ChromaDB requires unique IDs)
    documents = []   # The actual text of each memory
    metadatas = []   # Extra information about each memory (when it was created)

    # Loop through each memory string and prepare it for storage
    for memory_text in memories:
        # uuid4() generates a random unique ID like "a3f8c2d1-..."
        # str() converts it to a string since ChromaDB IDs must be strings
        memory_id = str(uuid.uuid4())

        ids.append(memory_id)              # Add the unique ID
        documents.append(memory_text)      # Add the memory text
        metadatas.append({                 # Add metadata about this memory
            "timestamp": timestamp,        # When it was created
            "type": "long_term_memory"     # Tag it as a long-term memory
        })

    # Store all memories in ChromaDB in one batch call
    # ChromaDB will automatically:
    # 1. Convert each document string to a vector using our embedding function
    # 2. Store the vector, document, and metadata on disk
    collection.add(
        ids=ids,             # Unique IDs for deduplication
        documents=documents, # The memory text strings
        metadatas=metadatas  # The metadata dicts
    )

    # Confirm how many memories were stored (helpful for debugging)
    print(f"\n  [Memory] Stored {len(memories)} new memory/memories.")


# ==============================================================================
# SECTION 4: RETRIEVING RELEVANT MEMORIES
# Before Claude responds, we search ChromaDB for memories relevant to the
# current user message. This is semantic search — it finds memories that are
# SIMILAR IN MEANING, not just exact keyword matches.
# ==============================================================================

def retrieve_relevant_memories(collection, query: str) -> list[str]:
    """
    Searches ChromaDB for memories semantically similar to the query.
    Returns the top K most relevant memory strings.

    Args:
        collection: The ChromaDB collection to search
        query: The user's current message (used as the search query)

    Returns:
        A list of relevant memory strings (may be empty if nothing relevant found)
    """

    # First check if we have any memories stored at all
    # collection.count() returns the total number of documents stored
    if collection.count() == 0:
        return []  # No memories stored yet, return empty list

    # query() searches ChromaDB for documents most similar to our query
    # ChromaDB converts the query to a vector and finds the closest stored vectors
    # n_results: how many results to return (we want the top 5 most relevant)
    results = collection.query(
        query_texts=[query],        # The search query (wrapped in a list)
        n_results=min(TOP_K_MEMORIES, collection.count())  # Don't ask for more than we have
    )

    # results["documents"] is a list of lists (one list per query)
    # We only have one query, so we take results["documents"][0]
    # This gives us a flat list of memory strings
    retrieved_memories = results["documents"][0] if results["documents"] else []

    return retrieved_memories  # Return the list of relevant memories


# ==============================================================================
# SECTION 5: DISPLAY ALL MEMORIES
# The user can type 'memories' to see everything we know about them.
# This is a transparency feature — users should know what data we store.
# ==============================================================================

def display_all_memories(collection):
    """
    Prints all stored memories to the console.
    Used when the user types the 'memories' command.

    Args:
        collection: The ChromaDB collection containing our memories
    """

    # Check if any memories exist
    total = collection.count()  # How many memories do we have?

    # If no memories, tell the user
    if total == 0:
        print("\n  [Memories] No memories stored yet. Tell me about yourself!")
        return  # Nothing more to do

    # get() with no filters returns ALL documents in the collection
    # include=["documents", "metadatas"] tells ChromaDB what data to return
    all_data = collection.get(
        include=["documents", "metadatas"]  # Get both the text and the metadata
    )

    # Print a header
    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║           STORED MEMORIES ({total} total)           ║")
    print(f"  ╚══════════════════════════════════════════════════╝")

    # Loop through each memory and print it with its timestamp
    for i, (doc, meta) in enumerate(zip(all_data["documents"], all_data["metadatas"])):
        # meta["timestamp"] is in ISO format, we'll just show the date part
        timestamp = meta.get("timestamp", "unknown")[:10]  # "2026-03-12" (first 10 chars)
        print(f"  [{i+1}] ({timestamp}) {doc}")  # Print numbered memory with date

    print()  # Empty line for spacing


# ==============================================================================
# SECTION 6: CLEAR ALL MEMORIES
# The user can type 'clear' to erase all stored memories.
# Important for privacy and testing.
# ==============================================================================

def clear_all_memories(client, collection):
    """
    Deletes the entire ChromaDB collection and recreates it empty.
    This is the nuclear option — it erases everything.

    Args:
        client: The ChromaDB client (needed to delete and recreate collection)
        collection: The current collection (will be replaced)

    Returns:
        The new empty collection
    """

    # delete_collection removes the entire collection from disk
    client.delete_collection(name=COLLECTION_NAME)

    # get_or_create_collection recreates it fresh and empty
    new_collection = get_or_create_collection(client)

    print("\n  [Memory] All memories cleared. Starting fresh!")

    return new_collection  # Return the new empty collection so the caller can use it


# ==============================================================================
# SECTION 7: THE MAIN CHAT FUNCTION
# This is where everything comes together.
# Each turn: retrieve memories → build context → get Claude's reply → extract new memories
# ==============================================================================

def chat(user_message: str, short_term_memory: list, collection, client_ai) -> str:
    """
    Processes one user message and returns Claude's response.
    This function orchestrates the entire memory-aware conversation loop.

    Args:
        user_message: The text the user just typed
        short_term_memory: List of recent messages (last 10 turns)
        collection: ChromaDB collection for long-term memories
        client_ai: Anthropic client for calling Claude

    Returns:
        Claude's response as a string
    """

    # STEP 1: Retrieve relevant long-term memories for this message
    # We search ChromaDB to find memories related to what the user is saying
    relevant_memories = retrieve_relevant_memories(collection, user_message)

    # STEP 2: Build the system prompt with any relevant memories injected
    # The system prompt tells Claude who it is and what it knows about the user
    if relevant_memories:
        # Format the memories as a readable list for Claude
        memory_context = "\n".join(f"- {m}" for m in relevant_memories)

        # System prompt includes retrieved memories so Claude can use them
        system_prompt = f"""You are a helpful personal assistant with memory capabilities.

You have the following relevant memories about the user from previous conversations:
{memory_context}

Use these memories naturally in your responses when relevant. Be warm, personable, and remember details about the user to make the conversation feel continuous and personal. Don't explicitly say "based on my memory" — just incorporate what you know naturally."""

    else:
        # No relevant memories found, use a plain system prompt
        system_prompt = """You are a helpful personal assistant with memory capabilities.

You don't have any stored memories about this user yet. Be warm and personable, and try to learn about them through conversation. When they share personal information, acknowledge it naturally."""

    # STEP 3: Build the messages list for Claude
    # We include short-term memory (recent conversation) so Claude has context
    # short_term_memory already contains the recent back-and-forth exchanges
    messages_for_claude = short_term_memory.copy()  # Copy to avoid modifying the original

    # Add the current user message to the messages list
    messages_for_claude.append({
        "role": "user",         # This message is from the user
        "content": user_message # The actual text of the message
    })

    # STEP 4: Call Claude with the full context
    # Claude sees: system prompt (with memories) + recent conversation + current message
    response = client_ai.messages.create(
        model=MODEL_NAME,                   # claude-opus-4-6
        max_tokens=MAX_TOKENS,              # Maximum length of Claude's response
        system=system_prompt,               # Injected memories + persona instructions
        messages=messages_for_claude        # Recent conversation history + current message
    )

    # Extract the text from Claude's response object
    assistant_reply = response.content[0].text

    # STEP 5: Update short-term memory with this exchange
    # Add the user message to short-term memory
    short_term_memory.append({
        "role": "user",         # Mark as user message
        "content": user_message # The user's text
    })

    # Add Claude's reply to short-term memory
    short_term_memory.append({
        "role": "assistant",        # Mark as assistant (Claude) message
        "content": assistant_reply  # Claude's response text
    })

    # STEP 6: Trim short-term memory to keep only the last SHORT_TERM_LIMIT messages
    # We keep the last 10 messages (5 exchanges) to avoid context window overflow
    # If we have more than SHORT_TERM_LIMIT*2 messages, slice off the oldest ones
    if len(short_term_memory) > SHORT_TERM_LIMIT * 2:
        # Keep only the last SHORT_TERM_LIMIT*2 messages (10 by default)
        short_term_memory = short_term_memory[-(SHORT_TERM_LIMIT * 2):]

    # STEP 7: Extract new long-term memories from this exchange
    # Build a "conversation turn" string combining user message + assistant reply
    conversation_turn = f"User: {user_message}\nAssistant: {assistant_reply}"

    # Ask Claude (separately) to extract any important facts from this exchange
    new_memories = extract_memories(client_ai, conversation_turn)

    # Store the extracted facts in ChromaDB for future sessions
    if new_memories:
        store_memories(collection, new_memories)

    return assistant_reply  # Return Claude's reply to display to the user


# ==============================================================================
# SECTION 8: MAIN ENTRY POINT — THE CLI INTERFACE
# This is the command-line interface the user types into.
# It loops forever, reading input and printing responses, until user types 'quit'.
# ==============================================================================

def main():
    """
    Main function that runs the CLI chat interface.
    Sets up ChromaDB, initializes the Anthropic client, then enters the chat loop.
    """

    # --- Setup: Load API key ---
    api_key = os.getenv("ANTHROPIC_API_KEY")  # Read from .env file (loaded at top)

    # If no API key is found, we can't proceed — tell the user what to do
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment.")
        print("Please create a .env file with: ANTHROPIC_API_KEY=sk-ant-your-key-here")
        return  # Exit the function (and the program)

    # --- Setup: Initialize Anthropic client ---
    # The client handles all communication with the Claude API
    client_ai = anthropic.Anthropic(api_key=api_key)

    # --- Setup: Initialize ChromaDB ---
    # This connects to (or creates) our persistent memory database
    chroma_client = get_chroma_client()

    # Get or create the memory collection where facts are stored
    collection = get_or_create_collection(chroma_client)

    # --- Setup: Initialize short-term memory ---
    # This list holds the last N conversation turns in Python memory (not on disk)
    # It resets every time the app starts — that's what makes it "short-term"
    short_term_memory = []  # Start with empty conversation history

    # --- Welcome message ---
    # Tell the user how many memories we already have from previous sessions
    existing_memories = collection.count()  # Check how many memories are stored

    print("\n" + "="*60)
    print("  PERSONAL ASSISTANT WITH PERSISTENT MEMORY")
    print("  Powered by Claude claude-opus-4-6 + ChromaDB")
    print("="*60)

    # Show how many memories survived from previous sessions
    if existing_memories > 0:
        print(f"\n  Welcome back! I remember {existing_memories} facts about you.")
        print("  (Type 'memories' to see what I know)")
    else:
        print("\n  Hello! I'm your personal assistant.")
        print("  I'll remember important things you tell me, even after you close this app.")

    print("\n  Commands:")
    print("  'memories' — see all stored facts about you")
    print("  'clear'    — erase all memories")
    print("  'quit'     — exit the app")
    print("-"*60 + "\n")

    # --- Main chat loop ---
    # This loop runs forever until the user types 'quit'
    while True:

        # Prompt the user for input with a visual indicator
        try:
            user_input = input("  You: ").strip()  # .strip() removes leading/trailing whitespace
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C or Ctrl+D gracefully
            print("\n\n  Goodbye! Your memories are saved.")
            break  # Exit the loop

        # Skip empty input (user just pressed Enter without typing anything)
        if not user_input:
            continue  # Go back to the top of the loop

        # --- Handle special commands ---

        # Command: 'quit' or 'exit' — stop the program
        if user_input.lower() in ["quit", "exit"]:
            print("\n  Goodbye! Your memories are safely stored. See you next time!")
            break  # Exit the while loop, ending the program

        # Command: 'memories' — display all stored long-term memories
        if user_input.lower() == "memories":
            display_all_memories(collection)  # Print all facts from ChromaDB
            continue  # Go back to the loop (don't send this to Claude)

        # Command: 'clear' — erase all memories
        if user_input.lower() == "clear":
            # Ask for confirmation before erasing everything
            confirm = input("  Are you sure? This will erase ALL memories. (yes/no): ").strip().lower()
            if confirm == "yes":
                collection = clear_all_memories(chroma_client, collection)  # Erase and recreate
            else:
                print("  Memory clear cancelled.")  # User changed their mind
            continue  # Go back to the loop

        # --- Normal chat: send message to Claude ---
        print("\n  Assistant: ", end="", flush=True)  # Print label before the response

        # Call the main chat function — this handles memory retrieval, Claude API, memory storage
        try:
            reply = chat(
                user_message=user_input,           # What the user typed
                short_term_memory=short_term_memory,  # Recent conversation history
                collection=collection,             # ChromaDB memory store
                client_ai=client_ai                # Anthropic API client
            )

            # Print Claude's response
            print(reply)  # The actual reply text from Claude
            print()       # Blank line for readability

        except anthropic.APIError as e:
            # Handle API errors (network issues, rate limits, invalid API key)
            print(f"\n  ERROR: Claude API error: {e}")
            print("  Please check your API key and internet connection.")

        except Exception as e:
            # Handle any other unexpected errors
            print(f"\n  ERROR: Unexpected error: {e}")
            print("  Please try again.")


# --- Run the program ---
# This standard Python pattern ensures main() only runs when we execute this file directly
# (not when it's imported as a module by another script)
if __name__ == "__main__":
    main()  # Start the personal assistant
