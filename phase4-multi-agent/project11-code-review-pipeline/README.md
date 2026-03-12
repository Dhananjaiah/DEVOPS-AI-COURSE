# Project 11: Automated Code Review Pipeline

## What You Are Building

An automated code review system that takes Python code and runs it through three specialized AI agents:

1. **Code Reviewer** — reads your code and identifies bugs, security vulnerabilities, performance problems, and style issues with specific line numbers and severity levels
2. **Test Writer** — reads the code and the review, then writes pytest test cases specifically designed to catch the bugs that were found
3. **Code Fixer** — reads the original code, the review, and the tests, then produces a corrected version that addresses all CRITICAL and WARNING issues

Plus an **Approval Agent** that verifies the fix actually resolved the critical issues, with a retry loop if it did not.

This is the kind of system that DevOps teams are deploying in CI/CD pipelines today. Every pull request gets an AI code review. Every security issue gets flagged before it reaches production.

---

## The Security Problem You Will Discover

The sample code (`sample_buggy_code.py`) contains real security vulnerabilities that exist in real company codebases. The most important one you will learn about today is **SQL injection**.

### What Is SQL Injection?

SQL injection is the number one security vulnerability on the OWASP Top 10 list (the industry's official ranking of the most dangerous software flaws). It has been on that list since 2003. Despite being over 20 years old and extremely well-documented, it is still found in production code at major companies every year.

Here is the vulnerable pattern from the sample code:

```python
# DANGEROUS — do not do this
query = "SELECT * FROM users WHERE username = '" + username + "'"
cursor.execute(query)
```

If a normal user provides `username = "alice"`, the query becomes:
```sql
SELECT * FROM users WHERE username = 'alice'
```

That is fine. But what if an attacker provides:
`username = "' OR '1'='1"`?

The query becomes:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1'
```

Since `'1'='1'` is always true, this returns EVERY user in the database. The attacker just bypassed authentication.

Even worse, an attacker could provide:
`username = "'; DROP TABLE users; --"`

The query becomes:
```sql
SELECT * FROM users WHERE username = ''; DROP TABLE users; --'
```

This deletes your entire user table. That is SQL injection.

### The Fix (Always Use Parameterized Queries)

```python
# SAFE — use parameterized queries
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))  # The ? is replaced safely by sqlite3
```

The database driver handles the escaping. The user's input can never become part of the SQL structure. This is the correct pattern and your Code Fixer agent will apply it.

---

## The Three Severity Levels

The Code Reviewer categorizes issues into three levels:

### CRITICAL
Issues that must be fixed before any deployment. These cause:
- Security vulnerabilities (SQL injection, authentication bypass, data exposure)
- Runtime crashes (division by zero, null pointer errors)
- Data corruption or loss

No code with CRITICAL issues should ever reach production.

### WARNING
Issues that should be fixed but are not immediately dangerous:
- Performance problems (O(n²) algorithms, missing pagination)
- Missing input validation (could lead to bad data in the database)
- Poor error handling (swallowing exceptions)
- Unused imports (code smell, increases maintenance burden)

### INFO
Minor suggestions:
- Style improvements
- Documentation gaps
- Minor readability issues

These are nice-to-have fixes, not requirements.

---

## How This Fits Into DevOps CI/CD

CI/CD stands for Continuous Integration / Continuous Deployment. It is the practice of automatically running a series of checks every time a developer pushes new code. The typical CI/CD pipeline looks like this:

```
Developer pushes code
        ↓
[Automated Tests Run]    ← pytest, unit tests
        ↓
[Linting and Style]      ← flake8, black
        ↓
[Security Scan]          ← bandit, safety
        ↓
[AI Code Review]         ← This project!
        ↓
[Deploy to Staging]
        ↓
[Deploy to Production]
```

By adding an AI code review step to the pipeline, teams catch:
- Security vulnerabilities before they reach production
- Bugs that manual review might miss
- Performance issues early when they are cheap to fix
- Consistency violations that accumulate into technical debt

---

## Real-World AI Code Review Tools

You are not the first to think of this. Several companies have built this exact product:

### GitHub Copilot Code Review
GitHub (owned by Microsoft) uses AI to review pull requests. It comments directly on code in the GitHub interface, explaining issues and suggesting fixes.

### CodeRabbit
A service that automatically reviews every pull request for security issues, bugs, and best practices. Used by thousands of open source projects.

### Snyk
Specializes in security scanning. Finds known vulnerabilities in both your code and your dependencies (the packages you import).

### SonarQube with AI
Traditional static analysis tool that has added AI-powered explanations to help developers understand and fix the issues it finds.

What you are building today is a simplified but functionally equivalent version of these tools.

---

## Architecture Deep Dive

### The Pipeline Flow

```
[Original Code]
      │
      ▼
[Review Node]──────────────────────────────────────────
      │                                               │
      │  Writes: state["review"]                      │
      ▼                                               │
[Test Node]                                           │
      │                                               │
      │  Reads: state["original_code"],              │
      │         state["review"]                       │
      │  Writes: state["test_code"]                   │
      ▼                                               │
[Fix Node]─────────────────────────────────┐          │
      │                                    │ (retry)  │
      │  Reads: state["original_code"],    │          │
      │         state["review"],           │          │
      │         state["test_code"]         │          │
      │  Writes: state["fixed_code"]       │          │
      ▼                                    │          │
[Approve Node]                             │          │
      │                                    │          │
      │  Checks: all CRITICAL issues fixed?│          │
      │                                    │          │
      ├──── APPROVED ────────────────────────────────▼
      │                                              │
      └──── NEEDS_FIX ───────────────────────────────┘
             (max 2 cycles)
                │
                ▼
         [Output Node]
```

### Why Test Generation Matters

Writing tests before fixing code is a practice called **Test-Driven Development (TDD)**. The idea is:
1. Write a test that fails on the buggy code
2. Fix the code
3. Run the test — it should now pass

By having the Test Writer agent generate tests BEFORE the Code Fixer runs, you get:
- A clear specification of what "fixed" means
- Automated verification that the fix actually worked
- Regression tests that prevent the same bug from returning later

In production, these generated tests would be committed to the repository alongside the fixed code.

---

## Code Walkthrough

### System Prompts Define Expertise

Each agent's system prompt gives it a specific perspective:

The **Reviewer's** prompt says:
```
"You are a senior software engineer doing code review. Analyze code for:
bugs, security issues, performance problems, code style issues.
Be specific about line numbers and issues."
```

This makes Claude adopt the mindset of a security-conscious senior engineer. It looks for exactly the categories mentioned.

The **Test Writer's** prompt says:
```
"You are a QA engineer. Given code and a review, write pytest test cases
that would catch the bugs found in the review."
```

This makes Claude think like a QA engineer — not "how do I make this work?" but "how do I prove this is broken?"

The **Fixer's** prompt says:
```
"You are a code fixer. Given original code, a review, and test cases,
produce fixed code that addresses all CRITICAL and WARNING issues."
```

This makes Claude focus on targeted improvements rather than rewrites. It knows exactly what needs to change.

### The Fix-Verify Loop

```python
def should_refix(state: CodeReviewState) -> str:
    status = state.get("approval_status", "NEEDS_ANOTHER_FIX")
    if status == "APPROVED":
        return "output"
    elif status == "MAX_CYCLES_REACHED":
        return "output"    # Circuit breaker
    else:
        return "fix"       # Back to the fixer
```

The routing function returns a string. LangGraph uses that string to look up the next node in the mapping you provided when you called `add_conditional_edges`. If the fixer did not resolve all critical issues, we go back and try again.

---

## Project File Structure

```
project11-code-review-pipeline/
├── code_review_pipeline.py    # Main multi-agent pipeline
├── sample_buggy_code.py       # Realistic buggy Python file for testing
├── requirements.txt           # Python dependencies
├── .env.example               # Template for API keys
├── .env                       # Your actual API keys (never commit this!)
├── review_output/             # All pipeline outputs saved here
│   ├── *_review_*.md          # Code review reports
│   ├── *_tests_*.py           # Generated pytest files
│   ├── *_fixed_*.py           # Fixed code versions
│   └── *_summary_*.md         # Pipeline run summaries
├── README.md                  # This file
└── TRANSCRIPT.md              # Session transcript
```

---

## Setup and Running

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Note: This project does NOT require Tavily — only the Anthropic API key is needed.

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 3: Run With the Sample Buggy Code

```bash
python code_review_pipeline.py sample_buggy_code.py
```

### Step 4: Run With Your Own Code

```bash
python code_review_pipeline.py path/to/your_code.py
```

The pipeline works on any Python file. Try it on something from a previous phase of this course.

---

## What to Expect in the Output

### Terminal Output

```
🔬 CODE REVIEW PIPELINE 🔬

This pipeline uses THREE specialized AI agents:
   1. 🔍 Code Reviewer  — finds bugs, security issues, performance problems
   2. 🧪 Test Writer    — writes pytest tests for each issue found
   3. 🔧 Code Fixer     — fixes all CRITICAL and WARNING issues
   4. ✅ Approval Agent — verifies the fix is complete

Reviewing file: sample_buggy_code.py
Code size: 147 lines

============================================================
🔍 Code Reviewer analyzing code...
   File: sample_buggy_code.py
============================================================
   Code size: 147 lines

📋 Review Summary:
   CRITICAL issues: 5
   WARNING issues:  4
   INFO issues:     2
```

### The Review Report

The review will identify each SQL injection point with its line number:

```markdown
## Code Review Report

### Summary
This user management module contains multiple critical SQL injection
vulnerabilities across all database functions. Every database query
uses string concatenation instead of parameterized queries...

### Issues Found

**[CRITICAL] SQL Injection in get_user_by_username (Line 38)**
- Problem: Username is directly concatenated into SQL query string
- Risk: Attacker can manipulate query to bypass authentication or dump database
- Fix: Use parameterized queries: cursor.execute("... WHERE username = ?", (username,))

**[CRITICAL] Division by Zero in calculate_average_score (Line 57)**
- Problem: No check for empty list before dividing
- Risk: ZeroDivisionError crash when empty list is passed
- Fix: Add `if not scores: return 0` check before the division
```

### The Generated Tests

The Test Writer produces real pytest tests:

```python
import pytest

class TestCodeReview:
    """Tests designed to catch all CRITICAL and WARNING issues."""

    def test_sql_injection_prevention_get_user(self):
        """
        Test that get_user_by_username uses parameterized queries.
        SQL injection attack string should not cause unexpected behavior.
        """
        # This would have been a critical vulnerability in the original code
        malicious_input = "' OR '1'='1"
        # The fixed function should handle this safely without crashing
        # ...

    def test_calculate_average_empty_list(self):
        """
        Test that calculate_average_score handles empty list without crashing.
        Original code would raise ZeroDivisionError.
        """
        from fixed_code import calculate_average_score
        result = calculate_average_score([])
        assert result == 0, "Empty list should return 0, not crash"
```

---

## Running the Generated Tests

After the pipeline completes, you will find the test file in `review_output/`. To run it:

```bash
# Install pytest if you do not have it
pip install pytest

# Run the generated tests
pytest review_output/sample_buggy_code_tests_*.py -v
```

Expected output:
```
test_sql_injection_prevention_get_user PASSED
test_calculate_average_empty_list PASSED
test_find_duplicates_performance PASSED
test_create_user_input_validation PASSED
...

5 passed in 0.23s
```

---

## The DevOps Integration

### Integrating Into GitHub Actions

Here is how you would add this to a real CI/CD pipeline using GitHub Actions:

```yaml
# .github/workflows/ai-code-review.yml
name: AI Code Review

on:
  pull_request:
    branches: [main, develop]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run AI Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Get list of changed Python files
          git diff --name-only origin/main HEAD | grep '\.py$' | while read file; do
            python code_review_pipeline.py "$file"
          done

      - name: Upload Review Results
        uses: actions/upload-artifact@v3
        with:
          name: code-review-results
          path: review_output/
```

With this in place, every pull request automatically gets a code review from your three AI agents. The review results are uploaded as artifacts that the reviewer can inspect.

### Fail the Build on CRITICAL Issues

You can make the pipeline fail CI/CD if critical issues are found:

```python
# In output_node, check if any critical issues remain in fixed code
if "CRITICAL" in state.get("review", "") and state.get("approval_status") != "APPROVED":
    print("CRITICAL issues not resolved — failing build")
    sys.exit(1)  # Non-zero exit code causes CI/CD to fail
```

This enforces security standards automatically — no CRITICAL issues can slip through.

---

## Real World Context

### The Cost of Security Vulnerabilities

Understanding why this matters:

- The average cost of a data breach in 2023 was **$4.45 million** (IBM Security report)
- SQL injection attacks are responsible for approximately **65%** of web application attacks
- The average time to identify a security breach is **204 days**
- Most breaches involve vulnerabilities that were known and preventable

An AI code review system that catches SQL injection before deployment pays for itself after preventing a single breach.

### Companies Using AI for Security

**Netflix** uses AI to automatically scan all code changes for security vulnerabilities before they are merged. They call it "automated security guardrails."

**Shopify** has integrated AI code review into their pull request workflow. Every code change gets an automated first pass before human reviewers look at it.

**Google** uses AI to help identify bugs in open source software through their OSS-Fuzz program — a form of automated testing similar to what you built today.

---

## Extend This Project

### Add a Security-Specific Agent

Create a dedicated security agent that only looks for security issues:

```python
SECURITY_AGENT_PROMPT = """You are a security engineer specializing in OWASP Top 10
vulnerabilities. When reviewing code, look ONLY for:
1. SQL/NoSQL injection
2. Authentication and session management flaws
3. Sensitive data exposure
4. Access control issues
5. Security misconfiguration
6. Cryptographic failures

Rate each finding by CVSS score (0-10) and provide the OWASP category."""
```

### Add Complexity Analysis

Add an agent that analyzes code complexity:

```python
COMPLEXITY_AGENT_PROMPT = """You are a performance engineer. Analyze the algorithmic
complexity of each function. Identify any O(n²) or worse algorithms and suggest
more efficient alternatives. Calculate Big-O notation for each function."""
```

### Save Findings to a Database

Instead of text files, save the review findings to a SQLite database. Track which files have been reviewed, when, and what issues were found. Build a dashboard showing security trends over time.

### Integration With Git

Automatically run the pipeline on every changed file when you do `git commit`:

```python
# In .git/hooks/pre-commit
#!/bin/bash
# Get list of staged Python files
git diff --cached --name-only | grep '\.py$' | while read file; do
    python code_review_pipeline.py "$file"
done
```

---

## Key Concepts Learned

| Concept | Explanation |
|---------|-------------|
| SQL injection | Attacker manipulates database queries via unvalidated user input |
| Parameterized queries | Safe way to include user data in SQL using placeholders |
| CRITICAL/WARNING/INFO | Severity classification system for code issues |
| Test-Driven Development | Writing tests before/during fixing to verify corrections |
| CI/CD pipeline | Automated sequence of checks that run on every code change |
| Fix-verify loop | Run fix → check if fixed → repeat if not → cap with circuit breaker |
| OWASP Top 10 | Industry standard list of the 10 most critical security vulnerabilities |

---

## Common Issues

### "Error: ANTHROPIC_API_KEY not found"
Create a `.env` file with your API key. Do not just edit `.env.example` — that is the template.

### Pipeline takes a long time
Three agents plus the approval node means 4 Claude API calls minimum. Each call can take 15-30 seconds for large code files. Budget 60-120 seconds per run.

### Fixed code has syntax errors
The fixer wraps code in markdown code blocks. The output file includes the full response. If you want just the code, extract the content between ` ```python ` and ` ``` ` markers.

### Review finds no issues in good code
That is correct behavior. If you run the pipeline on already-correct code, the reviewer should report minimal issues and the approval should pass immediately.

---

## What Comes Next

In Project 12, you will build a **Data Analysis Crew** — three agents that work on a business dataset. They will clean the data, perform statistical analysis, and produce an executive business report. You will see how the same multi-agent pattern applies to data science and business intelligence workflows.

---

*Phase 4 | Project 11 of 12 | Multi-Agent Systems with LangGraph*
