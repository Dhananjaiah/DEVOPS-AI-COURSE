# smart_notes.py
# A command-line tool that takes text (or a text file) and uses Claude to summarize it.
# You can run it three ways:
#   python smart_notes.py --text "Your text here"
#   python smart_notes.py --file notes.txt
#   python smart_notes.py              (will prompt you to type text interactively)
# Optionally add --output result.txt to save the summary to a file.

# ── Import Section ──────────────────────────────────────────────────────────

import os                       # "os" lets us read environment variables (like our API key).
import sys                      # "sys" lets us exit the program cleanly if something goes wrong.
import argparse                 # "argparse" lets us handle command-line arguments (flags like --text or --file).
                                # This is a standard Python library — no need to install it.

from dotenv import load_dotenv  # Reads our .env file and loads the API key into Python's memory.
from openai import OpenAI       # The OpenAI-compatible library — works with Groq too.


# ── Step 1: Load environment variables from .env file ───────────────────────

load_dotenv()  # Read the .env file. After this, os.getenv() can find our API key.

api_key = os.getenv("GROQ_API_KEY")  # Grab the Groq API key from environment variables.

if not api_key:                       # Safety check: if there's no API key, stop now.
    print("ERROR: GROQ_API_KEY not found in environment.")
    print("Please create a .env file with your key. See .env.example for the format.")
    print("Get your free key at: https://console.groq.com/keys")
    sys.exit(1)                       # Exit the program with error code 1.


# ── Step 2: Set up command-line argument parsing ────────────────────────────
# argparse lets users control your program from the terminal using "flags" like:
#   --text "some text"
#   --file myfile.txt
#   --output results.txt
# Without argparse, users would have to hardcode values inside the .py file.
# With argparse, your tool feels like a real professional command-line application.

parser = argparse.ArgumentParser(
    # argparse.ArgumentParser creates a new argument parser.
    # "description" is a help text that shows up when users type: python smart_notes.py --help
    description="Smart Notes Summarizer: Summarize any text using Claude AI."
)

parser.add_argument(
    "--text",                    # The name of the flag. Users type --text "some words".
    type=str,                    # The value should be a string (text). type=str is the default but being explicit is good.
    help="The text you want to summarize. Wrap it in quotes if it has spaces.",
    default=None                 # If the user doesn't provide --text, it will be None (empty).
)

parser.add_argument(
    "--file",                    # The name of the flag. Users type --file notes.txt.
    type=str,                    # The file path is a string.
    help="Path to a .txt file you want to summarize.",
    default=None                 # If the user doesn't provide --file, it will be None (empty).
)

parser.add_argument(
    "--output",                  # The name of the flag. Users type --output summary.txt.
    type=str,                    # The output file path is a string.
    help="Optional: path to save the summary output. Example: --output summary.txt",
    default=None                 # If not provided, we just print to the screen and don't save.
)

args = parser.parse_args()  # This actually READS the command-line arguments the user typed.
                             # Now args.text, args.file, and args.output hold the values.
                             # Example: if user typed --text "Hello world", then args.text = "Hello world"


# ── Step 3: Get the text to summarize ───────────────────────────────────────
# We have three possible sources of text:
#   1. --text flag: the user typed text directly
#   2. --file flag: the user gave us a file to read
#   3. Neither: ask the user interactively

input_text = None  # Start with no text. We'll fill this in below.
                   # "None" in Python means "nothing" or "empty" — like a blank space.

if args.text:
    # The user provided --text "some text here"
    input_text = args.text  # Use the text they typed directly. Simple!
    print(f"Summarizing text: '{input_text[:60]}...'")  # Preview first 60 characters.
                                                          # [:60] means "take characters from position 0 to 60".
                                                          # This is called "slicing" — very useful in Python.

elif args.file:
    # The user provided --file path/to/file.txt
    # "elif" means "else if" — we only check this if the first "if" was False.

    if not os.path.exists(args.file):  # os.path.exists() checks if a file actually exists.
        print(f"ERROR: File not found: {args.file}")   # If the file doesn't exist, tell the user.
        print("Please check the file path and try again.")
        sys.exit(1)                    # Exit with error.

    with open(args.file, "r", encoding="utf-8") as f:
        # "with open(...) as f:" is Python's way of safely opening a file.
        # "r" means "read mode" (we're only reading, not writing).
        # "encoding='utf-8'" makes sure special characters (like é, ñ, 中文) are read correctly.
        # The "with" keyword automatically closes the file when we're done — even if an error occurs.
        input_text = f.read()  # f.read() reads the entire file content as a single string.

    print(f"Summarizing file: {args.file} ({len(input_text)} characters)")
    # len(input_text) counts the number of characters in the text.
    # This tells the user how much text we loaded.

else:
    # The user didn't give us --text or --file, so we ask them interactively.
    # "else" runs when ALL the above "if" and "elif" conditions were False.
    print("No --text or --file argument provided.")
    print("Please type or paste your text below.")
    print("When you're done, press Enter twice (leave a blank line) to submit.")
    print("-" * 50)  # A visual separator.

    lines = []  # An empty list to collect lines of text as the user types them.
    while True:              # "while True" means "loop forever until we break out."
        line = input()       # input() waits for the user to type a line and press Enter.
        if line == "":       # If the user presses Enter with nothing typed (blank line)...
            break            # "break" exits the while loop. We're done collecting text.
        lines.append(line)   # .append() adds the new line to our list.
                             # Example: if user types "Hello", lines becomes ["Hello"]

    input_text = "\n".join(lines)  # Join all the lines back together with newline characters.
                                    # "\n".join(["line1", "line2"]) = "line1\nline2"
                                    # This reconstructs the full multi-line text.

if not input_text or input_text.strip() == "":
    # .strip() removes spaces and newlines from the start and end of a string.
    # We check if the text is completely empty even after stripping whitespace.
    print("ERROR: No text provided. Please provide text to summarize.")
    sys.exit(1)  # Exit if there's nothing to summarize.


# ── Step 4: Create the Groq client ──────────────────────────────────────────

client = OpenAI(                                 # Groq is OpenAI-compatible, so we use the same SDK.
    api_key=api_key,                             # Our Groq API key.
    base_url="https://api.groq.com/openai/v1"   # Point the client at Groq's servers instead of OpenAI.
)


# ── Step 5: Define the system prompt ────────────────────────────────────────
# A "system prompt" is a special instruction you give to Claude BEFORE the conversation starts.
# It sets Claude's role, personality, and rules.
# Think of it like a job briefing: "You are a professional note-taker. Your job is to..."
# The user never sees the system prompt — it's a behind-the-scenes instruction.

system_prompt = """You are a professional note-taker and summarizer. Your job is to help people
understand the key points of any text quickly and clearly.

When given text to summarize, always respond with EXACTLY this structure:

## Summary
[Write a clear 2-sentence summary of the main point]

## Key Points
- [First key point]
- [Second key point]
- [Third key point]

## Action Item
[One concrete action item if applicable, or write "No specific action item identified." if not applicable]

Be concise, clear, and professional. Use plain English that anyone can understand."""

# Triple quotes """ let us write a string across multiple lines.
# This is much more readable than trying to cram everything on one line.


# ── Step 6: Build the user message ──────────────────────────────────────────
# We combine the instruction with the actual text the user wants summarized.

user_message = f"""Please summarize the following text:

---
{input_text}
---"""
# We use an f-string to insert input_text into the message template.
# The --- lines are just visual markers to clearly separate the instruction from the text.


# ── Step 7: Send to Claude and get the summary ──────────────────────────────

model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
# os.getenv("GROQ_MODEL", "llama-3.1-8b-instant") tries to read GROQ_MODEL from .env.
# If not set, defaults to "llama-3.1-8b-instant" — fast, free, and capable.
# Other good free Groq models: "llama-3.3-70b-versatile", "mixtral-8x7b-32768"

print("\nSending to Groq for summarization...")  # Status message so the user knows it's working.
print("Please wait...\n")

response = client.chat.completions.create(  # Send the message to Groq. Same API shape as OpenAI.
    model=model,                             # Which AI model to use.
    max_tokens=1024,                         # Max length of the response (in tokens).
    messages=[                               # The conversation messages.
        {
            "role": "system",                # System message sets the AI's role/instructions.
            "content": system_prompt         # The system prompt we defined above.
        },
        {
            "role": "user",                  # This message is from us (the user).
            "content": user_message          # The actual text: instruction + the text to summarize.
        }
    ]
)

summary_text = response.choices[0].message.content  # Extract the response text.
                                                      # Same structure as OpenAI: choices[0].message.content


# ── Step 8: Print the summary nicely ────────────────────────────────────────

print("=" * 60)                          # Print 60 "=" signs as a top border.
print("           SMART NOTES SUMMARY")  # Centered title.
print("=" * 60)                          # Another border.
print(summary_text)                      # Print Claude's full formatted response.
print("=" * 60)                          # Bottom border.

print(f"\nTokens used: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output")
# Show token usage so students can see the cost pattern.


# ── Step 9: Optionally save the output to a file ────────────────────────────

if args.output:
    # Only do this if the user provided --output filename.txt
    # Otherwise args.output is None and we skip this block.

    output_content = f"""SMART NOTES SUMMARY
Generated by smart_notes.py
{'=' * 60}

Original source: {args.file if args.file else 'Direct text input'}

{summary_text}

{'=' * 60}
Tokens used: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output
"""
    # This builds the full text we'll save to the file.
    # We include metadata like the source and token count.

    with open(args.output, "w", encoding="utf-8") as f:
        # "w" means "write mode" — create the file or overwrite it if it exists.
        # encoding="utf-8" handles special characters.
        f.write(output_content)  # Write the content string to the file.

    print(f"\nSummary saved to: {args.output}")  # Tell the user where the file was saved.

print("\nDone!")  # Final success message.
