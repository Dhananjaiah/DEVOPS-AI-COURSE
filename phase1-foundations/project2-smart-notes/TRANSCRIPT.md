# Project 2: Coaching Session Transcript
## "Smart Notes" — CLI Summarizer with System Prompts

**Session Type:** Live tutoring session (follow-up to Project 1)
**Student:** Alex (just completed Project 1 — Hello AI)
**Coach:** Jamie
**Duration:** ~55 minutes

---

**[Session begins. Alex has Project 1 still open in VS Code and looks confident compared to last session.]**

---

**Jamie:** Welcome back! How did you feel after Project 1?

**Alex:** Really good actually! I showed my roommate and they were kind of amazed. I ran it a few times with different questions. I also tried your suggestion of making it loop with user input.

**Jamie:** That's awesome — you actually went and experimented. That's exactly the right mindset. Did the loop work?

**Alex:** Mostly! I got it working but then realized I didn't know how to stop the loop gracefully. It just kept asking forever until I hit Ctrl+C.

**Jamie:** Ctrl+C is totally valid — that's how developers force-stop programs all the time. But you're right, it's better to have a clean exit. We'll see a proper way to do that today with the `while True / break` pattern. Ready to look at Project 2?

**Alex:** Yeah, let's do it.

**Jamie:** Alright. Here's the upgrade from Project 1. In Project 1, the question was hardcoded — it never changed. And the user had no way to tell the program what they wanted without editing the code. Today we fix both of those things.

**Alex:** I noticed the new file uses `argparse`. I saw that word in the code but I don't know what it means.

**Jamie:** Let's start there. Do you know what a CLI is?

**Alex:** Command line interface?

**Jamie:** Exactly right. And you've been using the command line this whole time — typing commands in your terminal. A CLI tool is a program you control entirely from the terminal by typing commands and flags. You've used them before — have you ever typed something like `git commit -m "my message"` or `pip install -r requirements.txt`?

**Alex:** Oh yeah, `-r` is a flag! Like `-r requirements.txt` tells pip which file to read.

**Jamie:** Perfect. You already understood CLI flags intuitively! `argparse` is how you add that same feature to your own Python programs. You define flags like `--text` or `--file`, and then in the code you can read what the user typed for those flags. It turns your script from a simple file you run into a real tool.

**Alex:** That's actually really cool. So I could make `python smart_notes.py --file meeting_notes.txt` and it reads that specific file?

**Jamie:** Exactly. And `python smart_notes.py --help` will print usage instructions automatically. argparse generates that for free. It's one of those things that makes your tool feel professional.

**Alex:** Okay, I want to understand the system prompt thing. In Project 1 we just had messages. What's different here?

**Jamie:** Great timing — that's the most important new concept in this project. Let me use an analogy. Imagine you just hired a new assistant at work. On their first day, you sit down with them and say: "Your job is to summarize meeting notes. Always give me exactly three bullet points. Keep it under 100 words. Don't include your own opinions, just facts. Is that clear?" That's a system prompt — it's the briefing you give before the work starts.

**Alex:** Oh! So it's like giving Claude a job description.

**Jamie:** Precisely. The system prompt says who Claude is, what its rules are, and often what format it should respond in. The user message is the actual work — "here's today's meeting notes, please process them." The system prompt is always there in the background.

**Alex:** And the user never sees the system prompt?

**Jamie:** The end user doesn't — it's behind the scenes. Though if you're building the tool yourself, you obviously wrote it. This is actually a big part of prompt engineering — the craft of writing system prompts that reliably produce the output you want.

**Alex:** What do you mean reliably?

**Jamie:** If your system prompt just says "summarize this" — Claude might give you a paragraph one time, bullet points another time, a numbered list another time. If your tool needs to display the output in a specific way — say, only show the action items — inconsistent format breaks everything. So you write the system prompt to force a specific structure every time. Look at the one in smart_notes.py:

```
You are a professional note-taker and summarizer.
Always respond with EXACTLY this structure:
## Summary
[2-sentence summary]
## Key Points
- [point]
- [point]
- [point]
## Action Item
[one action item]
```

**Alex:** It tells Claude exactly what format to use. Like a template.

**Jamie:** Exactly. And because we say "EXACTLY this structure," Claude will follow it very closely. This is called structured output — getting an AI to produce consistent, machine-readable (or at least predictably formatted) responses.

**Alex:** Okay, I want to try running it. Let me set up the venv first.

**Jamie:** Go for it. What's the first step?

**Alex:** Navigate to the project2 folder, create venv with `python -m venv venv`, activate it with `venv\Scripts\activate`, then `pip install -r requirements.txt`. And make a `.env` file.

**Jamie:** Excellent. You remembered all the steps from memory. Go ahead.

**Alex:** [5 minutes pass] ...Okay, I activated venv, installed everything, copied `.env.example` to `.env`... and I already have my API key so I just pasted it in. Can I run it?

**Jamie:** Do it! Try: `python smart_notes.py --file sample_notes.txt`

**Alex:** Running... "Summarizing file: sample_notes.txt (1823 characters)"... "Sending to Claude for summarization... Please wait..." and then... oh it's printing the summary! It says "SMART NOTES SUMMARY" with the borders... and it gave me a Summary, Key Points, and Action Item!

**Jamie:** How does the format look?

**Alex:** Really clean! And it matches exactly the format in the system prompt. The Summary is two sentences, there are three key points, and there's an action item at the bottom.

**Jamie:** That's the power of structured output. Now try passing text directly. Type: `python smart_notes.py --text "Python is a programming language that is easy to learn. It is used in AI and web development."`

**Alex:** Running... okay it worked! Much shorter summary because the input was shorter. And the tokens are way lower — 134 input, 72 output.

**Jamie:** Notice how the token count scales with input size. Short input, short output, low cost. That's good intuition to build. Now try interactive mode — just run `python smart_notes.py` with no arguments.

**Alex:** Running... it says "No --text or --file argument provided. Please type or paste your text below. When you're done, press Enter twice to submit." Let me type something...

[Types: "Today we launched the new website. The launch went smoothly. We got 200 new signups in the first hour. The marketing team is happy. Next step is to monitor server performance."]

**Alex:** I pressed Enter after that... nothing happened.

**Jamie:** You need to press Enter one more time on a completely blank line. That's the "two Enters" signal. Try it.

**Alex:** Oh! Pressing Enter again on an empty line... it sent! And got a response. That's a smart trick — blank line = done.

**Jamie:** It's a classic CLI convention. Many tools use it for multi-line input. Alright, now try the `--output` flag: `python smart_notes.py --file sample_notes.txt --output my_summary.txt`

**Alex:** Running... it printed the summary AND says "Summary saved to: my_summary.txt". Oh cool, there's a new file in my folder now! Opening it... yep, the summary is in there with all the metadata.

**Jamie:** Now you have a tool that can programmatically process files and save output. That's a real workflow automation tool. Imagine a cron job running this on 50 documents overnight.

**Alex:** What's a cron job?

**Jamie:** A scheduled task — you tell your server "run this script every night at 2am." We'll cover that in the DevOps section. For now, just know that CLI tools like this one are what makes automation possible. If the user had to click a button, you couldn't automate it. A command-line tool can be automated.

**Alex:** Ohh that's why CLIs are so important! It's not just for nerds who don't like GUIs — it's because GUIs can't be automated easily.

**Jamie:** That's one of the best insights you'll get from this whole course. Say that again so it sticks.

**Alex:** CLIs are important because they can be automated. You can put them in scripts, scheduled tasks, and pipelines. A GUI requires a human to click.

**Jamie:** Write that down. Seriously. Okay, I want you to look at the code — specifically the `while True` loop for interactive mode. Can you explain what's happening?

**Alex:** Let me look... okay so `lines = []` creates an empty list. Then `while True:` starts a loop. Each time through the loop, `line = input()` waits for the user to type something. If `line == ""` — if they typed nothing, just pressed Enter — then `break` exits the loop. Otherwise `lines.append(line)` adds the line to the list. Then after the loop, `"\n".join(lines)` joins all the lines.

**Jamie:** Perfect explanation. What does `break` do?

**Alex:** Exits the loop. So if `while True` would loop forever, `break` is the escape hatch.

**Jamie:** Exactly. Python loops can't stop themselves by default when you write `while True` — you have to explicitly tell them to stop. That's what `break` does. There's also `continue` which skips the rest of the current loop iteration and goes back to the top. You don't use it here, but it's good to know.

**Alex:** What about `lines.append(line)` — what's `append`?

**Jamie:** `append` is a method on Python lists that adds a new item to the end. If `lines = ["hello"]` and you call `lines.append("world")`, now `lines = ["hello", "world"]`. It's how you build a list one item at a time.

**Alex:** And `"\n".join(lines)` — what's the `\n`?

**Jamie:** `\n` is a newline character. It's invisible, but it tells Python "go to the next line here." When you have a list of lines like `["line1", "line2", "line3"]` and you join them with `"\n"`, you get: `"line1\nline2\nline3"` — which when printed displays as three separate lines.

**Alex:** Oh, so `join` is the opposite of `split`?

**Jamie:** Exactly! Great connection. `"hello world".split(" ")` gives you `["hello", "world"]`. And `" ".join(["hello", "world"])` gives you `"hello world"` back.

**Alex:** Okay that's a really useful pattern. Can I ask about file reading? What's the `encoding="utf-8"` for?

**Jamie:** Good question. Text files aren't stored as text in a computer — they're stored as numbers (bytes). "Encoding" is the rules for translating those numbers back into characters. There are different encoding systems. ASCII was the original but it only handled English letters. UTF-8 can handle characters from every human language — Chinese, Arabic, French accents, emojis. If you use the wrong encoding, special characters turn into garbage or your program crashes. UTF-8 is the safe default for almost everything.

**Alex:** Makes sense. One more thing — the `os.path.exists()` check. Why do we check that before opening the file?

**Jamie:** Try removing that check and running the program with a file that doesn't exist. What do you think would happen?

**Alex:** A crash?

**Jamie:** Python would throw a `FileNotFoundError` exception. The error message is something like `[Errno 2] No such file or directory: 'fakefile.txt'`. It's functional — it tells you the file doesn't exist — but it's unfriendly. Our check gives a cleaner, more helpful message. This is the difference between code that technically works and code that's pleasant to use.

**Alex:** "Defensive programming" — you mentioned that in Project 1 too. Check for problems before they cause confusing errors.

**Jamie:** Exactly. You're building the vocabulary. Quiz time?

**Alex:** Let's go.

**Jamie:** Question 1: If a user runs `python smart_notes.py` with no flags, what happens step by step?

**Alex:** The `if args.text:` check is False because they didn't give `--text`. The `elif args.file:` check is also False. So we fall to the `else:` block. It prints a message telling the user to type their text. Then the `while True` loop runs, collecting lines until they press Enter twice. Then `input_text` is set to all those lines joined together.

**Jamie:** Excellent. Question 2: What would happen if you forgot `system=system_prompt` in the API call?

**Alex:** Claude would still respond, but without the formatting instructions. So the summary might come back as a paragraph, or in a different structure each time. It wouldn't reliably follow the Summary/Key Points/Action Item template.

**Jamie:** Correct. Claude would try its best to summarize, but without explicit formatting rules, it improvises. Question 3: In the `open()` call, what's the difference between mode `"r"` and mode `"w"`?

**Alex:** `"r"` is read — you're reading an existing file. `"w"` is write — you're creating or overwriting a file. We use `"r"` to read the input file and `"w"` to write the output file.

**Jamie:** All three right. You're getting it. One last thing before I let you go — look at the line where we do the file open for writing: `with open(args.output, "w", encoding="utf-8") as f:`. What happens if `args.output` already exists as a file?

**Alex:** Oh... write mode overwrites? So it would delete the old content and write the new content?

**Jamie:** Exactly. `"w"` mode is destructive — it starts the file fresh. If you wanted to ADD to an existing file without deleting what's there, you'd use `"a"` for append mode. We don't do that here, but it's useful to know.

**Alex:** Okay, I think I've got this project down. What's Project 3?

**Jamie:** Project 3 is where things get really exciting — you'll build a RAG system. RAG stands for Retrieval-Augmented Generation. You'll load a document, and then users can ask questions about it in a conversation. Claude answers based on the document's content.

**Alex:** Oh, like how some chatbots can answer questions about specific company documents? Like "What's our vacation policy?"

**Jamie:** Exactly! That's the core technology behind almost every "chat with your documents" product. You'll use a database called ChromaDB to store and search through document chunks. It sounds complex but we'll take it step by step.

**Alex:** That sounds actually really useful. I want to build that.

**Jamie:** You will. Great session today. You learned system prompts, argparse, file I/O, while loops, and the philosophy of why CLIs matter for automation. Each one of those is something you'll use in real engineering work. See you in Project 3.

**Alex:** Thanks, Jamie! See you then.

---

**[End of Session]**

**Session Summary:**
- Covered: system prompts, argparse, CLI tools, file reading/writing, while loops, break, list.append(), string joining, defensive programming with os.path.exists()
- Key insight from student: "CLIs are important because they can be automated — a GUI requires a human to click"
- Common confusion resolved: why blank-line-Enter triggers submission in interactive mode
- All three quiz questions answered correctly
- Student confidence level: 8/10 — visibly more comfortable with Python fundamentals
- Next session: Project 3 — Ask My Doc (RAG, ChromaDB, vector embeddings)
