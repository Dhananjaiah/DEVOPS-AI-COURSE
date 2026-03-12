# Environment Setup Guide — Start Here

> This guide sets up your computer from absolute scratch. Follow every step in order.

---

## What You're Installing

| Tool | What It Is | Why You Need It |
|------|-----------|----------------|
| Python | The programming language | Runs all our code |
| pip | Python's package installer | Installs libraries like Claude SDK |
| VS Code | Code editor | Where you write code |
| Git | Version control | Saves your work, optional but recommended |

---

## STEP 1 — Install Python

### Download
1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.12.x"** button
3. Run the downloaded installer

### CRITICAL Installation Setting
On the first installer screen, you will see a checkbox at the bottom:
```
☐ Add Python to PATH
```
**CHECK THIS BOX** before clicking Install Now. This is the #1 beginner mistake. Without it, your terminal won't find Python.

4. Click **"Install Now"**
5. Wait for it to finish

### Verify Python installed
Open Command Prompt (press `Windows key + R`, type `cmd`, press Enter):
```bash
python --version
```
Expected output:
```
Python 3.12.x
```
If you see this, Python is installed correctly.

---

## STEP 2 — Install VS Code

1. Go to **https://code.visualstudio.com/**
2. Click **"Download for Windows"**
3. Run the installer, accept all defaults
4. Open VS Code

### Install the Python Extension
1. Click the square icon in the left sidebar (looks like 4 squares — Extensions)
2. In the search box type: `Python`
3. Find the one by **Microsoft** (millions of installs)
4. Click **Install**

### Open the Terminal in VS Code
Press **Ctrl + `** (backtick key, top-left of keyboard, above Tab).
A terminal panel opens at the bottom — this is where you run commands.

---

## STEP 3 — Get Your Claude API Key

Claude (by Anthropic) is the AI we'll use. You need an API key — think of it as a password that lets your code talk to Claude.

1. Go to **https://console.anthropic.com/**
2. Sign up for a free account
3. In the left menu, click **"API Keys"**
4. Click **"Create Key"**
5. Name it: `ai-course`
6. Copy the key — it starts with `sk-ant-...`
7. **Save it somewhere safe** — you only see it once!

---

## STEP 4 — Get Your Tavily API Key (for web search projects)

Tavily gives your AI agents the ability to search the web.

1. Go to **https://tavily.com/**
2. Sign up for a free account
3. Go to your dashboard and copy your API key

---

## STEP 5 — Create Your Course Folder

In the VS Code terminal:
```bash
# Go to your course folder
cd C:/Users/techi/Downloads/2026/DEVOPS-AI-COURSE
```

---

## STEP 6 — Per-Project Setup Pattern

Every project follows this same setup pattern:

```bash
# 1. Go into the project folder
cd phase1-foundations/project1-hello-ai

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it (Windows)
venv\Scripts\activate

# You'll see (venv) appear in your terminal — means it's active

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create your .env file
copy .env.example .env
# Then open .env and fill in your real API keys
```

---

## Understanding Virtual Environments

A **virtual environment** (`venv`) is like a separate clean room for each project.

Without it: all your projects share the same set of installed tools — updating one can break another.

With it: each project has its own tools, isolated from everything else.

**Rule:** Always activate your venv before working:
```bash
# Windows
venv\Scripts\activate

# You know it's active when you see:
(venv) C:\Users\techi\...>
```

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `python` not found | Reinstall Python, check "Add to PATH" |
| `pip` not found | Run: `python -m pip install --upgrade pip` |
| `venv\Scripts\activate` fails | Run PowerShell as admin: `Set-ExecutionPolicy RemoteSigned` |
| API key error | Check your `.env` file has no spaces around the `=` sign |
| Module not found | Make sure venv is activated, then `pip install -r requirements.txt` |

---

## Folder Structure Overview

```
DEVOPS-AI-COURSE/
├── README.md                    ← Course overview
├── SETUP.md                     ← This file
├── PROGRESS.md                  ← Track your progress
├── phase1-foundations/
│   ├── project1-hello-ai/
│   ├── project2-smart-notes/
│   └── project3-ask-my-doc/
├── phase2-agents-tools/
│   ├── project4-web-research-agent/
│   ├── project5-file-manager-agent/
│   └── project6-multi-step-task-agent/
├── phase3-memory-context/
│   ├── project7-personal-assistant/
│   ├── project8-customer-support-bot/
│   └── project9-knowledge-base-agent/
├── phase4-multi-agent/
│   ├── project10-research-writer-team/
│   ├── project11-code-review-pipeline/
│   └── project12-data-analysis-crew/
└── phase5-real-world/
    ├── project13-hr-recruiter/
    ├── project14-sales-pipeline/
    ├── project15-enterprise-rag/
    └── project16-devops-agent/
```

---

Ready? Start with [Project 1 — Hello AI](./phase1-foundations/project1-hello-ai/README.md).
