# hello_ai.py
# This is your very first AI program! It sends a message to an OpenAI model
# and prints back the response.

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


# Step 1: Load the secret API key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# Step 2: Safety check
if not api_key:
    print("ERROR: No API key found!")
    print("Please do these steps:")
    print("  1. Copy .env.example to a new file called .env")
    print("  2. Open .env and replace 'sk-proj-your-key-here' with your real API key")
    print("  3. Get your key at: https://platform.openai.com/api-keys")
    sys.exit(1)

print("API key loaded successfully!")


# Step 3: Create the OpenAI client
client = OpenAI(api_key=api_key)


# Step 4: Define the message
my_question = "Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?"
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# Step 5: Print a status message
print("\n" + "=" * 50)
print("Sending message to OpenAI...")
print(f"Model: {model}")
print(f"Your question: {my_question}")
print("=" * 50 + "\n")


# Step 6: Send the message and get a response
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": my_question,
        }
    ],
    max_tokens=300,
)


# Step 7: Extract response text
answer_text = response.choices[0].message.content or "(No text returned)"


# Step 8: Print response
print("AI Response:")
print("-" * 50)
print(answer_text)
print("-" * 50)


# Step 9: Show token usage
print("\nToken Usage:")
if response.usage:
    print(f"  Input tokens  : {response.usage.prompt_tokens}")
    print(f"  Output tokens : {response.usage.completion_tokens}")
    print(f"  Total tokens  : {response.usage.total_tokens}")
else:
    print("  Usage data not returned by the API.")

print("\nDone! Your first AI call was a success!")