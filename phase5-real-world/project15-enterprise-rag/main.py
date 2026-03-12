# main.py
# Project 15: Production-Grade Enterprise RAG System
# This is a complete, production-ready AI knowledge base with authentication,
# document management, question answering, conversation history, and logging.
# Every enterprise AI search tool follows patterns like these.

# ============================================================
# IMPORTS — organized by category for clarity
# ============================================================

# Standard library imports
import os                              # File and environment variable access
import json                            # JSON serialization/deserialization
import logging                         # Python's built-in logging system
import uuid                            # Generate unique IDs for documents
from datetime import datetime, timedelta  # Time handling for JWT expiry
from typing import Optional, List      # Type hints for function signatures

# FastAPI and HTTP imports
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Pydantic for data validation
from pydantic import BaseModel         # Base class for all request/response schemas

# JWT (JSON Web Token) for authentication
# JWT is the standard way to handle auth in REST APIs
from jose import JWTError, jwt        # jwt = decode/encode tokens, JWTError = auth failures

# Password hashing for secure storage
# NEVER store plain-text passwords — always hash them
from passlib.context import CryptContext  # Handles bcrypt hashing

# ChromaDB for vector storage (our knowledge base)
import chromadb                        # Vector database for semantic search

# LangChain for AI integration
from langchain_anthropic import ChatAnthropic  # Claude AI model
from langchain_core.messages import HumanMessage, SystemMessage  # Message types

# Environment variables
from dotenv import load_dotenv         # Load .env file

# ASGI server
import uvicorn                         # Runs the FastAPI application

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
load_dotenv()  # Read ANTHROPIC_API_KEY and SECRET_KEY from .env file

# ============================================================
# LOGGING SETUP
# ============================================================
# In production, every query must be logged for:
# - Compliance (who asked what, when)
# - Debugging (what went wrong)
# - Monitoring (which documents are used most)
# - Audit trails (required by many enterprise security policies)

os.makedirs("logs", exist_ok=True)    # Create logs directory if it doesn't exist

# Configure Python's logging system
logging.basicConfig(
    level=logging.INFO,                # Log INFO level and above
    format='%(asctime)s | %(levelname)s | %(message)s',  # Log format with timestamp
    handlers=[
        # Write logs to a file
        logging.FileHandler("logs/queries.log"),  # Persistent log file
        # Also print logs to the console (helpful during development)
        logging.StreamHandler()        # Console output
    ]
)

# Create a named logger for our application
logger = logging.getLogger("enterprise-rag")  # Our app's logger instance

# ============================================================
# JWT AUTHENTICATION CONFIGURATION
# ============================================================
# JWT is like a hotel key card:
# 1. Guest checks in (user logs in) → hotel gives them a key card (JWT token)
# 2. Guest uses key card to enter their room (access protected endpoints)
# 3. Key card expires after checkout time (token expiry)
# 4. No need to check the front desk again until it expires (stateless)

# This secret key is used to sign tokens — anyone with this key can create valid tokens
# CHANGE THIS IN PRODUCTION — use a long random string stored securely
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production-use-random-256-bits")

# ALGORITHM tells JWT how to sign and verify tokens
# HS256 = HMAC with SHA-256 — the standard choice for most applications
ALGORITHM = "HS256"

# How long until the token expires — 30 minutes is a common default
# After this, the user must log in again
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================================
# PASSWORD HASHING
# ============================================================
# CryptContext handles the bcrypt hashing algorithm
# bcrypt automatically handles salting (adding random data to prevent rainbow table attacks)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 defines how to extract the token from the Authorization header
# The tokenUrl tells clients WHERE to get a token (our /auth/token endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# ============================================================
# USER DATABASE
# ============================================================
# For simplicity, we store users in a dictionary instead of a database
# In production, this would be a PostgreSQL or SQLite database
# The passwords are stored as bcrypt hashes (NEVER store plain text!)

# To generate a hash: pwd_context.hash("yourpassword")
# These hashes were pre-generated from "admin123" and "pass123"
USERS = {
    "admin": {
        "username": "admin",
        "full_name": "System Administrator",
        "email": "admin@company.com",
        "role": "admin",
        # bcrypt hash of "admin123"
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False
    },
    "user1": {
        "username": "user1",
        "full_name": "Standard User One",
        "email": "user1@company.com",
        "role": "user",
        # bcrypt hash of "pass123"
        "hashed_password": pwd_context.hash("pass123"),
        "disabled": False
    }
}

# ============================================================
# CONVERSATION HISTORY STORAGE
# ============================================================
# Stores Q&A history per user — in memory for simplicity
# In production, use Redis or PostgreSQL
user_histories = {}  # Format: {"username": [{"question": ..., "answer": ..., "sources": ..., "timestamp": ...}]}

# ============================================================
# CHROMADB SETUP
# ============================================================
# ChromaDB is our vector database — it stores document text as embeddings
# Embeddings are mathematical representations that capture semantic meaning
# When you search "revenue growth", it finds "financial performance" too (not just exact words)

# Initialize ChromaDB with persistent storage so data survives server restarts
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # Stores to disk

# Create or get our document collection
# A collection is like a table in a regular database, but for vector data
document_collection = chroma_client.get_or_create_collection(
    name="enterprise_documents",       # Name of our knowledge base
    metadata={"hnsw:space": "cosine"}  # Use cosine similarity for searching
)

# In-memory document registry
# Tracks metadata about each document (who uploaded it, when, what it contains)
document_registry = {}  # Format: {"doc_id": {"filename": ..., "uploaded_by": ..., "upload_time": ...}}

# ============================================================
# CLAUDE AI INITIALIZATION
# ============================================================
llm = ChatAnthropic(
    model="claude-opus-4-6",           # Most capable model for enterprise Q&A
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=2000                    # Allow longer answers for complex enterprise questions
)

# ============================================================
# PYDANTIC SCHEMAS
# ============================================================
# These define the exact shape of data going in and out of every endpoint

class Token(BaseModel):
    """Response schema for successful login — returns the JWT token"""
    access_token: str                  # The JWT token string
    token_type: str                    # Always "bearer" per OAuth2 standard

class TokenData(BaseModel):
    """Internal schema for data stored inside the JWT payload"""
    username: Optional[str] = None     # Username extracted from the token

class User(BaseModel):
    """Public user information (safe to return in API responses)"""
    username: str
    full_name: str
    email: str
    role: str
    disabled: bool

class QuestionRequest(BaseModel):
    """Request schema for the /ask endpoint"""
    question: str                      # The user's question
    num_results: int = 3               # How many source documents to retrieve (default 3)

class QuestionResponse(BaseModel):
    """Response schema for the /ask endpoint"""
    question: str                      # Echo back the question
    answer: str                        # Claude's answer based on retrieved documents
    sources: List[str]                 # List of source document names used
    confidence: str                    # HIGH/MEDIUM/LOW based on source quality
    timestamp: str                     # When the question was answered


# ============================================================
# AUTHENTICATION HELPER FUNCTIONS
# ============================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain text password matches the stored bcrypt hash.
    bcrypt is designed to be slow — this is intentional to prevent brute force attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)  # Returns True or False

def get_user(username: str) -> Optional[dict]:
    """
    Look up a user by username in our user dictionary.
    Returns None if the user does not exist.
    """
    return USERS.get(username)         # Dictionary lookup by key

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Validates username and password combination.
    Returns the user dict if valid, None if invalid.
    This is called during the login process.
    """
    user = get_user(username)          # Look up the user
    if not user:                       # User does not exist
        return None
    if not verify_password(password, user["hashed_password"]):  # Wrong password
        return None
    return user                        # Return user data if everything checks out

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT token containing the user data.
    The token is a string that looks like: xxxxx.yyyyy.zzzzz
    It can be decoded (but not forged) by anyone — the signature proves authenticity.
    """
    to_encode = data.copy()            # Copy the data dict — do not modify the original

    # Set the expiry time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # Custom expiry
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default 15 minutes

    to_encode.update({"exp": expire})  # Add expiry to the payload

    # Sign and encode the token using our secret key
    # jwt.encode creates the final token string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt                 # Return the token string

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency function — called automatically by FastAPI for protected endpoints.
    Extracts and validates the JWT token from the Authorization header.
    If the token is invalid or expired, raises a 401 Unauthorized error.

    How FastAPI dependencies work:
    - Add `current_user: dict = Depends(get_current_user)` to any endpoint
    - FastAPI calls this function BEFORE your endpoint code
    - If this function raises an exception, the endpoint is never reached
    - If successful, it returns the user data which your endpoint can use
    """
    # Define the error we will raise if authentication fails
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,     # 401 = not authenticated
        detail="Could not validate credentials",       # Error message
        headers={"WWW-Authenticate": "Bearer"},        # Required by OAuth2 standard
    )

    try:
        # Decode the JWT token — this verifies the signature and expiry
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the username from the payload
        username: str = payload.get("sub")  # "sub" (subject) = the username

        if username is None:           # Token is valid but has no username — reject
            raise credentials_exception

        token_data = TokenData(username=username)  # Wrap in Pydantic model

    except JWTError:                   # Token is invalid, expired, or tampered with
        raise credentials_exception

    # Look up the user in our database
    user = get_user(token_data.username)
    if user is None:                   # User no longer exists (deleted after token issued)
        raise credentials_exception
    if user.get("disabled"):           # User account has been disabled
        raise HTTPException(status_code=400, detail="Inactive user")

    return user                        # Return the full user dict for the endpoint to use


# ============================================================
# FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title="Enterprise RAG System",
    description="Production-grade AI document Q&A with JWT authentication, logging, and document management",
    version="1.0.0"
)


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    POST /auth/token
    Login endpoint. Takes username and password, returns a JWT token.
    The client must send this token in the Authorization header for all other requests.

    Request format (form data, not JSON):
    - username: admin
    - password: admin123

    Response:
    - access_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    - token_type: "bearer"
    """
    # Validate the username and password
    user = authenticate_user(form_data.username, form_data.password)

    if not user:                       # Invalid credentials
        # Log failed login attempt for security monitoring
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token with the username as the subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},     # Payload: store username as "sub"
        expires_delta=access_token_expires  # Token expires in 30 minutes
    )

    # Log successful login
    logger.info(f"Successful login: {user['username']} ({user['role']})")

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=User)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    """
    GET /auth/me
    Returns the profile of the currently logged-in user.
    Protected endpoint — requires valid JWT token.
    """
    return User(**current_user)        # Convert dict to User model


# ============================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),      # The uploaded file (required)
    current_user: dict = Depends(get_current_user)  # Auth check
):
    """
    POST /documents/upload
    Upload a .txt file and automatically ingest it into the ChromaDB vector store.
    Requires authentication.

    How it works:
    1. Read the uploaded file
    2. Split it into chunks (250 words each for manageable size)
    3. Store each chunk as a vector embedding in ChromaDB
    4. Record metadata in our document registry
    """
    # Validate file type — only accept .txt files for simplicity
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # Read the file content
    content = await file.read()        # Read bytes from the uploaded file
    text = content.decode("utf-8")     # Decode bytes to string (UTF-8 encoding)

    if not text.strip():               # Reject empty files
        raise HTTPException(status_code=400, detail="File is empty")

    # Generate a unique document ID
    doc_id = str(uuid.uuid4())[:12]    # First 12 characters of a UUID

    # CHUNK THE DOCUMENT
    # We split large documents into smaller chunks because:
    # 1. Embedding models have token limits
    # 2. Smaller chunks = more precise retrieval (find exactly the right paragraph)
    # 3. Better semantic coherence within each chunk
    words = text.split()               # Split text into individual words
    chunk_size = 250                   # Words per chunk (tune this for your use case)
    chunks = []
    chunk_ids = []
    chunk_metadatas = []

    for i in range(0, len(words), chunk_size):  # Iterate through word groups
        chunk_words = words[i:i + chunk_size]   # Get this chunk's words
        chunk_text = " ".join(chunk_words)       # Join words back into text
        chunk_id = f"{doc_id}_chunk_{i // chunk_size}"  # Unique ID for this chunk

        chunks.append(chunk_text)              # Add chunk text
        chunk_ids.append(chunk_id)             # Add chunk ID

        # Metadata helps us filter and identify chunks later
        chunk_metadatas.append({
            "doc_id": doc_id,                  # Which document this chunk belongs to
            "filename": file.filename,         # Original filename
            "uploaded_by": current_user["username"],  # Who uploaded it
            "chunk_index": i // chunk_size,    # Which chunk number this is
            "upload_time": datetime.now().isoformat()  # When it was uploaded
        })

    # ADD CHUNKS TO CHROMADB
    # ChromaDB will automatically create embeddings using its default embedding model
    document_collection.add(
        documents=chunks,              # The text content of each chunk
        ids=chunk_ids,                 # Unique IDs for each chunk
        metadatas=chunk_metadatas      # Metadata for filtering and identification
    )

    # RECORD IN DOCUMENT REGISTRY
    # The registry lets us list and delete documents by filename
    document_registry[doc_id] = {
        "doc_id": doc_id,
        "filename": file.filename,
        "uploaded_by": current_user["username"],
        "upload_time": datetime.now().isoformat(),
        "chunk_count": len(chunks),
        "word_count": len(words)
    }

    # Log the upload for audit trail
    logger.info(
        f"Document uploaded: {file.filename} | "
        f"doc_id: {doc_id} | "
        f"chunks: {len(chunks)} | "
        f"user: {current_user['username']}"
    )

    return {
        "message": "Document uploaded and ingested successfully",
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_created": len(chunks),
        "word_count": len(words)
    }


@app.get("/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """
    GET /documents
    Returns a list of all documents in the knowledge base.
    Protected endpoint — requires authentication.
    """
    if not document_registry:          # If no documents uploaded yet
        return {"documents": [], "total": 0, "message": "No documents in knowledge base"}

    return {
        "documents": list(document_registry.values()),  # Return all document metadata
        "total": len(document_registry),
        "total_chunks": document_collection.count()     # Total vector chunks in ChromaDB
    }


@app.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    DELETE /documents/{doc_id}
    Removes a document and all its chunks from the knowledge base.
    Only admin users can delete documents.
    Protected endpoint.
    """
    # Check if the user has admin role for deletion (access control)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 403 = authenticated but not authorized
            detail="Only admins can delete documents"
        )

    # Check if the document exists
    if doc_id not in document_registry:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Get the document info before deleting
    doc_info = document_registry[doc_id]

    # DELETE FROM CHROMADB — remove all chunks for this document
    # Query to find all chunks that belong to this document
    results = document_collection.get(
        where={"doc_id": doc_id}       # Filter by document ID metadata
    )

    if results and results.get("ids"):  # If we found chunks to delete
        document_collection.delete(ids=results["ids"])  # Delete all chunks

    # Remove from registry
    del document_registry[doc_id]

    # Log the deletion
    logger.info(
        f"Document deleted: {doc_info['filename']} | "
        f"doc_id: {doc_id} | "
        f"deleted by: {current_user['username']}"
    )

    return {
        "message": f"Document '{doc_info['filename']}' deleted successfully",
        "doc_id": doc_id,
        "chunks_removed": len(results.get("ids", []))
    }


# ============================================================
# Q&A ENDPOINT
# ============================================================

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user)  # Auth check
):
    """
    POST /ask
    The main Q&A endpoint. Searches the knowledge base and answers using Claude.
    This is the RAG (Retrieval Augmented Generation) core:
    1. RETRIEVE: Search ChromaDB for relevant document chunks
    2. AUGMENT: Combine the question with retrieved context
    3. GENERATE: Ask Claude to answer using only the retrieved context

    Protected endpoint — requires JWT token.
    """
    if not request.question.strip():   # Reject empty questions
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Check if there are any documents to search
    if document_collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents in knowledge base. Please upload documents first."
        )

    # STEP 1: RETRIEVE — search ChromaDB for relevant chunks
    # ChromaDB converts the question into an embedding and finds similar document embeddings
    search_results = document_collection.query(
        query_texts=[request.question],    # The question to search for
        n_results=min(request.num_results, document_collection.count()),  # Get N most relevant chunks
        include=["documents", "metadatas", "distances"]  # Include text, metadata, and relevance scores
    )

    # Extract the retrieved document chunks
    retrieved_docs = search_results.get("documents", [[]])[0]   # List of text chunks
    retrieved_metadata = search_results.get("metadatas", [[]])[0]  # List of metadata dicts
    distances = search_results.get("distances", [[]])[0]         # Lower = more relevant

    if not retrieved_docs:             # No relevant documents found
        raise HTTPException(status_code=404, detail="No relevant documents found for this question")

    # BUILD THE CONTEXT STRING from retrieved chunks
    # We format it clearly so Claude knows exactly what sources it has
    context_parts = []
    source_filenames = []              # Track which files were used

    for i, (doc, meta, dist) in enumerate(zip(retrieved_docs, retrieved_metadata, distances)):
        filename = meta.get("filename", "unknown")  # Source document name
        chunk_idx = meta.get("chunk_index", 0)      # Which part of the document
        context_parts.append(f"[Source {i+1}: {filename}, chunk {chunk_idx}]\n{doc}")
        if filename not in source_filenames:        # Deduplicate filenames
            source_filenames.append(filename)

    context = "\n\n---\n\n".join(context_parts)    # Join all sources with separators

    # STEP 2 & 3: AUGMENT + GENERATE
    # Give Claude the retrieved context and ask it to answer ONLY from that context
    # This is the key RAG instruction: "only use the provided context"
    system_prompt = """You are an enterprise knowledge assistant. Answer questions using ONLY the provided document context below.

Rules:
1. Base your answer ONLY on the provided context — do not use external knowledge
2. If the context does not contain the answer, say: "I don't have information about that in the knowledge base."
3. Always cite which source (Source 1, Source 2, etc.) you are drawing from
4. Be precise and professional — this is an enterprise system
5. If multiple sources have relevant information, synthesize them coherently"""

    # Build the human message combining the context and the question
    human_message = f"""DOCUMENT CONTEXT:
{context}

QUESTION: {request.question}

Please answer the question using only the provided context above."""

    # Call Claude with the augmented context
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    answer = response.content          # Claude's answer

    # DETERMINE CONFIDENCE LEVEL
    # Base confidence on how relevant the retrieved documents are
    # ChromaDB distances: lower = more similar (0 = perfect match, 2 = completely different)
    avg_distance = sum(distances) / len(distances) if distances else 2.0
    if avg_distance < 0.3:
        confidence = "HIGH"            # Very relevant sources found
    elif avg_distance < 0.6:
        confidence = "MEDIUM"          # Somewhat relevant sources
    else:
        confidence = "LOW"             # Sources may not directly address the question

    # STORE IN CONVERSATION HISTORY
    username = current_user["username"]
    if username not in user_histories:
        user_histories[username] = []  # Initialize history list for this user

    history_entry = {
        "question": request.question,
        "answer": answer,
        "sources": source_filenames,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }
    user_histories[username].append(history_entry)  # Add to history

    # LOG THE QUERY — this is essential for enterprise compliance
    logger.info(
        f"QUERY | user: {current_user['username']} | "
        f"question: {request.question[:100]}... | "  # Log first 100 chars of question
        f"sources: {source_filenames} | "
        f"confidence: {confidence}"
    )

    return QuestionResponse(
        question=request.question,
        answer=answer,
        sources=source_filenames,
        confidence=confidence,
        timestamp=datetime.now().isoformat()
    )


# ============================================================
# CONVERSATION HISTORY ENDPOINT
# ============================================================

@app.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    """
    GET /history
    Returns the conversation history for the currently logged-in user.
    Each user only sees their own history.
    Protected endpoint.
    """
    username = current_user["username"]
    history = user_histories.get(username, [])  # Get this user's history (or empty list)

    return {
        "username": username,
        "query_count": len(history),   # How many questions they have asked
        "history": history             # Full list of Q&A pairs
    }


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/health")
async def health_check():
    """
    GET /health
    Returns the health status of all system components.
    This endpoint is intentionally NOT protected — monitoring systems need to call it.
    """
    # Check ChromaDB status
    try:
        doc_count = document_collection.count()  # Test ChromaDB is working
        chroma_status = "healthy"
    except Exception as e:
        doc_count = 0
        chroma_status = f"error: {str(e)}"

    # Check Claude API (just verify the key is configured, don't make an API call)
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    claude_status = "configured" if api_key.startswith("sk-ant") else "not configured"

    return {
        "status": "healthy",
        "service": "Enterprise RAG System",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "chromadb": chroma_status,
            "documents_indexed": doc_count,
            "claude_api": claude_status,
            "users_active": len([u for u in USERS.values() if not u["disabled"]])
        }
    }


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("Starting Enterprise RAG System...")
    print("=" * 50)
    print("API Documentation: http://localhost:8000/docs")
    print("Default users:")
    print("  admin / admin123 (can upload, ask, delete)")
    print("  user1 / pass123  (can upload, ask)")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
