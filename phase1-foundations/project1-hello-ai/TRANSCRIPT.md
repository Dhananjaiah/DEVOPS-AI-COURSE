# Project 1: Coaching Session Transcript
## "Hello AI" — Your First API Call

**Session Type:** Live tutoring session
**Student:** Alex (complete beginner, age 24, works in IT helpdesk, wants to move into AI engineering)
**Coach:** Jamie (senior AI engineer with 6 years experience)
**Duration:** ~50 minutes

---

**[Session begins via video call. Alex has VS Code open on their screen.]**

---

**Jamie:** Hey Alex! Ready to write your very first AI program today?

**Alex:** Yeah, I'm excited but also kind of nervous. I've never done real programming before. I mean, I've messed around with Python tutorials on YouTube but never built anything real.

**Jamie:** That nervousness is totally normal. Here's what I want you to know: by the end of today, you'll have a working program that talks to an actual AI. The same AI that millions of people pay to use. And you'll have built the connection yourself. Pretty cool, right?

**Alex:** That does sound cool. Okay. What do we do first?

**Jamie:** First, let me just give you a quick picture of what we're building today, so nothing feels mysterious. We're going to write a Python program. That program will send a message to Claude — that's Anthropic's AI — and print back the response in your terminal. Like texting a robot, but from code.

**Alex:** When you say "terminal," do you mean the black screen thing?

**Jamie:** Exactly! The black screen with the blinking cursor. On Windows it's called Command Prompt or PowerShell. On Mac it's called Terminal. Same concept — it's just a way to type commands directly to your computer instead of clicking buttons.

**Alex:** Got it. And this Claude — it's like ChatGPT?

**Jamie:** Very similar! Both are "large language models" — AI systems trained on enormous amounts of text. ChatGPT is made by OpenAI, Claude is made by Anthropic. We're using Claude because their API is well-designed and beginner-friendly. And both use the same concept: you send text in, you get text back.

**Alex:** What's an API? I keep hearing that word.

**Jamie:** Great question — let me give you the best analogy I know. You know how when you go to a restaurant, you don't walk into the kitchen yourself to cook your food? You talk to the waiter, the waiter goes to the kitchen, the kitchen makes the food, and the waiter brings it back to you.

**Alex:** Yeah...

**Jamie:** An API is the waiter. It's a middleman that lets your program talk to another service — in this case, Anthropic's AI — without you having to understand all the complicated stuff happening "in the kitchen." You send a request, the API handles everything, and you get a response back.

**Alex:** Oh! That actually makes sense. So when I call the API, I don't need to know how Claude actually works inside?

**Jamie:** Exactly. You don't need to understand the AI math. You just need to know how to format your request correctly — and that's what this project teaches. Alright, let's open the project folder. Can you navigate to it?

**Alex:** Yeah, one sec... okay I'm in `project1-hello-ai`. I can see the files: `hello_ai.py`, `requirements.txt`, `.env.example`, `README.md`.

**Jamie:** Perfect. Before we run anything, we need to do setup. Step one: create a virtual environment. Open your terminal, make sure you're in the project1 folder, and type: `python -m venv venv`

**Alex:** What's a virtual environment? Why do we need it?

**Jamie:** Another great question. Imagine you're working on two different projects. Project A needs version 1 of a tool. Project B needs version 2 of the same tool — and versions 1 and 2 aren't compatible. If you install both, they'll fight each other and one of the projects will break.

**Alex:** Oh, that sounds messy.

**Jamie:** It is! A virtual environment solves this by creating a private "bubble" for each project. Inside that bubble, you can install exactly the versions you need, and they won't interfere with other projects. It's like each project has its own personal toolbox.

**Alex:** Okay, that makes sense. Running it now... `python -m venv venv`... it just blinked and did nothing? Did it work?

**Jamie:** [laughs] Yes! In the terminal world, no news is usually good news. If something failed, you'd see a red error message. Since it just ran quietly, it worked. Check your folder — you should now see a new folder called `venv`.

**Alex:** Oh yeah! There it is. Okay cool. Now what?

**Jamie:** Now we activate it. On Windows type: `venv\Scripts\activate`

**Alex:** Okay... `venv\Scripts\activate`... it says `venv : File C:\Users\techi\...\venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`

**Jamie:** Ah! Welcome to your first Windows gotcha. Don't worry, this is super common. Windows has a security setting that blocks scripts by default. Open PowerShell as administrator — right-click on the PowerShell icon and choose "Run as administrator." Then type: `Set-ExecutionPolicy RemoteSigned` and press Enter, then type `Y` to confirm.

**Alex:** Okay... running as admin... typing that... it says "do you want to change the execution policy?" I pressed Y... okay done.

**Jamie:** Great. Now go back to your regular terminal (not the admin one) and try the activate command again.

**Alex:** `venv\Scripts\activate`... oh! It says `(venv)` at the beginning of my prompt now! Like `(venv) C:\Users\techi\...>`

**Jamie:** That's the sign! The `(venv)` prefix means your virtual environment is active. Now everything you install will go into that bubble. Run: `pip install -r requirements.txt`

**Alex:** Running... I see a bunch of stuff scrolling. "Collecting anthropic"... "Collecting python-dotenv"... it's downloading things. This is the tools we need?

**Jamie:** Exactly. `pip` is Python's package manager — its job is to download and install libraries. `requirements.txt` is a list of the libraries this project needs, and `pip install -r` reads that list and installs all of them.

**Alex:** Okay it finished! "Successfully installed anthropic-0.40.0 python-dotenv-1.0.0" and some other things.

**Jamie:** Perfect! Now the most important step: your API key. We need to create the `.env` file. Copy `.env.example` to `.env`. On Windows: `copy .env.example .env`

**Alex:** Done. Now I need to put my real API key in it?

**Jamie:** Yes. Go to `console.anthropic.com`, sign up or log in, click "API Keys" in the sidebar, create a new key, copy it — and paste it into the `.env` file replacing the placeholder text.

**Alex:** Okay... I'm at the website... creating a key... it says to copy it now because I'll never see it again?

**Jamie:** Right! Store it somewhere safe too, like a password manager. This is your private key — treat it like a password.

**Alex:** Got it... copied... opening the `.env` file in VS Code... okay I can see `ANTHROPIC_API_KEY=sk-ant-your-key-here`. I replaced that with my real key and saved.

**Jamie:** Great! Now let's look at the code before we run it. Open `hello_ai.py`. Read through the comments. What does line 1 say?

**Alex:** It says `# hello_ai.py` and then explains what the program does. Oh! The comments explain everything. Every single line has a comment!

**Jamie:** That's intentional for learning. In real production code, you wouldn't comment every line — you'd only comment the parts that aren't obvious. But while you're learning, comments on everything help you understand what's happening.

**Alex:** So the `#` symbol makes a comment? Python ignores it?

**Jamie:** Exactly. `#` tells Python "ignore everything on this line after this symbol." It's just for human readers. Use comments to leave notes to yourself and your teammates.

**Alex:** Okay I read through it... I think I understand most of it. The part where it says `messages=[{"role": "user", "content": my_question}]` — what's that square bracket thing?

**Jamie:** That's a Python list. A list is an ordered collection of items, wrapped in square brackets `[ ]`. Inside the list, each item is a dictionary — curly braces `{ }` with key-value pairs. So you have a list containing one dictionary. The dictionary has two keys: `"role"` and `"content"`. This is the format the Anthropic API expects.

**Alex:** Why does it need a list? We're only sending one message.

**Jamie:** Great observation! The API is designed for multi-turn conversations. In a real chatbot, you'd have a history of messages — user says something, Claude responds, user says something else, Claude responds again. All of those would be in the list. For our simple case, we only have one message, but it still needs to be in list format because that's what the API expects.

**Alex:** Oh that makes sense! Okay, I think I'm ready. Can I just run it?

**Jamie:** Go for it! Type `python hello_ai.py`

**Alex:** Okay... `python hello_ai.py`...

**[5 second pause]**

**Alex:** OH WOW! It printed stuff! Let me read... "API key loaded successfully!"... "Sending message to Claude..."... and then — holy cow — Claude actually answered! It says: "An AI agent is like a really smart helper that can think on its own and do tasks for you, like searching the internet, writing emails, or solving problems step by step. You give it a goal, and it figures out how to reach that goal all by itself without you having to tell it every tiny thing to do!"

**Jamie:** [laughs] Welcome to AI engineering! How does it feel?

**Alex:** That's insane! I just... made a program that talked to an AI? And it actually answered?

**Jamie:** You did. That's a real API call to a real AI model. You wrote every piece of that code. Look at the bottom — what does it say about token usage?

**Alex:** It says "Input tokens: 34, Output tokens: 58, Total tokens: 92."

**Jamie:** Perfect. So 34 tokens for the question, 58 for the answer. That's tiny — practically free. Now here's an important question: why do you think we see the token count?

**Alex:** Um... because it costs money? Like, that's how they charge you?

**Jamie:** Exactly right. Anthropic charges per token used. Knowing the token count helps you estimate costs. If you built a customer support bot that answers 10,000 questions per day, you'd want to know roughly how many tokens each answer uses so you can budget correctly.

**Alex:** Makes sense. So if I changed `max_tokens` to something really small, what would happen?

**Jamie:** Try it! Change `max_tokens=1024` to `max_tokens=10` and run it again.

**Alex:** Changing it... running... oh! The answer got cut off super short! It just says "An AI agent is like a really smart" and then it stopped.

**Jamie:** Perfect experiment! You just proved that `max_tokens` is a hard cap. The model stops generating the moment it hits that limit, even mid-sentence. Change it back to 1024 for the final version.

**Alex:** Done. Okay, let me ask you something — what if I forget to activate the virtual environment before running?

**Jamie:** Try it! Open a NEW terminal tab (don't close your current one), navigate to the project folder WITHOUT activating venv, and try `python hello_ai.py`.

**Alex:** Okay, new terminal... going to the folder... running without activating... it says: `ModuleNotFoundError: No module named 'anthropic'`

**Jamie:** There it is! Classic error. It can't find the `anthropic` library because you installed it INSIDE the venv, but this terminal session doesn't know about the venv. To fix it, you just activate the venv first. Go back to your other terminal where `(venv)` is showing and it works fine there.

**Alex:** Oh I see! The venv is like... it only exists in the terminal where you activated it?

**Jamie:** Exactly. Each terminal session is independent. Any time you start a new terminal, you need to activate the venv before running your project's code. Experienced developers have this as muscle memory — first thing when opening a project, they activate the venv.

**Alex:** Okay, that's really good to know. I'll remember that.

**Jamie:** Alright, quiz time! Three quick questions. First: What is `load_dotenv()` doing?

**Alex:** Um... it reads the `.env` file and... loads the values into Python's memory?

**Jamie:** Exactly right. And specifically, where in Python's memory does it put them?

**Alex:** Uhhhh... environment variables?

**Jamie:** Yes! It loads them as environment variables. After calling `load_dotenv()`, you can retrieve them using `os.getenv("VARIABLE_NAME")`. Great. Question two: If you removed the `if not api_key:` check, would the program still work?

**Alex:** If the API key is there... yeah? But if I forgot to set it up...

**Jamie:** Finish that thought.

**Alex:** It would crash eventually, but with a more confusing error. Like maybe it would get to the API call part and fail there with some weird message.

**Jamie:** Exactly! Without the early check, the error would happen deep inside the `anthropic` library with a less helpful error message. Our check makes it fail fast with a clear, human-friendly error message. That's good engineering practice. Last question: What does `[0]` mean in `response.content[0].text`?

**Alex:** It's getting the first item from a list? Because Python counts from zero?

**Jamie:** Perfect. You nailed all three. You're a natural.

**Alex:** Ha! I don't know about that. But I actually understand what the code is doing now. It's not magic anymore.

**Jamie:** That's the goal. Once you understand what each line does, you can modify it, debug it, and build on it. You're no longer just following instructions — you're actually programming.

**Alex:** What's next?

**Jamie:** Project 2 is called "Smart Notes." You'll build a command-line tool that takes notes or text files and summarizes them using Claude. You'll learn about system prompts — which let you give Claude a "personality" or role — and about argparse, which lets users control your program with command-line flags like `python smart_notes.py --file my_notes.txt`. These are concepts used in real production CLI tools at companies.

**Alex:** Ooh, that sounds useful. Like I could actually use that for my own notes!

**Jamie:** That's the idea! The best way to learn is to build things you'd actually want to use. See you in Project 2. And between now and then — experiment! Try changing the question, try changing max_tokens, try making a loop that asks multiple questions. Playing is how you learn fastest.

**Alex:** Will do. Thanks Jamie, this was awesome!

**Jamie:** Great work today. You shipped your first AI program. That's worth celebrating.

---

**[End of Session]**

**Session Summary:**
- Covered: virtual environments, API keys, `.env` files, imports, the Anthropic API call structure, tokens, f-strings, list indexing
- Common errors encountered: PowerShell execution policy, ModuleNotFoundError from missing venv activation
- Student confidence level: Started at 4/10, ended at 7/10
- Next session: Project 2 — Smart Notes (system prompts, argparse, CLI tools)
