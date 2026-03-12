# Session Transcript: Project 11 — Code Review Pipeline

**Course:** DevOps AI Course — Phase 4: Multi-Agent Systems
**Session Date:** Day 24 of the course
**Duration:** Approximately 90 minutes
**Student Background:** Completed Project 10 (Research-Writer Team)

---

## Session Start

**Instructor:** In Project 10, you built two agents that worked together on a content task. Today you are going to build three agents working on a DevOps task — automated code review. This is one of the most practically valuable things you can build with AI.

**Student:** Code review sounds familiar. I have done manual code reviews in pull requests on GitHub.

**Instructor:** Exactly. And you know how slow and inconsistent manual review can be. Some reviewers are thorough, some are not. Reviewers get tired. Junior reviewers miss security issues that senior engineers would catch. An AI system is always thorough, always consistent, and never gets tired.

**Student:** Does it actually find real security issues?

**Instructor:** Let's find out. Look at `sample_buggy_code.py`. What do you see?

*[Student reads the file...]*

**Student:** It is a user management module. Database queries, user creation, search functionality. It looks like normal company code to me.

**Instructor:** Look at line 38 specifically.

**Student:** `query = "SELECT * FROM users WHERE username = '" + username + "'"`... Oh. The username is just pasted directly into the SQL string.

**Instructor:** That is SQL injection. It is the number one web application security vulnerability according to OWASP. It has been the top vulnerability for over two decades. And it still appears in production code at major companies every single year.

**Student:** So an attacker could put SQL code inside the username?

**Instructor:** Exactly. If someone puts `' OR '1'='1` as their username, the query becomes `WHERE username = '' OR '1'='1'` — and that returns every user in the database. They just bypassed authentication with a creative username.

**Student:** That is scary. And this is in the sample code on purpose?

**Instructor:** Yes, there are ten intentional bugs in that file. Let us watch the three AI agents find and fix every one of them.

---

## Setting Up

**Student:** Only one API key needed this time — just Anthropic?

**Instructor:** Correct. No web search needed. The agents are reading code, not searching the internet. Just add your Anthropic key to `.env` and you are ready.

*[Student sets up .env file and runs pip install]*

```bash
pip install -r requirements.txt
```

**Student:** Done. Let me run it.

```bash
python code_review_pipeline.py sample_buggy_code.py
```

---

## Watching the Code Reviewer Work

*[System begins running...]*

```
🔬 CODE REVIEW PIPELINE 🔬

This pipeline uses THREE specialized AI agents:
   1. 🔍 Code Reviewer  — finds bugs, security issues, performance problems
   2. 🧪 Test Writer    — writes pytest tests for each issue found
   3. 🔧 Code Fixer     — fixes all CRITICAL and WARNING issues
   4. ✅ Approval Agent — verifies the fix is complete

Reviewing file: sample_buggy_code.py
Code size: 147 lines
```

**Student:** 147 lines. A real human would take maybe 20 minutes to review that.

**Instructor:** The AI will take about 15-20 seconds. And it will not miss anything.

*[Review starts...]*

```
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

**Student:** Five CRITICAL issues! I only spotted the one SQL injection. Let me see the full review.

*[Full review output scrolls...]*

```
## Code Review Report

### Summary
This user management module contains pervasive SQL injection vulnerabilities
affecting every database operation. All five database functions use dangerous
string concatenation instead of parameterized queries. Additionally, the module
lacks input validation, stores passwords insecurely, and contains a significant
performance bug.

### Issues Found

**[CRITICAL] SQL Injection in get_user_by_username (Line 38)**
- Problem: Username is directly concatenated into SQL query string
- Risk: Authentication bypass, full database dump, data manipulation
- Fix: Use parameterized queries: cursor.execute("... WHERE username = ?", (username,))

**[CRITICAL] Division by Zero in calculate_average_score (Line 53)**
- Problem: No check for empty list — len(scores) returns 0
- Risk: ZeroDivisionError crashes the application when empty list is passed
- Fix: Add guard: if not scores: return 0.0

**[CRITICAL] SQL Injection in create_new_user (Lines 79-83)**
- Problem: All three user fields directly concatenated into INSERT statement
- Risk: Attacker can insert arbitrary SQL, bypass constraints, gain admin access
- Fix: Use parameterized queries for all three fields

**[CRITICAL] SQL Injection in get_all_users_with_role (Line 103)**
- Problem: Role parameter injected directly into query
- Risk: UNION SELECT attack could dump entire password database
- Fix: Parameterized query required

**[CRITICAL] SQL Injection in update_user_email (Line 122) and search_users_by_name (Line 140)**
- Problem: Same injection pattern in two more functions
- Risk: Email update can be used to corrupt data or gain unauthorized access
- Fix: Parameterized queries in both functions

**[WARNING] Plain Text Password Storage (Line 83)**
- Problem: Password stored without hashing despite hashlib being imported
- Risk: Database breach exposes all user passwords in plain text
- Fix: Use hashlib.sha256 or better yet bcrypt/argon2 for password hashing

**[WARNING] O(n²) Performance in find_duplicate_users (Lines 63-72)**
- Problem: Nested loop comparing every pair of users
- Risk: 1000 users = 1,000,000 iterations; will be extremely slow at scale
- Fix: Use a set to find duplicates in O(n) time

**[WARNING] Missing Input Validation in create_new_user (Line 75)**
- Problem: No validation of username, password, or email format
- Risk: Empty strings, None values, or malformed emails stored in database
- Fix: Add validation before database operations

**[WARNING] No Result Limit in search_users_by_name (Line 141)**
- Problem: Fetches all matching rows with no LIMIT clause
- Risk: Could return thousands of rows, causing memory exhaustion
- Fix: Add LIMIT 100 to query

**[INFO] Unused Imports (Lines 10, 14)**
- Problem: json and re are imported but never used
- Risk: Unnecessary code — increases maintenance burden
- Fix: Remove unused imports

**[INFO] Hardcoded Database Path (Line 19)**
- Problem: DATABASE_PATH is hardcoded as "users.db"
- Fix: Read from environment variable: os.getenv("DATABASE_PATH", "users.db")
```

**Student:** That is incredibly detailed. It found the SQL injection in EVERY function, not just the first one. I only caught one when I read the code.

**Instructor:** That is why automated review is valuable. Human readers get fatigued. We read the first function carefully and the sixth function quickly. The AI reads every line with equal attention.

**Student:** And it found the division by zero bug. I completely missed that.

**Instructor:** Most people would. It is in a function with a clean-sounding name — `calculate_average_score`. You assume it works. The AI checks every function for every category of bug regardless of how innocent it looks.

---

## The Test Writer in Action

*[Workflow continues to test node...]*

```
============================================================
🧪 Test Writer creating test cases...
============================================================

🧪 Test Code Preview (first 600 chars):
----------------------------------------
# Auto-generated tests for security vulnerabilities in user management module
# Generated by AI Code Review Pipeline

import pytest
import sqlite3
import os
import tempfile

class TestCodeReview:
    """
    Test cases designed to catch all CRITICAL and WARNING issues found
    in the code review. These tests FAIL on the buggy code and PASS on fixed code.
    """

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_users.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, name TEXT, role TEXT)")
        conn.commit()
        conn.close()
        return str(db_path)
----------------------------------------
   Total test code: 3847 characters
   Test functions written: 8
```

**Student:** Eight test functions. And they use a `tmp_path` fixture — that is a pytest feature that creates a temporary directory for the test. The AI knows how to write idiomatic pytest!

**Instructor:** The Test Writer agent has a system prompt that says "You are a QA engineer." Because LLMs have been trained on enormous amounts of code, including pytest documentation and real test suites, it naturally produces idiomatic code.

**Student:** I notice the tests say "These tests FAIL on the buggy code and PASS on fixed code." That is proper Test-Driven Development.

**Instructor:** Exactly. This is the TDD principle — write the test that proves the bug exists first, then fix the bug, then verify the test passes. The AI does this automatically.

---

## Watching the Code Fixer

*[Workflow continues to fix node...]*

```
============================================================
🔧 Code Fixer fixing issues (cycle 1)...
============================================================
   Writing first-pass fixes...

🔧 Fixed Code Preview (first 600 chars):
----------------------------------------
## Changes Made

1. **SQL Injection Fixes (CRITICAL)**: Replaced all string concatenation in SQL
   queries with parameterized queries using `?` placeholders across all 5 functions:
   get_user_by_username, create_new_user, get_all_users_with_role,
   update_user_email, and search_users_by_name

2. **Division by Zero Fix (CRITICAL)**: Added guard clause in calculate_average_score:
   `if not scores: return 0.0`

3. **Password Hashing (WARNING)**: Implemented SHA-256 hashing using the already-imported
   hashlib module before storing passwords

4. **Performance Fix (WARNING)**: Replaced O(n²) nested loops in find_duplicate_users
   with a set-based O(n) algorithm

5. **Input Validation (WARNING)**: Added validation in create_new_user for empty/None values

6. **Query Limiting (WARNING)**: Added LIMIT 100 to search_users_by_name query

7. **Unused Imports Removed (INFO)**: Removed json and re imports
```

**Student:** It documented every single change it made. And it addressed all five CRITICAL issues.

**Instructor:** That is what the system prompt told it to do — start with a "Changes Made" section. Readable output from AI is just as important as correct output.

*[Continues showing the actual fixed code...]*

**Student:** Look at the fixed `get_user_by_username`:

```python
def get_user_by_username(username):
    # Input validation - reject None or empty username
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # FIXED: Use parameterized query - the ? placeholder is replaced safely
    # The database driver handles all escaping - user input cannot become SQL
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))  # username passed as tuple parameter

    result = cursor.fetchone()
    conn.close()
    return result
```

**Student:** The `?` placeholder is the fix. The user input goes in the tuple, not the string. The database driver handles the escaping.

**Instructor:** Exactly. The database driver knows to treat everything in that tuple as data, never as SQL commands. The attacker's `' OR '1'='1` would be treated as a literal username string — searched for in the database, found nothing, returned nothing. Harmless.

---

## The Approval Stage

*[Workflow continues to approve node...]*

```
============================================================
✅ Approval Agent checking fix quality...
============================================================

   Approval notes: VERDICT: APPROVED
   UNRESOLVED_ISSUES: None
   NOTES: All 5 CRITICAL SQL injection vulnerabilities have been addressed
   with parameterized queries. The division by zero edge case is handled.
   Password hashing is now implemented. The O(n²) performance bug has been
   corrected with a set-based approach...

   ✅ Fix APPROVED! All critical issues resolved.
   ➡️  Routing: Approved → going to OUTPUT
```

**Student:** Approved on the first try. All critical issues resolved.

**Instructor:** The fixer did a thorough job. If it had missed even one CRITICAL issue, the approval would fail and we would go back for a second fix cycle.

---

## Examining the Outputs

*[Workflow saves all files...]*

```
💾 Saving all outputs to review_output/...

   📋 Review saved to: review_output/sample_buggy_code_review_20260312_150342.md
   🧪 Tests saved to: review_output/sample_buggy_code_tests_20260312_150342.py
   🔧 Fixed code saved to: review_output/sample_buggy_code_fixed_20260312_150342.py
   📊 Summary saved to: review_output/sample_buggy_code_summary_20260312_150342.md
```

**Student:** Four files saved. The review, the tests, the fixed code, and a summary. That is a complete audit trail.

**Instructor:** Exactly. In a real DevOps context, you would commit these files to your repository along with the code changes. Future developers would know: this code was reviewed, here are the issues that were found, here are the tests that verify the fixes.

**Student:** This is like an automated paper trail for security compliance.

**Instructor:** You just described the value proposition of most security audit software. Companies pay thousands of dollars a month for tools that do exactly this.

---

## The Security Learning Moment

**Student:** Okay, I need to ask — is SQL injection really that common? I have never thought about it before.

**Instructor:** It has been the number one web vulnerability for over twenty years. Yes, really. And here is the disturbing part — the fix is trivially simple. Just use parameterized queries. One small change per function. But developers under pressure take shortcuts, use tutorials that do not show the safe pattern, or work in legacy codebases where the bad pattern is already established.

**Student:** So I should always use parameterized queries in my own code going forward.

**Instructor:** Always. Never concatenate user input into a SQL string. Not even for "simple" internal tools. The habit should be automatic.

**Student:** And the password hashing issue — storing plain text passwords?

**Instructor:** Also extremely common, and extremely dangerous. If your database is breached (and databases get breached), plain text passwords expose every user's password immediately. With proper hashing using bcrypt or argon2, the attacker would need to crack each password individually — a process that can take years for strong passwords.

**Student:** The sample code imported hashlib but never used it. That is almost worse — the developer knew passwords should be hashed but did not implement it.

**Instructor:** That happens constantly in real codebases. The intent was there. The implementation was left for "later" and never happened.

---

## Wrap-Up

**Instructor:** What surprised you most about this session?

**Student:** The range of issues the reviewer found. I was expecting it to catch the SQL injection I already knew about, but it found the division by zero, the performance issue, the unused imports — everything. It was more thorough than I would have been.

**Instructor:** That is a core advantage of AI code review. It applies every category of analysis to every line of code, consistently, without fatigue.

**Student:** I want to integrate this into my actual projects. Can I run this on code I am writing right now?

**Instructor:** Absolutely. Pass any Python file as an argument. Try it on something from Phase 2 or Phase 3 of this course. You might find issues in code you wrote weeks ago.

**Student:** That is slightly terrifying.

**Instructor:** That is good engineering practice. Find the issues before they find you.

---

## Homework

1. Run the pipeline on one of your own Python files from Phase 1 or Phase 2
2. Read the SQL injection section in the OWASP Top 10 documentation (free online)
3. Look at the generated test file and try to actually run it with pytest
4. Modify the review agent's system prompt to also check for Python type hints
5. Research bcrypt and understand why it is better than hashlib.sha256 for passwords

---

*End of Session — Project 11 Complete*
*Next: Project 12 — Data Analysis Crew (sales data cleaning, analysis, and executive reporting)*
