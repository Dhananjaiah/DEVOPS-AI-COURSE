# Project 1: Hello AI — Your First Conversation with Claude

**Difficulty:** Absolute Beginner
**Time to Complete:** 30–45 minutes
**Prerequisite:** Python installed, VS Code (or any text editor)

---

## 1. Project Overview

Welcome to your very first AI project! This is where your journey into AI engineering begins.

In this project, you will write a Python program that sends a message to Claude (an AI made by Anthropic) and prints the response in your terminal. That's it. Simple — but incredibly powerful.

**Why does this matter for real jobs?**

Nearly every tech company in 2025 is adding AI into their products. When a developer knows how to connect a program to an AI model using an API, they are valuable. This exact skill — calling an AI from code — is the foundation of:

- AI-powered customer support bots
- Automated report generation tools
- Smart search features inside apps
- AI assistants in enterprise software

When you complete this project, you will have done the same thing that professional engineers do when they first wire up an AI feature. It's not magic — it's just code you can learn.

---

## 2. What You Are Building

You are building a Python script called `hello_ai.py`. When you run it, it will:

1. Secretly load your API key from a `.env` file (so you never paste your password in code)
2. Connect to Anthropic's servers (the company that made Claude)
3. Send this exact message: *"Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?"*
4. Print Claude's response in a clear format in your terminal
5. Show how many "tokens" (words) were used — this is how API costs are calculated

Here is what the end result looks like:

```
API key loaded successfully!

==================================================
Sending message to Claude...
Your question: Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?
==================================================

Claude's Response:
--------------------------------------------------
An AI agent is like a really smart robot helper that can read, think, and do tasks on its own, like searching the internet or writing emails for you. You give it a goal, and it figures out the steps to reach that goal all by itself!
--------------------------------------------------

Token Usage:
  Input tokens  : 34
  Output tokens : 52
  Total tokens  : 86

Done! Your first AI call was a success!
```

---

## 3. Setup Instructions

Follow every step carefully. If something goes wrong, read the error message — it usually tells you exactly what is wrong.

### Step 1: Make sure Python is installed

Open your terminal (on Windows: press `Windows + R`, type `cmd`, press Enter).

Type this and press Enter:
```bash
python --version
```

You should see something like `Python 3.11.0` or higher. If you see an error, install Python from [python.org](https://python.org).

### Step 2: Navigate to the project folder

In your terminal, move into this project's folder:
```bash
cd C:\Users\techi\Downloads\2026\DEVOPS-AI-COURSE\phase1-foundations\project1-hello-ai
```

### Step 3: Create a virtual environment

A virtual environment is like a clean room for your project. It keeps this project's tools separate from other Python projects on your computer. Think of it like having separate toolboxes for separate jobs.

```bash
python -m venv venv
```

This creates a folder called `venv` inside your project folder.

### Step 4: Activate the virtual environment

This "turns on" the clean room so Python uses it:

**On Windows:**
```bash
venv\Scripts\activate
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

After activation, your terminal prompt will change to show `(venv)` at the start. That means it worked!

```
(venv) C:\Users\techi\...\project1-hello-ai>
```

**IMPORTANT:** If you close your terminal and come back, you MUST activate the virtual environment again before running any commands.

### Step 5: Install the required libraries

```bash
pip install -r requirements.txt
```

This reads `requirements.txt` and installs all the libraries listed. It may take 1–2 minutes. You'll see a bunch of text scrolling — that's normal.

### Step 6: Create your `.env` file

Your `.env` file stores your secret API key. **Never share this file or put it in GitHub.**

Copy the example file:

**On Windows:**
```bash
copy .env.example .env
```

**On Mac/Linux:**
```bash
cp .env.example .env
```

Now open `.env` in a text editor and replace `sk-ant-your-key-here` with your real API key.

### Step 7: Get your API key

1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign up or log in
3. Click on "API Keys" in the left sidebar
4. Click "Create Key"
5. Copy the key (it starts with `sk-ant-`)
6. Paste it into your `.env` file

Your `.env` file should look like this:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 8: Run the program!

```bash
python hello_ai.py
```

---

## 4. Complete Code Walkthrough

Let's go through every part of `hello_ai.py` so you understand what each line does.

### Part 1: Imports

```python
import os
from dotenv import load_dotenv
import anthropic
import sys
```

**What is an import?**
When you "import" something in Python, you are saying: "Hey Python, go find this tool and bring it into my program so I can use it."

- `os` — Stands for "operating system". It lets Python read environment variables (secret values stored outside your code).
- `load_dotenv` — This specific function from the `dotenv` library reads your `.env` file.
- `anthropic` — The official Python library for talking to Claude. Without this, we'd have to write hundreds of lines of complex networking code ourselves.
- `sys` — Gives us `sys.exit()` which lets us stop the program if something goes wrong.

### Part 2: Loading the API Key

```python
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
```

**What is a `.env` file?**
It's a plain text file that holds secrets (like passwords) in a format like:
```
SECRET_NAME=secret_value
```

**Why not just put the API key directly in the code?**
If you put your API key directly in the code (`api_key = "sk-ant-abc123"`), anyone who sees your code (on GitHub, for example) can steal your key and use it. You would get charged for their usage! The `.env` file is kept separate and not shared.

`load_dotenv()` reads the `.env` file. After that, `os.getenv("ANTHROPIC_API_KEY")` retrieves the value.

### Part 3: Safety Check

```python
if not api_key:
    print("ERROR: No API key found!")
    sys.exit(1)
```

**What is an `if` statement?**
An `if` statement checks a condition. If the condition is true, it runs the code inside. Here we check: "Is api_key empty (None)?" If yes, print an error and stop the program.

This is called "defensive programming" — you check for problems early rather than letting them cause confusing errors later.

### Part 4: Creating the Client

```python
client = anthropic.Anthropic(api_key=api_key)
```

This creates an "Anthropic client object". Think of it like dialing a phone number. The `client` variable now holds an open connection to Anthropic's service, ready to send and receive messages.

### Part 5: Sending the Message

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": my_question
        }
    ]
)
```

This is the core API call. Breaking it down:

| Parameter | What it does |
|-----------|--------------|
| `model` | Which AI model to use. Like choosing which expert you want to talk to. |
| `max_tokens` | The maximum length of Claude's response. 1 token ≈ 0.75 words. |
| `messages` | A list of the conversation so far. Each message has a "role" and "content". |
| `role: "user"` | Marks this message as coming from you (the human). |
| `content` | The actual text of your message. |

### Part 6: Reading the Response

```python
answer_text = response.content[0].text
```

The `response` object has this structure:
```
response
  └── content  (a list)
        └── [0]  (the first item in the list)
              └── .text  (the actual text string)
```

We use `[0]` because Python lists start counting at 0. The first item is always at index 0.

### Part 7: Token Usage

```python
print(f"  Input tokens  : {response.usage.input_tokens}")
print(f"  Output tokens : {response.usage.output_tokens}")
```

Every API call costs money based on tokens. Understanding token usage helps you:
- Estimate costs before building a big feature
- Optimize your prompts to be shorter (and cheaper)
- Debug when you're accidentally sending huge inputs

---

## 5. Sample Output

When you run `python hello_ai.py` successfully, you should see something like this:

```
API key loaded successfully!

==================================================
Sending message to Claude...
Your question: Hello! Can you explain what an AI agent is in 2 sentences, like I'm 10 years old?
==================================================

Claude's Response:
--------------------------------------------------
An AI agent is like a really smart helper that can think on its own and do tasks for you, like searching the internet, writing emails, or solving problems step by step. You give it a goal, and it figures out how to reach that goal all by itself without you having to tell it every tiny thing to do!
--------------------------------------------------

Token Usage:
  Input tokens  : 34
  Output tokens : 58
  Total tokens  : 92

Done! Your first AI call was a success!
```

**Note:** Claude's exact response will vary each time you run it. That's normal — AI models don't give the exact same answer twice, just like a person wouldn't word things exactly the same twice.

---

## 6. Real World Use Cases

Companies use this exact technique (calling an AI API from code) in many real products:

### Example 1: Automated Customer Support at Scale
A company like an online bank has millions of customers sending emails every day asking "What's my balance?", "How do I reset my password?", "Why was I charged twice?" Instead of hiring 1,000 support agents, they write code that reads each email, sends it to Claude, and lets Claude write a helpful first-response. Human agents only handle the tricky ones. This saves millions of dollars per year.

### Example 2: Internal Knowledge Tools at Tech Companies
Large tech companies have thousands of internal documents, wikis, runbooks, and policies. New employees spend weeks just finding information. Engineers build tools where employees can type a question and the tool uses Claude to find and summarize the relevant documents instantly. This is exactly what you will build in Project 3 (RAG systems).

### Example 3: AI-Powered Code Review
Some companies use Claude to do a first pass of code review on every pull request (when a developer submits new code). The AI checks for common bugs, security issues, and style problems, and leaves comments. This catches obvious problems before human reviewers even look, saving senior developer time.

---

## 7. Extend This Project

Once you have `hello_ai.py` working, try these enhancements to practice:

### Idea 1: Make it Ask the User for Input
Instead of a hardcoded question, let the user type their own question:

```python
# Replace the hardcoded question line with:
my_question = input("What would you like to ask Claude? ")
```

Now your program becomes an interactive chatbot!

### Idea 2: Ask Multiple Questions in a Loop
Use a `while` loop so the user can keep asking questions until they type "quit":

```python
while True:
    my_question = input("\nAsk a question (or type 'quit' to stop): ")
    if my_question.lower() == "quit":
        break
    # ... rest of your API call code here
```

### Idea 3: Save Conversations to a File
After getting Claude's response, save both the question and answer to a text file:

```python
with open("conversation_log.txt", "a") as f:  # "a" means "append" (add to end, don't overwrite)
    f.write(f"Question: {my_question}\n")
    f.write(f"Answer: {answer_text}\n")
    f.write("-" * 50 + "\n")
```

---

## 8. What You Learned

| Concept | What It Means |
|---------|--------------|
| API | Application Programming Interface — a way for programs to talk to each other over the internet |
| API Key | A secret password that identifies you to an external service |
| `.env` file | A file that stores secrets outside your code so they don't accidentally get shared |
| `python-dotenv` | A Python library that reads `.env` files and loads them into Python |
| `anthropic` library | The official Python library for talking to Claude |
| Client object | A Python object that holds an open connection to a service, ready to make requests |
| `messages.create()` | The function that sends your message to Claude and waits for a response |
| Tokens | The unit of measurement for text in AI models (roughly 0.75 words per token) |
| `max_tokens` | A limit on how long the AI's response can be |
| f-strings | Python's way of inserting variable values into text strings using `f"..."` syntax |
| `sys.exit()` | A way to stop a Python program immediately, useful when an error occurs |
| Virtual environment | An isolated Python environment for a specific project, prevents version conflicts |

---

## 9. Quiz Questions

Test yourself! Try to answer from memory before revealing the answers.

**Question 1:** Why do we store the API key in a `.env` file instead of writing it directly in the Python code?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** Security. If you put your API key directly in your code (`api_key = "sk-ant-abc123"`), anyone who reads your code — for example if you accidentally push it to GitHub — can see and steal your key. They could then use it to call the API and you would be charged for their usage. The `.env` file is kept out of version control (added to `.gitignore`) so it's never shared. The code only contains the variable name, not the actual secret value.

</details>

---

**Question 2:** What does `max_tokens=1024` do in the API call, and what happens if you set it to 10?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** `max_tokens` sets the maximum length of Claude's response. Each "token" is roughly 0.75 words (so 1024 tokens ≈ about 768 words). If you set `max_tokens=10`, Claude would stop writing after about 7-8 words, even if it was in the middle of a sentence. It's a hard cut-off. You set this to control costs (longer responses use more tokens and cost more money) and to prevent runaway responses that are unexpectedly long.

</details>

---

**Question 3:** What does `response.content[0].text` mean? Why the `[0]`?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** `response` is the object that came back from the API call. It contains a field called `content`, which is a Python list (a collection of items). Even if Claude only sends one message back, it's still wrapped in a list. `[0]` means "give me the first item in this list" — Python counts list positions starting from 0, not 1. So the first item is always at index `[0]`. Then `.text` gets the actual text string from that item. The full chain `response.content[0].text` means: "From the response, get the content list, take the first item, and give me its text."

</details>
