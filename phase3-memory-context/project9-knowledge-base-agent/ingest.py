# ingest.py
# Script to ingest documents from a directory into ChromaDB.
# Run this first to populate the knowledge base before using knowledge_agent.py
# Usage: python ingest.py [directory_path]
# Example: python ingest.py ./sample_docs

# --- Standard library imports ---
import os           # For file system operations (listing files, reading paths)
import sys          # For reading command-line arguments and exiting
import uuid         # For generating unique chunk IDs
import datetime     # For timestamping when documents were ingested

# --- Third-party imports ---
import chromadb                         # The vector database for storing document chunks
from chromadb.utils import embedding_functions  # Pre-built text-to-vector functions

# --- Constants ---
# Directory where ChromaDB persists data to disk
CHROMA_DB_PATH = "./knowledge_db"

# The ChromaDB collection name for our knowledge base
COLLECTION_NAME = "company_knowledge"

# Chunking parameters
# Chunk size: how many characters per chunk
# Smaller chunks = more precise retrieval but less context
# Larger chunks = more context but may include irrelevant content
CHUNK_SIZE = 800       # Characters per chunk

# Overlap: how many characters to repeat between consecutive chunks
# Overlap prevents a concept from being split across two chunks
CHUNK_OVERLAP = 100    # Characters of overlap between adjacent chunks


# ==============================================================================
# SECTION 1: CHROMADB SETUP
# ==============================================================================

def get_chroma_client():
    """
    Creates and returns a persistent ChromaDB client.
    PersistentClient saves data to disk so it survives between script runs.
    """
    # PersistentClient saves to CHROMA_DB_PATH folder
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client  # Return the connected client


def get_or_create_collection(client):
    """
    Gets or creates the ChromaDB collection for the knowledge base.
    Uses a local sentence-transformer model for embeddings.
    """
    # SentenceTransformerEmbeddingFunction converts text to numerical vectors
    # The "all-MiniLM-L6-v2" model is downloaded automatically on first use
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # Small, fast, local embedding model
    )

    # Get or create the collection with our embedding function
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,            # Collection name
        embedding_function=embedding_fn  # How to create vectors from text
    )

    return collection  # Return the collection


# ==============================================================================
# SECTION 2: DOCUMENT CHUNKING
# Why chunk? Two reasons:
# 1. LLMs have limited context windows — we can't send 100 pages to Claude
# 2. Small chunks make retrieval more precise (less noise in the retrieved text)
# Overlap ensures concepts aren't cut in half at chunk boundaries.
# ==============================================================================

def chunk_document(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Splits a document into overlapping chunks of a specified size.

    Example with chunk_size=10, overlap=2:
    "Hello World, how are you today" →
    ["Hello Worl", "rld, how a", "ow are you", "ou today"]

    Args:
        text: The full document text to chunk
        chunk_size: How many characters per chunk
        overlap: How many characters to repeat between adjacent chunks

    Returns:
        List of text chunks
    """
    # If the document is shorter than one chunk, return it as-is
    if len(text) <= chunk_size:
        return [text.strip()]  # Single chunk, stripped of whitespace

    chunks = []       # Will hold our chunk strings
    start = 0         # Start position for current chunk

    # Slide through the document, creating chunks with overlap
    while start < len(text):
        # End position for this chunk (start + chunk_size, or end of text)
        end = min(start + chunk_size, len(text))

        # Extract the chunk from start to end
        chunk = text[start:end].strip()  # .strip() removes leading/trailing whitespace

        # Only add non-empty chunks
        if chunk:
            chunks.append(chunk)  # Add chunk to our list

        # Move start forward by (chunk_size - overlap) for the next chunk
        # This creates the overlap: we go back 'overlap' characters each step
        start += chunk_size - overlap

        # Safety check: if overlap >= chunk_size, we'd loop forever
        # This shouldn't happen with normal settings, but protect against it
        if chunk_size - overlap <= 0:
            break  # Prevent infinite loop

    return chunks  # Return all chunks


# ==============================================================================
# SECTION 3: FILE READING
# ==============================================================================

def read_text_file(filepath: str) -> str:
    """
    Reads a text file and returns its content as a string.
    Handles encoding errors gracefully (some files have special characters).

    Args:
        filepath: Absolute or relative path to the .txt file

    Returns:
        The file content as a string, or empty string on error
    """
    try:
        # Open the file with UTF-8 encoding (handles most international characters)
        # errors="replace" replaces unrecognized characters with '?' instead of crashing
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()  # Read entire file into memory

        return content  # Return the file content

    except FileNotFoundError:
        # The file doesn't exist
        print(f"  WARNING: File not found: {filepath}")
        return ""  # Return empty string

    except IOError as e:
        # Some other file reading error
        print(f"  WARNING: Could not read {filepath}: {e}")
        return ""  # Return empty string


# ==============================================================================
# SECTION 4: IDEMPOTENT INGESTION
# "Idempotent" means: running the script multiple times has the same effect as running once.
# We achieve this by generating deterministic chunk IDs (based on filename + chunk index).
# If a chunk with that ID already exists in ChromaDB, we skip it.
# ==============================================================================

def generate_chunk_id(filename: str, chunk_index: int) -> str:
    """
    Generates a deterministic ID for a document chunk.
    Using the filename + chunk_index ensures the same chunk always gets the same ID.
    This prevents duplicate chunks when re-running the script.

    Args:
        filename: The source document filename (e.g., "policy.txt")
        chunk_index: The index of this chunk within the document (0, 1, 2, ...)

    Returns:
        A stable string ID like "policy_txt_chunk_003"
    """
    # Replace dots with underscores in filename (IDs can't have dots in some systems)
    safe_filename = filename.replace(".", "_").replace(" ", "_").lower()

    # Create a readable, deterministic ID
    chunk_id = f"{safe_filename}_chunk_{chunk_index:04d}"  # e.g., "policy_txt_chunk_0003"

    return chunk_id  # Return the stable ID


def get_existing_ids(collection) -> set:
    """
    Gets all chunk IDs already stored in the ChromaDB collection.
    Used to skip re-ingesting documents that are already in the database.

    Args:
        collection: The ChromaDB collection to check

    Returns:
        A set of existing chunk ID strings
    """
    # If collection is empty, return empty set
    if collection.count() == 0:
        return set()  # No existing IDs

    # collection.get() with no filters returns everything
    # We only need "ids" — no need to fetch the full document text
    result = collection.get(include=[])  # Empty include list means only IDs returned

    # Convert the list of IDs to a set for O(1) lookup speed
    return set(result["ids"])  # Return set of ID strings


# ==============================================================================
# SECTION 5: MAIN INGESTION FUNCTION
# ==============================================================================

def ingest_directory(directory_path: str):
    """
    Ingests all .txt files from a directory into ChromaDB.
    This is the main function that orchestrates the entire ingestion process.

    Args:
        directory_path: Path to the directory containing .txt files
    """

    # --- Validate the directory ---
    if not os.path.isdir(directory_path):
        print(f"ERROR: '{directory_path}' is not a valid directory.")
        print("Please provide a directory containing .txt files.")
        sys.exit(1)  # Exit with error code 1

    # --- Find all .txt files in the directory ---
    # os.listdir() returns all files and subdirectories in the path
    all_files = os.listdir(directory_path)

    # Filter to only .txt files
    txt_files = [f for f in all_files if f.endswith(".txt")]

    # Sort alphabetically for consistent ordering
    txt_files.sort()

    # Report if no .txt files found
    if not txt_files:
        print(f"WARNING: No .txt files found in '{directory_path}'")
        print("Please add .txt files to the directory and try again.")
        return  # Exit the function

    print(f"\nFound {len(txt_files)} .txt file(s) in '{directory_path}'")
    print()

    # --- Setup ChromaDB ---
    print("Connecting to ChromaDB...")
    client = get_chroma_client()              # Get the persistent ChromaDB client
    collection = get_or_create_collection(client)  # Get or create our collection

    print(f"Collection '{COLLECTION_NAME}' ready.")
    print(f"Current chunk count: {collection.count()}")
    print()

    # --- Get existing IDs (for idempotency) ---
    existing_ids = get_existing_ids(collection)  # Set of already-ingested chunk IDs
    print(f"Already ingested: {len(existing_ids)} chunks (will skip these)")
    print()

    # --- Ingest each file ---
    total_new_chunks = 0        # Count of newly added chunks (across all files)
    total_skipped_chunks = 0    # Count of skipped (duplicate) chunks
    timestamp = datetime.datetime.now().isoformat()  # Timestamp for all chunks in this run

    for file_index, filename in enumerate(txt_files, 1):
        # Build the full path to this file
        filepath = os.path.join(directory_path, filename)

        # Progress indicator: "Ingesting file 1/5: policy.txt..."
        print(f"Ingesting file {file_index}/{len(txt_files)}: {filename}...")

        # Read the file content
        content = read_text_file(filepath)

        # Skip empty files
        if not content.strip():
            print(f"  SKIPPED: {filename} is empty")
            continue  # Move to next file

        # Chunk the document into smaller pieces
        chunks = chunk_document(content)
        print(f"  Split into {len(chunks)} chunks ({CHUNK_SIZE} chars each, {CHUNK_OVERLAP} char overlap)")

        # Prepare data for ChromaDB batch add
        ids_to_add = []         # Chunk IDs
        documents_to_add = []   # Chunk text
        metadatas_to_add = []   # Chunk metadata

        file_new_chunks = 0     # New chunks from this file
        file_skipped = 0        # Skipped chunks from this file

        # Process each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            # Generate a deterministic ID for this chunk
            chunk_id = generate_chunk_id(filename, chunk_index)

            # Check if this chunk already exists in the database (idempotency check)
            if chunk_id in existing_ids:
                file_skipped += 1    # Count skipped chunks
                continue             # Skip this chunk — already ingested

            # New chunk — prepare for ingestion
            ids_to_add.append(chunk_id)    # The unique ID

            documents_to_add.append(chunk_text)  # The actual text content

            metadatas_to_add.append({           # Metadata for filtering/display
                "filename": filename,            # Source document name
                "chunk_index": chunk_index,      # Which chunk within the document
                "total_chunks": len(chunks),     # Total chunks in this document
                "timestamp": timestamp,          # When this was ingested
                "chunk_size": len(chunk_text)    # Actual character count of this chunk
            })

            file_new_chunks += 1  # Count this as a new chunk

        # Add all new chunks for this file to ChromaDB in one batch
        if ids_to_add:
            collection.add(
                ids=ids_to_add,             # Unique IDs (prevents duplicates)
                documents=documents_to_add, # The text content (will be vectorized)
                metadatas=metadatas_to_add  # Metadata for each chunk
            )

        # Report results for this file
        print(f"  Added: {file_new_chunks} new chunks, Skipped: {file_skipped} existing chunks")

        # Accumulate totals
        total_new_chunks += file_new_chunks
        total_skipped_chunks += file_skipped

    # --- Final summary ---
    print()
    print("="*60)
    print("INGESTION COMPLETE")
    print("="*60)
    print(f"Files processed: {len(txt_files)}")
    print(f"New chunks added: {total_new_chunks}")
    print(f"Chunks skipped (already existed): {total_skipped_chunks}")
    print(f"Total chunks in database: {collection.count()}")
    print(f"Database location: {os.path.abspath(CHROMA_DB_PATH)}")
    print()

    if total_new_chunks > 0:
        print("You can now run knowledge_agent.py to query the knowledge base!")
    else:
        print("No new content was added. Knowledge base is up to date.")

    print()


# ==============================================================================
# SECTION 6: ENTRY POINT
# ==============================================================================

def main():
    """
    Main entry point. Reads the directory path from command-line args.
    """

    # Check if a directory path was provided as a command-line argument
    if len(sys.argv) < 2:
        # sys.argv[0] is the script name, sys.argv[1] would be the first argument
        print("Usage: python ingest.py <directory_path>")
        print("Example: python ingest.py ./sample_docs")
        print()
        print("This script will:")
        print("  1. Find all .txt files in the directory")
        print("  2. Split each file into chunks")
        print("  3. Store the chunks in ChromaDB for semantic search")
        sys.exit(1)  # Exit with error code

    # Get the directory path from the command line
    directory = sys.argv[1]  # sys.argv[1] is the first argument after the script name

    # Print header
    print()
    print("="*60)
    print("  KNOWLEDGE BASE INGESTION TOOL")
    print(f"  Target directory: {directory}")
    print(f"  Chunk size: {CHUNK_SIZE} chars, Overlap: {CHUNK_OVERLAP} chars")
    print("="*60)

    # Run the ingestion
    ingest_directory(directory)


# --- Run main() only when executed directly ---
if __name__ == "__main__":
    main()
