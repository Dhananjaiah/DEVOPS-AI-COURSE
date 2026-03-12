# hello_ai.py
# This is your very first AI program! It sends a message to an OpenAI model
# and prints back the response.
# You can run it simply with:
#   python hello_ai.py
# Before running, make sure you have a .env file with your OPENAI_API_KEY set.

# ── Import Section ──────────────────────────────────────────────────────────

import os                       # "os" lets us read environment variables (like our API key).
import sys                      # "sys" lets us exit the program cleanly if something goes wrong.

from dotenv import load_dotenv  # Reads our .env file and loads the API key into Python's memory.
                                # Without this, Python wouldn't know about our secret key.
from openai import OpenAI       # The official library to talk to OpenAI's GPT models.
                                # This is installed via "pip install openai".


# ── Step 1: Load environment variables from .env file ───────────────────────

load_dotenv()  # Read the .env file in the current directory.
               # After this, os.getenv() can find our API key.
               # The .env file should contain: OPENAI_API_KEY=sk-proj-your-key-here

api_key = os.getenv("OPENAI_API_KEY")  # Grab the API key value from environment variables.
                                        # os.getenv() looks for a variable by name and returns its value.
                                        # If the variable doesn't exist, it returns None (empty).


## ── Step 2: Safety check — make sure we have an API key ─────────────────────
# If the user forgot to set up the .env file, we want to give them a helpful
# error message instead of a confusing crash later.

if not api_key:                        # "not api_key" is True when api_key is None or empty string "".
    print("ERROR: No API key found!")  # Tell the user what went wrong.
    print("Please do these steps:")    # Give them clear instructions to fix it.
    print("  1. Copy .env.example to a new file called .env")
    print("  2. Open .env and replace 'sk-proj-your-key-here' with your real API key")
    print("  3. Get your key at: https://platform.openai.com/api-keys")
    sys.exit(1)                        # Exit the program with error code 1.
                                       # Code 1 means "something went wrong".
                                       # Code 0 would mean "everything is fine".

print("API key loaded successfully!")  # If we reach this line, the key exists. 


# ── Step 3: Create the OpenAI client ────────────────────────────────────────

client = OpenAI(api_key=api_key)  # Create a "client" object that connects to OpenAI's servers.
                                   # Think of it like opening a phone line to OpenAI.
                                   # We pass our api_key so OpenAI knows who we are.
                                   # All future API calls will go through this client object.


# ── Step 4: Define the message we want to send ──────────────────────────────

my_question = "Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?"
# This is the text we'll send to GPT. You can change this to ask anything!

model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# os.getenv("OPENAI_MODEL", "gpt-4o-mini") tries to read OPENAI_MODEL from .env.
# If it's not set, it falls back to "gpt-4o-mini" (the second argument is the default).
# "gpt-4o-mini" is a fast, cheap model — great for learning and testing.
# You could also use "gpt-4o" for a more powerful (but more expensive) model.


# ── Step 5: Print a status message ──────────────────────────────────────────
# This lets the user see what's happening before the API call is made.
# API calls can take a few seconds, so it's nice to show a "working..." message.

print("\n" + "=" * 50)              # "\n" adds a blank line. "=" * 50 prints 50 "=" signs as a visual border.
print("Sending message to OpenAI...")  # Tell the user we're about to call the API.
print(f"Model: {model}")            # f-string: inserts the value of "model" into the string.
                                     # Example output: "Model: gpt-4o-mini"
print(f"Your question: {my_question}")  # Show the user what question we're sending.
print("=" * 50 + "\n")              # Bottom border with a trailing blank line for spacing.


# ── Step 6: Send the message and get a response ─────────────────────────────
# This is the core API call — the line that actually talks to OpenAI!

response = client.chat.completions.create(  # Call OpenAI's Chat Completions API.
                                             # "create" sends our message and waits for a reply.
                                             # The result is stored in "response".
    model=model,                             # Which AI model to use (e.g., "gpt-4o-mini").
    messages=[                               # The conversation history as a list of messages.
                                             # Each message has a "role" and "content".
        {
            "role": "user",                  # "user" means this message is from us (the human).
                                             # Other roles: "system" (instructions) and "assistant" (AI's reply).
            "content": my_question,          # The actual text of our question.
        }
    ],
    max_tokens=300,                          # Limit the response to 300 tokens max.
                                             # A "token" is roughly ¾ of a word.
                                             # 300 tokens ≈ about 225 words.
                                             # This prevents unexpectedly long (and expensive) responses.
)


# ── Step 7: Extract the response text ───────────────────────────────────────

answer_text = response.choices[0].message.content or "(No text returned)"
# response.choices    → A list of possible replies (usually just one).
# [0]                 → Get the first (and typically only) choice.
# .message            → The message object inside that choice.
# .content            → The actual text string of the AI's reply.
# "or" is a fallback  → If .content is None or empty, use "(No text returned)" instead.
#                        This prevents our program from crashing on an empty response.


# ── Step 8: Print the AI's response ─────────────────────────────────────────

print("AI Response:")                # Label so the user knows what follows.
print("-" * 50)                      # Print 50 "-" signs as a visual separator.
print(answer_text)                   # Print the actual text that GPT sent back.
print("-" * 50)                      # Bottom separator for a clean, boxed look.


# ── Step 9: Show token usage ────────────────────────────────────────────────
# Tokens are how OpenAI measures usage and billing.
# Showing this helps you understand the cost of each API call.
# pricing info: https://openai.com/api/pricing/

print("\nToken Usage:")                # "\n" adds a blank line before this section.
if response.usage:                     # Check if the API returned usage data.
                                       # It almost always does, but we check just in case.
    print(f"  Input tokens  : {response.usage.prompt_tokens}")
    # "prompt_tokens" = how many tokens YOUR question used.
    # More text in your question = more input tokens = slightly higher cost.

    print(f"  Output tokens : {response.usage.completion_tokens}")
    # "completion_tokens" = how many tokens the AI's REPLY used.
    # Output tokens are usually more expensive than input tokens.

    print(f"  Total tokens  : {response.usage.total_tokens}")
    # "total_tokens" = prompt_tokens + completion_tokens.
    # This is the total "size" of this API call.
else:
    print("  Usage data not returned by the API.")
    # Fallback message in case usage data isn't available.

print("\nDone! Your first AI call was a success!")
# Final success message. If you see this, everything worked! 🎉