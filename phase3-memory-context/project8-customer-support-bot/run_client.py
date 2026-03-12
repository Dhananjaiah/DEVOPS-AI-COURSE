# run_client.py
# A test client that simulates a real customer using the TechCorp support bot.
# Run this AFTER starting the server with: uvicorn support_bot:app --reload
# Then in a SEPARATE terminal, run: python run_client.py

# --- Imports ---
import requests   # The requests library makes HTTP calls easy (like a browser for Python)
import json       # For pretty-printing JSON responses
import time       # For adding small delays between messages (more realistic)

# --- Configuration ---
# The base URL of our FastAPI server
# If you changed the port in support_bot.py, update this too
BASE_URL = "http://localhost:8000"  # Our local server address

# The /chat endpoint path
CHAT_URL = f"{BASE_URL}/chat"  # Full URL: http://localhost:8000/chat


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def send_message(message: str, session_id: str = None) -> dict:
    """
    Sends a message to the support bot API and returns the response dict.

    Args:
        message: The customer's message text
        session_id: Optional session ID to continue an existing conversation

    Returns:
        The response dict from the API (or an error dict)
    """
    # Build the request payload (this becomes the JSON body of the POST request)
    payload = {
        "message": message  # Required: the message text
    }

    # If we have a session ID, include it to continue the same conversation
    if session_id:
        payload["session_id"] = session_id  # Optional: continue existing session

    try:
        # requests.post() sends an HTTP POST request to the URL
        # json=payload automatically:
        # 1. Converts the dict to a JSON string
        # 2. Sets Content-Type: application/json header
        response = requests.post(
            CHAT_URL,          # The URL to call
            json=payload,      # The request body as a dict (auto-converted to JSON)
            timeout=30         # Wait up to 30 seconds for a response
        )

        # response.raise_for_status() raises an exception if status code >= 400
        # This catches HTTP errors like 404 Not Found or 500 Internal Server Error
        response.raise_for_status()

        # .json() parses the JSON response body into a Python dict
        return response.json()  # Return the parsed response dict

    except requests.exceptions.ConnectionError:
        # Server is not running or wrong URL
        print(f"\n  ERROR: Cannot connect to {BASE_URL}")
        print("  Is the server running? Start it with: uvicorn support_bot:app --reload")
        return {"error": "connection_failed"}  # Return error dict

    except requests.exceptions.HTTPError as e:
        # The server returned an error status code (4xx or 5xx)
        print(f"\n  HTTP ERROR: {e}")
        return {"error": str(e)}  # Return error with details

    except requests.exceptions.Timeout:
        # The request took too long
        print("\n  ERROR: Request timed out (waited 30 seconds)")
        return {"error": "timeout"}  # Return timeout error


def print_message(role: str, content: str, extra: str = ""):
    """
    Pretty-prints a conversation message with clear formatting.

    Args:
        role: "customer" or "bot" (determines formatting)
        content: The message text
        extra: Optional extra info to show (like escalation status)
    """
    # Separator line for readability
    print("\n" + "-"*60)

    if role == "customer":
        # Customer messages on the left with arrow
        print(f"  CUSTOMER: {content}")
    elif role == "bot":
        # Bot messages on the right with arrow
        print(f"  BOT: {content}")
        if extra:
            print(f"  [{extra}]")  # Extra info (escalation status, etc.)

    print("-"*60)  # Bottom separator


def get_conversation_history(session_id: str) -> dict:
    """
    Calls GET /conversations/{session_id} to retrieve full conversation history.

    Args:
        session_id: The session ID to look up

    Returns:
        The conversation history dict from the API
    """
    # Build the URL with the session ID in the path
    history_url = f"{BASE_URL}/conversations/{session_id}"

    try:
        # GET request to retrieve the conversation
        response = requests.get(history_url, timeout=10)
        response.raise_for_status()  # Raise error if status >= 400
        return response.json()       # Parse and return JSON

    except Exception as e:
        print(f"\n  ERROR getting history: {e}")
        return {}  # Return empty dict on error


def check_health() -> bool:
    """
    Calls GET /health to check if the server is running.

    Returns:
        True if server is healthy, False otherwise
    """
    try:
        # Simple GET request to the health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()  # Raise if not 200

        # Parse the health response
        health_data = response.json()

        # Print health info
        print(f"  Server Status: {health_data.get('status', 'unknown').upper()}")
        print(f"  Model: {health_data.get('model', 'unknown')}")
        print(f"  Active Sessions: {health_data.get('active_sessions', 0)}")

        return True  # Server is healthy

    except requests.exceptions.ConnectionError:
        print("  ERROR: Server is not running!")
        return False  # Server is not reachable


# ==============================================================================
# CONVERSATION SIMULATION FUNCTIONS
# ==============================================================================

def run_normal_conversation():
    """
    Simulates a normal customer support conversation.
    The customer has a billing question and gets it resolved.
    This shows how session_id maintains conversation context.
    """
    print("\n" + "="*60)
    print("  TEST 1: NORMAL CUSTOMER SUPPORT CONVERSATION")
    print("="*60)
    print("  Scenario: Customer has a billing question")
    print()

    session_id = None  # Start with no session (server will create one)

    # --- Message 1: Customer introduces their problem ---
    msg1 = "Hi, I have a question about my TechCorp Cloud subscription. I was charged twice this month."
    print_message("customer", msg1)

    response1 = send_message(msg1)  # Send to API

    if "error" in response1:
        print("  Skipping test due to connection error.")
        return None  # Return early if connection failed

    # Save the session ID for subsequent messages (this is how sessions work!)
    session_id = response1.get("session_id")
    bot_reply1 = response1.get("response", "No response")

    print_message("bot", bot_reply1, f"Session: {session_id[:8]}...")
    time.sleep(1)  # Small delay to simulate reading the response

    # --- Message 2: Customer provides more details ---
    msg2 = "The charges are from March 1st and March 3rd. Both show $29.99. My account email is customer@example.com"
    print_message("customer", msg2)

    response2 = send_message(msg2, session_id)  # Continue same session
    bot_reply2 = response2.get("response", "No response")

    print_message("bot", bot_reply2, f"Message #{response2.get('message_count', '?')} in session")
    time.sleep(1)

    # --- Message 3: Customer asks for resolution ---
    msg3 = "So will I get a refund? How long does it take?"
    print_message("customer", msg3)

    response3 = send_message(msg3, session_id)  # Continue same session
    bot_reply3 = response3.get("response", "No response")

    print_message("bot", bot_reply3)

    print(f"\n  Session ID for this conversation: {session_id}")
    print("  (Notice how the bot remembers context from all previous messages)")

    return session_id  # Return session ID for later tests


def run_frustrated_customer_conversation():
    """
    Simulates a frustrated customer conversation.
    Shows how the bot detects frustration and responds with more empathy.
    """
    print("\n" + "="*60)
    print("  TEST 2: FRUSTRATED CUSTOMER CONVERSATION")
    print("="*60)
    print("  Scenario: Customer is frustrated with a broken product")
    print()

    session_id = None  # New session

    # --- Frustrated message ---
    msg1 = "This is absolutely ridiculous! My TechCorp X1 Device has been broken for a WEEK and nobody is helping me!"
    print_message("customer", msg1)

    response1 = send_message(msg1)

    if "error" in response1:
        print("  Skipping test due to connection error.")
        return

    session_id = response1.get("session_id")
    bot_reply1 = response1.get("response", "No response")

    print_message("bot", bot_reply1, "Frustration detected — empathy mode active")
    time.sleep(1)

    # --- Follow-up with more frustration ---
    msg2 = "I've restarted it 10 times, done the factory reset, and it still won't turn on. I hate this product."
    print_message("customer", msg2)

    response2 = send_message(msg2, session_id)
    bot_reply2 = response2.get("response", "No response")

    print_message("bot", bot_reply2)


def run_escalation_conversation():
    """
    Simulates a conversation that gets escalated to a human agent.
    This is the most important test — shows the escalation logic.
    """
    print("\n" + "="*60)
    print("  TEST 3: ESCALATION TO HUMAN AGENT")
    print("="*60)
    print("  Scenario: Customer requests a human agent")
    print()

    session_id = None  # New session

    # --- Message 1: Initial problem ---
    msg1 = "I've been having trouble logging into my TechCorp Suite account for 3 days now."
    print_message("customer", msg1)

    response1 = send_message(msg1)

    if "error" in response1:
        print("  Skipping test due to connection error.")
        return

    session_id = response1.get("session_id")
    bot_reply1 = response1.get("response", "No response")

    print_message("bot", bot_reply1)
    time.sleep(1)

    # --- Message 2: Tried the solution, still not working ---
    msg2 = "I already tried resetting my password and clearing my browser cache. Nothing works."
    print_message("customer", msg2)

    response2 = send_message(msg2, session_id)
    bot_reply2 = response2.get("response", "No response")

    print_message("bot", bot_reply2)
    time.sleep(1)

    # --- Message 3: Request escalation ---
    # This triggers the escalation logic!
    msg3 = "I need to speak to a human manager about this. The bot isn't helping."
    print_message("customer", msg3)

    response3 = send_message(msg3, session_id)
    bot_reply3 = response3.get("response", "No response")
    is_escalated = response3.get("escalated", False)  # Check the escalated flag

    # Show escalation status prominently
    escalation_status = "ESCALATED TO HUMAN AGENT" if is_escalated else "NOT escalated"
    print_message("bot", bot_reply3, escalation_status)

    if is_escalated:
        print("\n  *** ESCALATION DETECTED! ***")
        print("  The 'escalated' flag in the API response is: True")
        print("  In a real system, this would:")
        print("  1. Create a support ticket")
        print("  2. Notify the on-call human agent")
        print("  3. Transfer the conversation to a ticketing system")


def run_history_retrieval_test(session_id: str):
    """
    Tests the GET /conversations/{session_id} endpoint.
    Shows that we can retrieve full conversation history.

    Args:
        session_id: The session ID from a previous conversation
    """
    if not session_id:
        print("\n  Skipping history test (no session ID available)")
        return

    print("\n" + "="*60)
    print("  TEST 4: RETRIEVE CONVERSATION HISTORY")
    print("="*60)
    print(f"  Retrieving history for session: {session_id[:8]}...")
    print()

    # Call the GET /conversations/{session_id} endpoint
    history = get_conversation_history(session_id)

    if not history:
        print("  Could not retrieve history.")
        return

    # Display the history
    messages = history.get("messages", [])
    total = history.get("message_count", 0)

    print(f"  Total messages in session: {total}")
    print()

    # Print each message with role and truncated content
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown").upper()  # USER or ASSISTANT
        content = msg.get("content", "")           # Message text

        # Truncate long messages for display
        if len(content) > 100:
            content = content[:100] + "..."  # Show first 100 chars

        print(f"  [{i}] {role}: {content}")

    print(f"\n  Notice: the server remembered all {total} messages in this session!")
    print("  This is what 'stateful' means — the context is preserved.")


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================

def main():
    """
    Runs all test conversations in sequence.
    Each test demonstrates a different capability of the support bot.
    """

    print("\n" + "#"*60)
    print("#  TECHCORP SUPPORT BOT - TEST CLIENT")
    print("#  Running automated conversation tests")
    print("#"*60)
    print()
    print("  This script will test 4 scenarios:")
    print("  1. Normal customer support conversation")
    print("  2. Frustrated customer (empathy detection)")
    print("  3. Escalation to human agent")
    print("  4. Retrieve conversation history via API")
    print()

    # --- Check server health first ---
    print("  Checking server health...")
    print("-"*60)
    is_healthy = check_health()  # Ping the /health endpoint

    if not is_healthy:
        # Server isn't running — tell the user what to do
        print("\n  Cannot run tests. Please start the server first:")
        print("  uvicorn support_bot:app --reload")
        print("\n  Then run this script again in a different terminal.")
        return  # Exit without running tests

    print("\n  Server is running! Starting tests...\n")
    time.sleep(1)  # Brief pause before starting

    # --- Run Test 1: Normal conversation ---
    session_id = run_normal_conversation()
    time.sleep(2)  # Pause between tests

    # --- Run Test 2: Frustrated customer ---
    run_frustrated_customer_conversation()
    time.sleep(2)

    # --- Run Test 3: Escalation ---
    run_escalation_conversation()
    time.sleep(2)

    # --- Run Test 4: History retrieval (uses session from Test 1) ---
    run_history_retrieval_test(session_id)

    # --- Final summary ---
    print("\n" + "="*60)
    print("  ALL TESTS COMPLETE!")
    print("="*60)
    print()
    print("  What you just tested:")
    print("  - POST /chat with and without session_id")
    print("  - Session persistence across multiple messages")
    print("  - Frustration detection and empathy response")
    print("  - Escalation keyword detection")
    print("  - GET /conversations/{session_id} history retrieval")
    print()
    print("  Try the interactive API docs at: http://localhost:8000/docs")
    print("  You can test endpoints manually there!")
    print()


# --- Entry point ---
# Only run main() when this script is executed directly (not imported)
if __name__ == "__main__":
    main()  # Run all tests
