# Project 8: Customer Support Bot API

## What You Will Build

A fully functional **REST API** for a customer support chatbot. Clients (web apps, mobile apps, other services) can send messages to this API and receive AI-generated responses. The bot maintains conversation history per session, detects frustrated customers, and escalates to human agents when needed.

This is your first encounter with **web APIs** — the technology that connects virtually every app on the internet.

---

## What Is a REST API? (Plain English)

Before writing any code, let's understand what an API actually is.

**API** stands for Application Programming Interface. Forget the acronym — here's the plain English version:

An API is a **contract** between two programs. It says: "If you send me a message in this specific format, I will respond with data in this specific format."

**Analogy: A Restaurant**

- You (the client) sit at a table
- The menu describes what you can order (the API specification)
- You tell the waiter "I'll have the pasta" (you send a request)
- The kitchen prepares the food (the server processes the request)
- The waiter brings your pasta (the server sends a response)

You don't need to know how the kitchen works. You just know the menu and the format for ordering.

**REST** stands for Representational State Transfer. A REST API uses standard HTTP methods (the same protocol your browser uses to load web pages):

| HTTP Method | What It Does | Restaurant Analogy |
|-------------|-------------|-------------------|
| `GET` | Retrieve data | "Show me today's menu" |
| `POST` | Send data, create something | "I'd like to order pasta" |
| `PUT` | Update something completely | "Actually, change my whole order" |
| `PATCH` | Update something partially | "Add extra cheese to the pasta" |
| `DELETE` | Remove something | "Cancel my order" |

Every endpoint in this API uses one of these methods. That's REST.

---

## What Is FastAPI?

FastAPI is a modern Python web framework for building APIs. You write Python functions and it automatically handles:

- Accepting HTTP requests
- Parsing JSON bodies
- Validating data types
- Generating interactive documentation
- Returning JSON responses

Compare the two approaches:

**Without FastAPI (manual approach — painful):**
```python
from http.server import BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)
        # Manual validation, manual error handling, manual response encoding...
```

**With FastAPI (what we use — clean):**
```python
@app.post("/chat")
async def chat(request: ChatRequest):
    # FastAPI handles all the HTTP plumbing
    # You just write business logic
    return ChatResponse(response="Hello!")
```

FastAPI is also extremely fast (hence the name) — it's one of the fastest Python web frameworks available.

---

## What Is a Session?

When multiple customers talk to a support bot simultaneously, you need a way to keep their conversations separate. That's what a **session** is.

**Analogy: Phone Support Lines**

When you call a support hotline:
- The call center has hundreds of simultaneous conversations
- Your conversation is tracked by your call ID
- The support rep sees only YOUR conversation history
- Other callers' conversations don't appear in your window

A **session_id** is the equivalent of that call ID. It's a unique string (UUID) that identifies one conversation.

In our system:
```python
sessions = {
    "a3f8c2d1-...": [
        {"role": "user", "content": "My account is broken"},
        {"role": "assistant", "content": "I can help with that!"},
        ...
    ],
    "b9e7f4c2-...": [
        {"role": "user", "content": "What is your refund policy?"},
        ...
    ]
}
```

Each session_id maps to its own independent conversation history. Session A never sees Session B's messages.

---

## Why Stateful Matters for Support Bots

A **stateless** system treats every request as if it's the first interaction. A **stateful** system remembers previous interactions.

**Stateless support bot (terrible experience):**
```
User: My account is broken.
Bot: I can help with that! What's the issue?
User: I can't log in.
Bot: What's your account issue? (forgot the previous message!)
User: I just told you — I can't log in!
Bot: I'm not sure what you mean. Please describe your problem.
```

**Stateful support bot (our approach):**
```
User: My account is broken.
Bot: I'm sorry to hear that! What's happening exactly?
User: I can't log in.
Bot: Got it — login issues are common. Let's try resetting your password. Can you
     confirm the email address on your account?
User: It's user@example.com
Bot: I'll send a reset link to user@example.com. That should resolve the login issue.
```

In the stateful version, every message from Claude includes the full conversation history. Claude says "Got it" because it remembers the user said "My account is broken" in the previous turn.

This is implemented by passing the growing `history` list to Claude's API with every message.

---

## Escalation Logic

Real customer support systems have escalation paths — ways for customers to request human assistance when the AI can't solve their problem.

Our bot checks for escalation in two layers:

**Layer 1: Keyword detection (fast)**
```python
ESCALATION_KEYWORDS = ["escalate", "human", "manager", "supervisor", "speak to someone", "real person"]
```

If any of these words appear in the message, escalation is triggered immediately.

**Layer 2: Claude-powered detection (smart)**

Claude also implicitly manages escalation in its instructions — it knows when to suggest escalation after 1-2 failed attempts to solve the problem.

**When escalation happens:**

The API response includes `"escalated": true` in the JSON:
```json
{
  "response": "I understand you'd like to speak with a human agent. I'm connecting you now. Your case number is CASE-A3F8C2D1. Estimated wait time is 3-5 minutes.",
  "session_id": "a3f8c2d1-...",
  "escalated": true,
  "message_count": 6
}
```

The calling application (a website, mobile app, etc.) reads `escalated: true` and can then:
- Create a support ticket in a ticketing system
- Send a notification to the on-call human agent
- Transfer the chat window to a different interface
- Log the escalation for quality review

---

## API Endpoints Reference

### POST /chat
Send a message, get a response.

**Request body:**
```json
{
  "message": "I can't log into my account",
  "session_id": "optional-existing-session-id"
}
```

**Response body:**
```json
{
  "response": "I'm sorry to hear you're having trouble logging in...",
  "session_id": "a3f8c2d1-4e5f-6789-...",
  "escalated": false,
  "message_count": 2
}
```

If you omit `session_id`, a new session is created. Save the returned `session_id` to continue the same conversation.

---

### GET /conversations/{session_id}
Retrieve the full conversation history for a session.

**Example URL:** `GET /conversations/a3f8c2d1-4e5f-6789-...`

**Response body:**
```json
{
  "session_id": "a3f8c2d1-4e5f-6789-...",
  "messages": [
    {"role": "user", "content": "I can't log into my account"},
    {"role": "assistant", "content": "I'm sorry to hear that..."}
  ],
  "message_count": 2
}
```

---

### DELETE /conversations/{session_id}
Delete a session and all its history.

**Response body:**
```json
{
  "message": "Session 'a3f8c2d1-...' has been deleted.",
  "status": "deleted"
}
```

---

### GET /health
Check if the API is running.

**Response body:**
```json
{
  "status": "ok",
  "model": "claude-opus-4-6",
  "active_sessions": 3
}
```

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

### Step 3: Set up API key
```bash
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-your-real-key
```

### Step 4: Start the server
```bash
uvicorn support_bot:app --reload
```

You'll see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.

============================================================
  TECHCORP CUSTOMER SUPPORT BOT
  Model: claude-opus-4-6
  API Docs: http://localhost:8000/docs
  Health:   http://localhost:8000/health
============================================================

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The `--reload` flag makes the server automatically restart when you save changes to `support_bot.py`. Great for development.

---

## How to Test the API

### Method 1: Run the test client (easiest)
In a **second terminal** (keep the server running in the first):
```bash
python run_client.py
```

This runs all four test scenarios automatically and prints the results.

### Method 2: Interactive API Documentation

FastAPI automatically generates interactive documentation. Open your browser to:

**http://localhost:8000/docs**

You'll see a Swagger UI with all endpoints listed. You can click any endpoint and click "Try it out" to send real requests from your browser. No code required.

### Method 3: curl (command line)

**Check health:**
```bash
curl http://localhost:8000/health
```

**Send a chat message:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I need help with my account"}'
```

**Continue the conversation (replace SESSION_ID with the ID from the previous response):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I cant log in", "session_id": "SESSION_ID"}'
```

**Get conversation history:**
```bash
curl http://localhost:8000/conversations/SESSION_ID
```

**Trigger escalation:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to speak to a human manager", "session_id": "SESSION_ID"}'
```

**Delete a session:**
```bash
curl -X DELETE http://localhost:8000/conversations/SESSION_ID
```

### Method 4: Python requests (for your own scripts)
```python
import requests

# Start a new conversation
response = requests.post("http://localhost:8000/chat", json={
    "message": "My billing is incorrect"
})
data = response.json()
session_id = data["session_id"]

# Continue the conversation
response2 = requests.post("http://localhost:8000/chat", json={
    "message": "I was charged twice this month",
    "session_id": session_id
})
print(response2.json()["response"])
```

---

## Understanding the Code Structure

```
support_bot.py
│
├── Constants                    — MODEL_NAME, escalation keywords, system prompt
│
├── FastAPI app setup            — Creates the app, adds CORS middleware
├── Session storage (dict)       — In-memory session store
│
├── Pydantic Models              — ChatRequest, ChatResponse, etc.
│   (Data validation shapes)
│
├── Helper functions
│   ├── check_for_escalation()   — Keyword-based escalation detection
│   ├── detect_frustration_simple()    — Quick keyword check
│   ├── detect_frustration_with_claude() — Claude-powered sentiment analysis
│   └── get_or_create_session()  — Session management
│
├── Endpoints
│   ├── GET  /health             — Health check
│   ├── POST /chat               — Main chat endpoint
│   ├── GET  /conversations/{id} — Get history
│   └── DELETE /conversations/{id} — Delete session
│
└── Startup event               — Runs on server start, checks config
```

---

## What Is CORS?

CORS (Cross-Origin Resource Sharing) is a browser security feature.

**The problem:** By default, browsers block JavaScript running on `www.yourwebsite.com` from calling an API at `api.othersite.com`. This prevents malicious websites from making requests on your behalf.

**The solution:** The API server tells the browser "it's OK, I trust requests from these origins." Our API uses `allow_origins=["*"]` which means "trust everyone." This is fine for development but should be restricted in production (e.g., `allow_origins=["https://yourdomain.com"]`).

Without the CORS middleware, a React or Vue.js web app would fail to call this API from a browser, even if both are running locally.

---

## What Is Pydantic?

Pydantic is a data validation library. We define models like this:

```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
```

When a request comes in with:
```json
{"message": 12345}  # number instead of string!
```

Pydantic automatically catches the type error and FastAPI returns:
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "str type expected",
      "type": "type_error.str"
    }
  ]
}
```

Without Pydantic, you'd need to manually validate every field. With Pydantic, incorrect data never reaches your business logic.

---

## Frustration Detection: Two Approaches

The app uses two frustration detection strategies:

**1. Keyword matching (fast, cheap)**
Simple string check: does the message contain words like "frustrated", "ridiculous", "broken"?

- Pros: Instant, no API cost
- Cons: Misses "I've been waiting for three hours" (frustrated but no keywords)

**2. Claude classification (smart, costs tokens)**
Sends the message to Claude with the prompt: "Is the customer frustrated? Answer yes/no."

- Pros: Catches subtle frustration, understands context
- Cons: Costs one extra API call per turn

The app uses keyword detection first. If no keywords found and the message is long enough to analyze (>20 characters), it uses Claude. This balances cost and accuracy.

When frustration is detected, a sentence is appended to Claude's system prompt:
```
IMPORTANT: This customer seems frustrated. Start your response by acknowledging their frustration with genuine empathy before moving to solutions.
```

This single instruction dramatically changes the tone of Claude's response.

---

## Limitations of This Implementation

This is a learning project. In a production system, you'd address these limitations:

1. **In-memory sessions** are lost when the server restarts. Production: use Redis or PostgreSQL for session storage.

2. **No authentication** — anyone who knows a session_id can read its history. Production: add API keys or JWT tokens.

3. **No rate limiting** — a single client could send thousands of requests and run up your Claude bill. Production: add rate limiting per IP or per API key.

4. **Single process** — this app runs in one Python process. Production: run multiple workers with a load balancer.

5. **No persistent logging** — conversations are not logged anywhere. Production: log everything to a database for quality analysis.

---

## What's Next

Project 9 builds a **knowledge base agent** — you'll use ChromaDB to let Claude search through actual company documents. Combined with the API architecture from this project, you'll have the foundation for a complete enterprise AI search system.
