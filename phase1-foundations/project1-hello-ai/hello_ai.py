# hello_ai.py
# This is your very first AI program! It sends a message to Claude (an AI)
# and prints back the response. Think of it like texting a really smart robot.

# ── Import Section ──────────────────────────────────────────────────────────
# "import" means we are bringing in tools that other people wrote for us.
# We don't have to build these tools ourselves — we just use them.

import os                    # "os" lets Python talk to your operating system (Windows/Mac/Linux).
                             # We use it to read environment variables (secret settings).

from dotenv import load_dotenv  # "dotenv" reads a file called ".env" and loads secret values
                                 # like your API key into Python so you don't have to type them in code.

import anthropic             # "anthropic" is the official library made by Anthropic (the company
                             # that built Claude). It lets us talk to Claude from Python.

import sys                   # "sys" gives us access to system-level things like exiting the program
                             # if something goes wrong.


# ── Step 1: Load the secret API key ─────────────────────────────────────────
# An API key is like a password that proves to Anthropic that YOU are allowed
# to use their AI. Without it, the program won't work.

load_dotenv()  # This reads the ".env" file in the same folder and loads all
               # the values inside it into Python's memory.
               # Example: if .env says ANTHROPIC_API_KEY=abc123, now Python knows that.

api_key = os.getenv("ANTHROPIC_API_KEY")  # os.getenv() looks up a value by name.
                                           # We are looking for "ANTHROPIC_API_KEY".
                                           # If it finds it, api_key will hold that value.
                                           # If it doesn't find it, api_key will be None (empty).


# ── Step 2: Safety check — make sure the API key actually exists ─────────────
# It would be confusing to run the whole program and get a weird error at the end
# just because the API key was missing. So we check FIRST.

if not api_key:                          # "if not api_key" means: "if api_key is empty or None"
    print("ERROR: No API key found!")    # Print a clear error message to the screen.
    print("Please do these steps:")      # Tell the user what to do next.
    print("  1. Copy .env.example to a new file called .env")
    print("  2. Open .env and replace 'sk-ant-your-key-here' with your real API key")
    print("  3. Get your key at: https://console.anthropic.com/")
    sys.exit(1)                          # Stop the program right now. The "1" means "error exit".
                                         # (sys.exit(0) would mean "everything was fine")

# If we get past the "if" block above, we know the API key exists.
print("API key loaded successfully!")    # Tell the user things are looking good.


# ── Step 3: Create the Anthropic client ─────────────────────────────────────
# Think of the "client" as opening a phone line to Anthropic's servers.
# Before you can send any messages, you need to open that connection first.

client = anthropic.Anthropic(api_key=api_key)  # Create a new Anthropic client object.
                                                # We pass in our api_key so it knows who we are.
                                                # This client object has methods like .messages.create()
                                                # that we'll use to actually send messages.


# ── Step 4: Define the message we want to send ──────────────────────────────
# We put our question in a variable so it's easy to see and change.

my_question = "Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?"
# This is the text we'll send to Claude. It's just a regular Python string (text).
# A string in Python is any text wrapped in quote marks.


# ── Step 5: Print a friendly status message ─────────────────────────────────
print("\n" + "="*50)          # Print a blank line, then 50 "=" signs as a visual separator.
                               # "="*50 means repeat the character "=" fifty times.
print("Sending message to Claude...")   # Let the user know we are about to send the request.
print(f"Your question: {my_question}")  # Print the question. The "f" before the quote means
                                         # we can put variable names inside curly braces {}.
                                         # This is called an "f-string" (formatted string).
print("="*50 + "\n")          # Another separator line, then a blank line.


# ── Step 6: Send the message to Claude and get a response ───────────────────
# This is the most important part! This is where we actually talk to the AI.

response = client.messages.create(   # Call the .create() method on the messages object.
                                      # This sends our message to Anthropic's servers.
                                      # It waits until Claude responds, then gives us the response.

    model="claude-opus-4-6",          # Tell Anthropic WHICH version of Claude to use.
                                       # Think of it like choosing which expert to call.
                                       # "claude-opus-4-6" is a powerful model.

    max_tokens=1024,                   # "max_tokens" limits how long Claude's response can be.
                                        # A "token" is roughly 3/4 of a word.
                                        # 1024 tokens = roughly 750 words max.
                                        # This prevents huge expensive responses by accident.

    messages=[                          # "messages" is a LIST of message objects.
                                         # A list in Python uses square brackets [ ].
                                         # Each message is a DICTIONARY with "role" and "content".
                                         # A dictionary uses curly braces { } and has key:value pairs.
        {
            "role": "user",              # "role" says WHO is speaking. "user" means it's from you.
                                          # Other possible role is "assistant" (Claude's replies).
            "content": my_question       # "content" is the actual text of the message.
                                          # We use our variable my_question from Step 4.
        }
    ]
)
# At this point, "response" holds everything Claude sent back:
# - The text answer
# - How many tokens were used
# - Other metadata


# ── Step 7: Extract the text from the response ──────────────────────────────
# The response object has a specific structure. We need to dig into it to get the text.

answer_text = response.content[0].text   # response.content is a list of content blocks.
                                           # [0] means "get the first item" (Python counts from 0).
                                           # .text gets the actual text string from that block.


# ── Step 8: Print Claude's response nicely ──────────────────────────────────
print("Claude's Response:")              # A header label.
print("-" * 50)                          # A line of dashes as a separator. "-"*50 = 50 dashes.
print(answer_text)                       # Print Claude's actual answer text.
print("-" * 50)                          # Another separator line.


# ── Step 9: Show token usage ────────────────────────────────────────────────
# Tokens are how Anthropic charges for API usage. It's good practice to see how many were used.
# Think of tokens like "usage minutes" on a phone plan.

print("\nToken Usage:")                             # Header for the usage section.
print(f"  Input tokens  : {response.usage.input_tokens}")   # How many tokens YOUR message used.
                                                              # (The question you sent)
print(f"  Output tokens : {response.usage.output_tokens}")  # How many tokens CLAUDE'S response used.
                                                              # (The answer Claude gave)
print(f"  Total tokens  : {response.usage.input_tokens + response.usage.output_tokens}")
# Total = input + output added together.
# The + between two numbers in Python means addition (same as in math class).

print("\nDone! Your first AI call was a success!")  # Celebrate! You did it!
