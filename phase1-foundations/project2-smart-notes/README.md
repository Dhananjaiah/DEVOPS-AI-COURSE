# Project 2: Smart Notes — AI-Powered Text Summarizer

**Difficulty:** Beginner (builds on Project 1)
**Time to Complete:** 45–60 minutes
**Prerequisite:** Completed Project 1 — Hello AI

---

## 1. Project Overview

In Project 1, you sent a single hardcoded message to Claude. That was your "Hello World" moment. Now we step it up.

In this project, you will build a real command-line tool — the kind engineers actually use in their daily work. It summarizes text using Claude. You can point it at any text file, or type text directly in your terminal, and it will return a clean, structured summary with key points and action items.

**Why does this matter for real jobs?**

Almost every company has too much text and not enough time. Engineers get pinged with long Slack threads. Managers wade through 20-page spec documents. Support teams read hundreds of customer emails a day. A tool that can instantly distill any blob of text into key points saves enormous amounts of human time.

Companies like Notion, Confluence, and Linear are embedding exactly this kind of AI summarization into their products. When you know how to build it yourself, you can propose and implement this kind of feature at your job — and that gets you noticed.

**New concepts you'll learn in this project:**
- System prompts — how to give Claude a role and instructions
- argparse — how to build real command-line tools with flags
- File I/O — reading from and writing to text files in Python
- f-strings with multi-line strings (triple quotes)

---

## 2. What You Are Building

`smart_notes.py` is a CLI (command-line interface) tool. CLI means you control it by typing commands in your terminal, not by clicking buttons.

You can use it in three ways:

**Way 1: Pass text directly**
```bash
python smart_notes.py --text "The quarterly revenue exceeded targets by 12%..."
```

**Way 2: Pass a file**
```bash
python smart_notes.py --file sample_notes.txt
```

**Way 3: Interactive mode (no arguments)**
```bash
python smart_notes.py
# Then you type or paste your text and press Enter twice when done
```

**Bonus: Save the output**
```bash
python smart_notes.py --file sample_notes.txt --output summary.txt
```

Claude will respond with a structured summary like this:
```
============================================================
           SMART NOTES SUMMARY
============================================================

## Summary
Planning software projects requires clear problem definition and stakeholder alignment. Breaking work into small tasks, realistic estimation, and regular communication prevent the most common project failures.

## Key Points
- Define success with specific, measurable goals before writing any code
- Break large tasks into pieces completable in 1-2 days to track progress accurately
- Build in buffer time because unexpected problems always occur in software development

## Action Item
Schedule a kickoff meeting to define project goals with specific success metrics before beginning development.

============================================================

Tokens used: 487 input, 112 output
Done!
```

---

## 3. Setup Instructions

### Step 1: Navigate to the project folder

```bash
cd C:\Users\techi\Downloads\2026\DEVOPS-AI-COURSE\phase1-foundations\project2-smart-notes
```

### Step 2: Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create your `.env` file

```bash
copy .env.example .env
```

Open `.env` and add your Anthropic API key. If you did Project 1, you already have a key. Just copy it from that project's `.env` file.

### Step 5: Test it!

Run it with the sample file:
```bash
python smart_notes.py --file sample_notes.txt
```

Or try the interactive mode:
```bash
python smart_notes.py
```

Or pass text directly:
```bash
python smart_notes.py --text "Python is a programming language that is easy to learn and widely used in AI, web development, and data science. It has a simple syntax and a large community."
```

---

## 4. Complete Code Walkthrough

### Part 1: Imports

```python
import os
import sys
import argparse
from dotenv import load_dotenv
import anthropic
```

You already know `os`, `sys`, `dotenv`, and `anthropic` from Project 1. The new one is:

**`argparse`** — This is Python's built-in library for handling command-line arguments. It reads what the user typed after `python smart_notes.py` and makes those values available as variables in your code.

For example, if the user types:
```
python smart_notes.py --file notes.txt --output result.txt
```

After argparse processes this, you have:
- `args.file == "notes.txt"`
- `args.output == "result.txt"`

Without argparse, you'd have to manually parse `sys.argv` (the raw list of everything typed), which is messy and error-prone.

### Part 2: Setting Up argparse

```python
parser = argparse.ArgumentParser(
    description="Smart Notes Summarizer: Summarize any text using Claude AI."
)

parser.add_argument("--text", type=str, help="...", default=None)
parser.add_argument("--file", type=str, help="...", default=None)
parser.add_argument("--output", type=str, help="...", default=None)

args = parser.parse_args()
```

**What is `ArgumentParser`?**
It's an object that manages all your command-line flags. You create one parser, add your flags to it, then call `parse_args()` which reads the actual terminal input and fills in the values.

**What does `default=None` mean?**
If the user doesn't provide that flag, the value is `None`. So if the user types `python smart_notes.py --file notes.txt` without `--output`, then `args.output` will be `None`. You can check `if args.output:` to decide whether to save a file.

**Free bonus: `--help`**
Because we used argparse, the user can type `python smart_notes.py --help` and automatically get this:
```
usage: smart_notes.py [-h] [--text TEXT] [--file FILE] [--output OUTPUT]

Smart Notes Summarizer: Summarize any text using Claude AI.

options:
  -h, --help       show this help message and exit
  --text TEXT      The text you want to summarize...
  --file FILE      Path to a .txt file you want to summarize.
  --output OUTPUT  Optional: path to save the summary output.
```

You didn't write that help text — argparse built it automatically from the `description` and `help` strings you provided!

### Part 3: Getting the Text

```python
if args.text:
    input_text = args.text
elif args.file:
    with open(args.file, "r", encoding="utf-8") as f:
        input_text = f.read()
else:
    # interactive mode...
```

**What is `with open(...) as f`?**

This is how Python reads and writes files. Let's break it down:

- `open(args.file, "r")` — Opens a file. `"r"` means read mode. Other modes:
  - `"w"` — write mode (creates or overwrites)
  - `"a"` — append mode (adds to end of existing file)
- `encoding="utf-8"` — Tells Python how to interpret the bytes in the file. UTF-8 handles special characters from any language.
- `as f` — Names the open file object `f`. You can call it anything, but `f` is the convention.
- `f.read()` — Reads the entire file content as one string.
- The `with` keyword — Automatically closes the file when the block ends. If you didn't use `with`, you'd have to call `f.close()` manually. If your program crashed before `f.close()`, the file could get corrupted. `with` prevents this.

**Interactive mode — what is a `while` loop?**

```python
lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)
input_text = "\n".join(lines)
```

A `while True` loop runs forever until something breaks it. Here, we keep reading lines until the user types a blank line. Then `break` exits the loop. `"\n".join(lines)` glues all the lines back together with newline characters between them.

### Part 4: The System Prompt

```python
system_prompt = """You are a professional note-taker and summarizer...
Always respond with EXACTLY this structure:
## Summary
...
## Key Points
...
## Action Item
..."""
```

**What is a system prompt and why is it powerful?**

In Project 1, we only sent one kind of message to Claude: a user message. There's actually a second type: the **system prompt**. It's passed separately as `system=system_prompt` in the API call.

Think of it this way:
- **User message** = what you say to Claude in the conversation
- **System prompt** = the job description you give Claude BEFORE the conversation starts

The system prompt shapes Claude's entire behavior. You can use it to:
- Give Claude a role: "You are a customer support agent for Acme Corp"
- Set a tone: "Always respond formally and never use casual language"
- Force a format: "Always respond in JSON format"
- Add rules: "If the user asks about competitor products, politely redirect them"
- Restrict behavior: "Only answer questions about cooking. For anything else, say you can't help"

In our case, we use the system prompt to:
1. Give Claude a role ("professional note-taker")
2. Force a specific output structure (the `## Summary`, `## Key Points` format)

The structured output is key for building real tools. If Claude sometimes gives a summary and sometimes gives a bullet list and sometimes gives a paragraph, your code can't reliably parse or display it. By forcing a format in the system prompt, you get consistent, predictable output.

### Part 5: The API Call

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=system_prompt,      # <-- NEW: the system prompt
    messages=[
        {"role": "user", "content": user_message}
    ]
)
```

This is almost identical to Project 1, with one addition: the `system=` parameter. Notice it's NOT inside the `messages` list — it's a separate top-level parameter.

### Part 6: Saving to File

```python
if args.output:
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output_content)
```

`"w"` mode writes to a file. If the file already exists, it will be overwritten. If it doesn't exist, it will be created.

---

## 5. Sample Output

Running: `python smart_notes.py --file sample_notes.txt`

```
Summarizing file: sample_notes.txt (1823 characters)

Sending to Claude for summarization...
Please wait...

============================================================
           SMART NOTES SUMMARY
============================================================

## Summary
Successful software projects require upfront planning that includes clear problem definitions, stakeholder alignment, and breaking work into manageable tasks. Common pitfalls like vague goals, poor estimation, and inadequate communication can be avoided with deliberate planning practices.

## Key Points
- Define success with specific, measurable goals before writing any code
- Break large tasks into 1-2 day pieces and multiply your time estimates by 1.5-2x to account for unexpected problems
- Establish regular communication rhythms (like daily standups) to surface blockers early

## Action Item
Before starting your next project, write a one-page document with a specific success metric, a stakeholder list, and a first-pass task breakdown.

============================================================

Tokens used: 487 input, 142 output

Done!
```

---

## 6. Real World Use Cases

### Example 1: Meeting Notes Automation
A company has 20 managers who each attend 5-10 meetings per week. After each meeting, someone has to type up notes and action items and email them to the team. This takes 30 minutes per meeting — about 3 hours per manager per week.

An engineer builds a simple tool: the meeting notetaker uploads their raw, stream-of-consciousness notes to a Slack command, the command calls a script like `smart_notes.py`, and Claude extracts the structured summary and action items and posts them back to the Slack channel. 3 hours saved per manager per week. With 20 managers, that's 60 hours of saved time per week — about 1.5 full-time employee equivalents. The ROI is obvious.

### Example 2: Legal Document Review
A law firm processes hundreds of contracts per month. Junior paralegals spend hours reading through each contract just to extract the key terms: payment amount, due dates, termination clauses. A simple summarizer tool with a carefully written system prompt that says "Extract: parties, payment terms, deadlines, and termination conditions" can do this initial extraction in seconds. The paralegals then only review Claude's output and check the important clauses, instead of reading every word of every contract.

### Example 3: Research and Competitive Intelligence
A product manager at a tech company needs to monitor competitor blogs, press releases, and tech articles every day to stay informed. They use a script that fetches each article, runs it through a summarizer with a system prompt like "Summarize this article in 3 bullet points focusing on product changes, pricing, or strategy shifts," and emails a digest every morning. What would take an hour to read each day now takes 5 minutes to scan.

---

## 7. Extend This Project

### Idea 1: Summarize in Different Styles
Add a `--style` flag that lets users choose:
- `--style brief` — 1 sentence only
- `--style detailed` — full paragraph form
- `--style bullets` — bullet points only
- `--style executive` — executive summary style

In your code, build the system prompt differently based on `args.style`:
```python
styles = {
    "brief": "Summarize in exactly 1 sentence.",
    "detailed": "Write a detailed 3-paragraph summary.",
    "bullets": "Respond with only bullet points, minimum 5.",
    "executive": "Write an executive summary suitable for a C-level audience."
}
system_prompt = f"You are a summarizer. {styles.get(args.style, styles['brief'])}"
```

### Idea 2: Process Multiple Files at Once
Add support for summarizing an entire folder of text files:
```python
import glob
files = glob.glob("notes_folder/*.txt")  # Find all .txt files in a folder
for filepath in files:
    # Read each file and summarize it, save output to matching output file
```

### Idea 3: Add a Word Count Target
Let users specify how long the summary should be:
```bash
python smart_notes.py --file report.txt --words 100
```

Update the system prompt to include: `"The summary should be approximately {args.words} words."` This teaches you how to build dynamic system prompts where the instructions change based on user input.

---

## 8. What You Learned

| Concept | What It Means |
|---------|--------------|
| System prompt | A behind-the-scenes instruction that gives Claude a role and rules before the conversation starts |
| argparse | Python's built-in library for handling command-line flags and arguments |
| CLI tool | A program controlled by typing commands in the terminal rather than clicking buttons |
| `with open(...)` | Python's safe way to open and work with files — automatically closes them when done |
| File modes | `"r"` = read, `"w"` = write/overwrite, `"a"` = append to end |
| `encoding="utf-8"` | How Python interprets bytes in files — UTF-8 handles all human languages |
| `args.flag` | How argparse makes command-line values available as Python variable attributes |
| `f.read()` | Reads an entire file's content into a single Python string |
| `"\n".join(list)` | Joins a list of strings into one string with newlines between each item |
| `default=None` | When a CLI flag is optional, `None` is the default value if the user doesn't provide it |
| Structured output | Using the system prompt to force Claude's response into a predictable format |
| `len(string)` | Returns the number of characters in a string |
| String slicing `[:60]` | Takes characters from position 0 to 60 — useful for previewing long strings |

---

## 9. Quiz Questions

Test yourself before moving on to Project 3!

**Question 1:** What is the difference between a system prompt and a user message? Why would you use a system prompt?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** A user message is the text of the conversation — what you're saying to Claude right now. A system prompt is a set of background instructions given to Claude before the conversation starts. The user never sees the system prompt; it shapes Claude's behavior throughout the conversation. You use a system prompt when you want Claude to always act a certain way — like always responding in a specific format, always playing a specific role (customer support agent, doctor, code reviewer), or always following specific rules (only answer cooking questions). In this project, we used the system prompt to force Claude to always respond with the same structured format: Summary, Key Points, Action Item.

</details>

---

**Question 2:** What happens if you run `python smart_notes.py --file myfile.txt` but `myfile.txt` doesn't exist? Walk through what the code does.

<details>
<summary>Click to reveal the answer</summary>

**Answer:** The code hits the `elif args.file:` block. Inside, the first thing it does is call `os.path.exists(args.file)`, which checks whether the file actually exists on disk. Since the file doesn't exist, `os.path.exists()` returns `False`, so `not os.path.exists()` is `True`. The `if` block runs, printing `"ERROR: File not found: myfile.txt"` and then calling `sys.exit(1)` to stop the program. The user sees a clear error message telling them to check the file path. Without this check, Python would throw a `FileNotFoundError` exception when trying to open the file — which is a harder error message for a beginner to understand.

</details>

---

**Question 3:** Why is structuring Claude's output (forcing it to always use `## Summary`, `## Key Points`, `## Action Item`) useful when building tools for companies?

<details>
<summary>Click to reveal the answer</summary>

**Answer:** When you're building a one-off personal tool, it doesn't matter much if Claude's output format varies — you're reading it yourself and you understand it either way. But when you're building a tool for a company, Claude's output often gets processed by more code downstream. For example, maybe after getting the summary you want to: (1) extract just the action items and create calendar events automatically, (2) store the summary in a database, (3) display only the key points in a UI dashboard. All of these require the output to be in a predictable, consistent format. If Claude sometimes writes "Action Items:" and sometimes writes "Next Steps:" and sometimes writes "To Do:", your code that looks for "Action Item" would break half the time. Structuring the output — by specifying the format in the system prompt — makes your code reliable and production-ready.

</details>
