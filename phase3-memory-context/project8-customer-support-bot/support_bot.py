# support_bot.py
# A customer support chatbot API built with FastAPI and Claude.
# This project introduces REST APIs, sessions, and stateful conversations.
# Run this server with: uvicorn support_bot:app --reload

# --- Standard library imports ---
import os           # For reading environment variables
import uuid         # For generating unique session IDs
from typing import Optional  # For type hints that allow None values

# --- Third-party imports ---
from fastapi import FastAPI, HTTPException   # FastAPI framework for building APIs
from fastapi.middleware.cors import CORSMiddleware  # Allows web browsers to call this API
from pydantic import BaseModel               # Data validation — ensures correct data types
from dotenv import load_dotenv               # Reads the .env file for API keys
import anthropic                             # Anthropic Python SDK for calling Claude

# --- Load environment variables ---
# This reads ANTHROPIC_API_KEY from the .env file into os.environ
load_dotenv()

# --- Constants ---
MODEL_NAME = "claude-opus-4-6"    # The Claude model we'll use for all responses
MAX_TOKENS = 1024                  # Maximum tokens Claude can return per response
MAX_HISTORY = 20                   # Maximum messages to keep per session (10 exchanges)

# --- Keywords that trigger escalation to a human agent ---
# If the user's message contains any of these words, we escalate
ESCALATION_KEYWORDS = ["escalate", "human", "manager", "supervisor", "speak to someone", "real person"]

# --- Frustration keywords for empathy detection ---
# These signal frustration, but we also use Claude to detect it more subtly
FRUSTRATION_KEYWORDS = ["frustrated", "angry", "useless", "terrible", "awful", "ridiculous", "broken", "hate"]

# --- The company name for TechCorp ---
COMPANY_NAME = "TechCorp"

# --- System prompt for the customer support agent ---
# This defines Claude's persona, knowledge, and behavior rules
SUPPORT_SYSTEM_PROMPT = f"""You are a helpful and empathetic customer support agent for {COMPANY_NAME}, a technology company that sells software tools, cloud services, and hardware devices.

Your personality:
- Warm, professional, and patient
- You listen carefully and address the customer's actual concern
- You never make the customer feel stupid
- You use simple, clear language without jargon

Your knowledge:
- {COMPANY_NAME} products: TechCorp Suite (productivity software), TechCorp Cloud (file storage), TechCorp X1 Device (hardware)
- Common issues: login problems, billing questions, technical troubleshooting, feature requests
- Company policy: 30-day refund policy, 24/7 support for premium customers, free tier has email support only

Your rules:
1. Always greet new customers warmly in your first response
2. Try to solve issues in 1-2 messages before suggesting escalation
3. If a customer is frustrated, acknowledge their frustration first before solving the problem
4. Be specific — don't give vague answers like "have you tried restarting?"
5. If you don't know the answer, say so honestly and offer to escalate

Remember: the customer's time is valuable. Be concise but thorough."""


# ==============================================================================
# SECTION 1: FASTAPI APPLICATION SETUP
# FastAPI is a modern Python web framework for building APIs.
# An API is a way for programs to communicate with each other over the internet.
# ==============================================================================

# Create the FastAPI application instance
# This is the main object that handles all HTTP requests
app = FastAPI(
    title="TechCorp Customer Support Bot",           # API title (shown in docs)
    description="AI-powered customer support using Claude claude-opus-4-6",  # Description
    version="1.0.0"                                  # API version
)

# Add CORS (Cross-Origin Resource Sharing) middleware
# This allows web browsers (like Chrome) to make requests to this API
# Without CORS, browsers would block requests from different origins (security feature)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow requests from ANY website (fine for development)
    allow_credentials=True,    # Allow cookies/auth headers to be sent
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],       # Allow all headers in requests
)

# --- Initialize the Anthropic client ---
# We create this once at startup and reuse it for all requests
# Reading from environment variable (set in .env file)
api_key = os.getenv("ANTHROPIC_API_KEY")  # Get the API key from environment

# Warn if API key is missing, but don't crash yet (some endpoints don't need it)
if not api_key:
    print("WARNING: ANTHROPIC_API_KEY not found. Chat endpoint will fail.")
    print("Create a .env file with: ANTHROPIC_API_KEY=sk-ant-your-key-here")

# Create the Anthropic client — used to call the Claude API
anthropic_client = anthropic.Anthropic(api_key=api_key) if api_key else None

# --- Session storage ---
# In a real app, this would be a database (Redis, PostgreSQL, etc.)
# For learning purposes, we use a simple Python dictionary
# Key: session_id (string), Value: list of message dicts
# IMPORTANT: This is IN-MEMORY storage — data is lost when the server restarts
sessions: dict[str, list] = {}  # Empty dict to start — sessions are created on first message


# ==============================================================================
# SECTION 2: PYDANTIC MODELS (DATA VALIDATION)
# Pydantic models define the shape of our request/response data.
# FastAPI uses them to automatically validate incoming data.
# If a request doesn't match the model, FastAPI returns a helpful error.
# ==============================================================================

class ChatRequest(BaseModel):
    """
    Model for incoming chat requests (POST /chat).
    The user sends this JSON body when sending a message.
    """
    message: str               # The user's message text (required)
    session_id: Optional[str] = None  # Optional: provide to continue an existing session


class ChatResponse(BaseModel):
    """
    Model for chat responses.
    The server sends this JSON body back to the client.
    """
    response: str              # Claude's reply text
    session_id: str            # The session ID (new or existing)
    escalated: bool = False    # True if the conversation was escalated to a human
    message_count: int = 0     # How many messages are in this session


class ConversationHistory(BaseModel):
    """
    Model for returning a session's full conversation history.
    Used by GET /conversations/{session_id}
    """
    session_id: str            # The ID of this session
    messages: list             # The list of message dicts [{role, content}, ...]
    message_count: int         # Total number of messages in the session


class HealthResponse(BaseModel):
    """
    Model for the health check endpoint.
    Used by monitoring systems to check if the API is running.
    """
    status: str                # "ok" if everything is working
    model: str                 # Which Claude model is configured
    active_sessions: int       # How many sessions are currently in memory


# ==============================================================================
# SECTION 3: HELPER FUNCTIONS
# These functions handle escalation detection, sentiment detection, and session management.
# ==============================================================================

def check_for_escalation(message: str) -> bool:
    """
    Checks if the user's message contains escalation keywords.
    Returns True if the user wants to speak to a human.

    Args:
        message: The user's message text

    Returns:
        True if escalation keywords are found, False otherwise
    """
    # Convert to lowercase so "Escalate" matches "escalate"
    message_lower = message.lower()

    # Check if any escalation keyword appears in the message
    for keyword in ESCALATION_KEYWORDS:
        if keyword in message_lower:  # String contains the keyword
            return True  # Found an escalation keyword — return True immediately

    return False  # No escalation keywords found


def detect_frustration_simple(message: str) -> bool:
    """
    Simple keyword-based frustration detection.
    Returns True if the message contains frustration keywords.
    This is a fast check before we use Claude for more nuanced detection.

    Args:
        message: The user's message text

    Returns:
        True if frustration keywords are found, False otherwise
    """
    # Convert to lowercase for case-insensitive matching
    message_lower = message.lower()

    # Check each frustration keyword
    for keyword in FRUSTRATION_KEYWORDS:
        if keyword in message_lower:  # If keyword found in message
            return True  # Customer seems frustrated

    return False  # No obvious frustration keywords


def detect_frustration_with_claude(message: str, conversation_history: list) -> bool:
    """
    Uses Claude to detect frustration in the customer's message.
    More nuanced than keyword matching — catches subtle frustration like
    "I've been waiting for three hours and nothing is working" (no keywords, but frustrated).

    Args:
        message: The current user message
        conversation_history: Recent conversation context

    Returns:
        True if Claude detects frustration, False otherwise
    """
    # Skip Claude detection if no API client is available
    if not anthropic_client:
        return False  # Can't detect without API, return False

    # Build a short summary of recent context (last 4 messages = 2 exchanges)
    recent_context = ""
    if conversation_history:
        # Take the last 4 messages for context
        recent_msgs = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history
        # Format them as "Role: message" lines
        recent_context = "\n".join(f"{m['role'].title()}: {m['content']}" for m in recent_msgs)

    # Build the frustration detection prompt
    frustration_prompt = f"""Is the customer frustrated in this message? Answer with ONLY "yes" or "no".

Recent conversation context:
{recent_context}

Current customer message: {message}

Answer (yes/no):"""

    try:
        # Call Claude for a quick yes/no classification
        response = anthropic_client.messages.create(
            model=MODEL_NAME,    # Use the same model
            max_tokens=10,       # We only need "yes" or "no" — 10 tokens is plenty
            messages=[
                {
                    "role": "user",          # Sending as user message
                    "content": frustration_prompt  # The classification prompt
                }
            ]
        )

        # Extract Claude's answer and normalize it
        answer = response.content[0].text.strip().lower()

        # Return True if Claude said "yes", False otherwise
        return answer.startswith("yes")  # .startswith() handles "yes." "yes," etc.

    except Exception:
        # If Claude call fails for any reason, default to no frustration detected
        return False  # Safe fallback — don't break the main chat because of this


def get_or_create_session(session_id: Optional[str]) -> tuple[str, list]:
    """
    Gets an existing session or creates a new one.
    A session is a unique conversation identified by a session_id.

    Args:
        session_id: Optional existing session ID (None if starting new conversation)

    Returns:
        Tuple of (session_id, message_history)
    """
    # If no session_id provided, or the session doesn't exist, create a new one
    if not session_id or session_id not in sessions:
        # Generate a new unique session ID using UUID4
        new_session_id = str(uuid.uuid4())  # e.g., "a3f8c2d1-4e5f-..."
        sessions[new_session_id] = []       # Initialize with empty message list
        return new_session_id, []           # Return new ID and empty history

    # Session exists — return the existing session ID and its message history
    return session_id, sessions[session_id]


def trim_session_history(history: list) -> list:
    """
    Keeps session history from growing too large.
    Trims to MAX_HISTORY messages (keeping the most recent ones).

    Args:
        history: The full message history list

    Returns:
        Trimmed history (at most MAX_HISTORY messages)
    """
    # If history is within limit, return as-is
    if len(history) <= MAX_HISTORY:
        return history  # No trimming needed

    # Keep only the last MAX_HISTORY messages
    # This slides a window forward as the conversation grows
    return history[-MAX_HISTORY:]  # Python negative slicing: last N items


# ==============================================================================
# SECTION 4: API ENDPOINTS
# These are the URLs clients can call. Each endpoint has:
# - An HTTP method (GET, POST, DELETE)
# - A path (the URL, like /chat or /health)
# - A function that runs when the endpoint is called
# ==============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    GET /health — Health check endpoint.
    Returns the status of the API.
    Used by monitoring systems (like AWS health checks) to verify the service is up.
    Returns 200 OK if everything is working.
    """
    return HealthResponse(
        status="ok",                         # Everything is working
        model=MODEL_NAME,                    # Which model is configured
        active_sessions=len(sessions)        # How many sessions are in memory
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST /chat — The main chat endpoint.
    Accepts a message and optional session_id, returns Claude's response.

    How it works:
    1. Get or create a session (conversation history)
    2. Check for escalation keywords
    3. Detect if the customer is frustrated
    4. Send the message + history to Claude
    5. Store the exchange in session history
    6. Return the response with metadata

    Request body: {"message": "My account is broken", "session_id": "optional-uuid"}
    Response body: {"response": "I'm sorry to hear that...", "session_id": "uuid", "escalated": false}
    """

    # Check that the Anthropic client is available
    if not anthropic_client:
        # Return HTTP 500 (Internal Server Error) if API key is missing
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not configured. Please set it in your .env file."
        )

    # Validate that the message is not empty
    if not request.message.strip():
        # Return HTTP 400 (Bad Request) if message is empty
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # STEP 1: Get or create the session for this conversation
    session_id, history = get_or_create_session(request.session_id)

    # STEP 2: Check if the user wants to escalate to a human
    is_escalated = check_for_escalation(request.message)

    # STEP 3: Detect if the customer is frustrated (to adjust response tone)
    # First try the fast keyword check
    is_frustrated = detect_frustration_simple(request.message)

    # If keywords didn't catch frustration, use Claude for more subtle detection
    # (only if the message is long enough to warrant it)
    if not is_frustrated and len(request.message) > 20:
        is_frustrated = detect_frustration_with_claude(request.message, history)

    # STEP 4: Build the system prompt
    # Start with the base support system prompt
    system = SUPPORT_SYSTEM_PROMPT

    # If customer is frustrated, add empathy instructions
    if is_frustrated:
        system += "\n\nIMPORTANT: This customer seems frustrated. Start your response by acknowledging their frustration with genuine empathy before moving to solutions. Use phrases like 'I completely understand how frustrating that must be' or 'I'm really sorry you're experiencing this.'"

    # STEP 5: Handle escalation — special response if they want a human
    if is_escalated:
        # Generate an escalation response using Claude (more natural than hardcoded text)
        escalation_prompt = f"""The customer has requested to speak with a human agent. Generate a warm, empathetic response that:
1. Acknowledges their request to speak with a human
2. Assures them a human agent will be with them shortly
3. Provides a realistic estimated wait time (e.g., 3-5 minutes during business hours)
4. Gives them a case number for reference (use format: CASE-{session_id[:8].upper()})
5. Keeps it brief (2-3 sentences)

Customer's message: {request.message}"""

        # Add the user's escalation message to history temporarily for context
        temp_history = history + [{"role": "user", "content": request.message}]

        # Call Claude for the escalation response
        escalation_response = anthropic_client.messages.create(
            model=MODEL_NAME,              # Claude model
            max_tokens=256,                # Short response for escalation
            system=SUPPORT_SYSTEM_PROMPT,  # Keep the persona consistent
            messages=temp_history + [       # Add the escalation prompt
                {"role": "user", "content": escalation_prompt}
            ]
        )

        # Get the escalation response text
        bot_reply = escalation_response.content[0].text

        # Add this exchange to session history
        history.append({"role": "user", "content": request.message})      # User's message
        history.append({"role": "assistant", "content": bot_reply})        # Bot's reply

        # Trim history to avoid it growing too large
        history = trim_session_history(history)

        # Save the updated history back to our sessions store
        sessions[session_id] = history

        # Return the escalation response
        return ChatResponse(
            response=bot_reply,              # The escalation message
            session_id=session_id,           # The session ID
            escalated=True,                  # Flag: escalated = True!
            message_count=len(history)       # Total messages in session
        )

    # STEP 6: Normal (non-escalation) chat flow
    # Add the user's current message to history for Claude's context
    history.append({"role": "user", "content": request.message})  # Add user message

    # Call Claude with the full conversation history
    # Claude sees all previous messages in this session, making it stateful
    response = anthropic_client.messages.create(
        model=MODEL_NAME,         # claude-opus-4-6
        max_tokens=MAX_TOKENS,    # Max response length
        system=system,            # System prompt (with optional frustration instructions)
        messages=history          # Full conversation history (stateful!)
    )

    # Extract Claude's response text
    bot_reply = response.content[0].text

    # Add Claude's reply to history
    history.append({"role": "assistant", "content": bot_reply})  # Add bot reply

    # Trim history to prevent it from growing too large
    history = trim_session_history(history)

    # Save the updated history back to sessions storage
    sessions[session_id] = history

    # Return the response with all metadata
    return ChatResponse(
        response=bot_reply,           # Claude's reply text
        session_id=session_id,        # The session ID (for client to track)
        escalated=False,              # Not escalated (normal conversation)
        message_count=len(history)    # How many messages in this session
    )


@app.get("/conversations/{session_id}", response_model=ConversationHistory)
async def get_conversation(session_id: str):
    """
    GET /conversations/{session_id} — Get full conversation history for a session.
    The {session_id} in the URL is a path parameter — it's part of the URL.
    Example: GET /conversations/a3f8c2d1-4e5f-...

    Returns:
        The full conversation history for the session
    """

    # Check if the session exists
    if session_id not in sessions:
        # Return HTTP 404 (Not Found) if the session doesn't exist
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. It may have expired or never existed."
        )

    # Get the message history for this session
    history = sessions[session_id]

    # Return the conversation history
    return ConversationHistory(
        session_id=session_id,        # Echo back the session ID
        messages=history,             # The full list of message dicts
        message_count=len(history)    # How many messages total
    )


@app.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str):
    """
    DELETE /conversations/{session_id} — Deletes a session and its history.
    Used when a conversation is complete and we want to free up memory.
    Also useful for privacy (customer can request their data be deleted).

    Returns:
        A confirmation message
    """

    # Check if the session exists
    if session_id not in sessions:
        # Return HTTP 404 if the session doesn't exist
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found."
        )

    # Delete the session from our in-memory storage
    del sessions[session_id]  # Python dict deletion

    # Return a success message (no Pydantic model needed for simple responses)
    return {
        "message": f"Session '{session_id}' has been deleted.",  # Confirmation
        "status": "deleted"                                        # Machine-readable status
    }


# ==============================================================================
# SECTION 5: STARTUP EVENT
# Code that runs when the server starts up.
# Good place to validate configuration and log important info.
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the FastAPI server starts.
    Checks configuration and prints startup information.
    """
    # Print startup banner
    print("\n" + "="*60)
    print("  TECHCORP CUSTOMER SUPPORT BOT")
    print(f"  Model: {MODEL_NAME}")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  Health:   http://localhost:8000/health")
    print("="*60)

    # Warn if API key is missing
    if not api_key:
        print("\nWARNING: ANTHROPIC_API_KEY is not set!")
        print("The /chat endpoint will return errors until you set it.")
    else:
        # Show a truncated version of the API key (for security)
        print(f"\nAPI Key: {api_key[:10]}...{api_key[-4:]} (truncated for security)")

    print()  # Blank line


# ==============================================================================
# SECTION 6: MAIN ENTRY POINT (for running directly)
# You can run this file directly with: python support_bot.py
# Or use uvicorn directly: uvicorn support_bot:app --reload
# ==============================================================================

if __name__ == "__main__":
    import uvicorn  # uvicorn is the ASGI server that runs FastAPI apps

    # Run the FastAPI app on localhost port 8000
    # reload=True means the server automatically restarts when you save changes
    uvicorn.run(
        "support_bot:app",  # Module:app pattern (filename:variable)
        host="0.0.0.0",     # Listen on all network interfaces
        port=8000,          # Port number
        reload=True         # Auto-reload on code changes (great for development)
    )
