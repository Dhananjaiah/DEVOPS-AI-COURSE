# Project 13: AI-Powered HR Recruitment Pipeline

## What You Will Build

In this project you build a complete, automated hiring pipeline powered by AI. The system reads a candidate's resume, compares it to a job description, scores the candidate, and automatically generates the right next step — interview invitation, offer letter, or rejection email.

This is not a toy example. Companies like LinkedIn, Greenhouse, Workday, and Lever all use systems exactly like this to handle thousands of applications per day. After completing this project, you understand the technology behind modern AI-assisted hiring.

---

## Real World Context: AI in Modern Hiring

### How Big Companies Use AI Screening Today

**LinkedIn Recruiter** uses AI to score candidates before a human ever looks at a profile. The algorithm considers skills, experience, education, location, and dozens of other signals to rank applicants.

**Greenhouse** (used by Airbnb, Squarespace, 5,000+ companies) integrates AI screening tools that score inbound applications automatically. Recruiters only review candidates above a threshold.

**Workday** (used by half the Fortune 500) has built-in AI that can screen and rank applicants against job requirements without human intervention.

**HireVue** uses AI video analysis to screen candidates through recorded video interviews, analyzing language patterns and responses.

**The business case is clear:**
- A senior role at a tech company receives 500-2,000 applications per opening
- Human review of every resume takes 6-10 seconds per resume at minimum
- 500 applications × 8 seconds = 67 minutes just for initial screening
- At scale (thousands of openings per year), this is months of work
- AI can do initial screening in seconds per candidate, 24/7, at zero marginal cost

---

## Architecture: How the Pipeline Works

```
Resume + Job Description
         |
         v
  [Agent 1: Resume Screener]
    - Analyzes match quality
    - Produces score (0-100)
    - PASS >= 60, FAIL < 60
         |
    [ROUTING DECISION]
    /              \
Score < 60        Score >= 60
    |                  |
[Agent 4:         [Agent 2:
 Rejection         Interview
 Emailer]          Scheduler]
    |                  |
  END            [ROUTING]
                /         \
          Score < 75    Score >= 75
               |              |
              END         [Agent 3:
                           Offer Letter
                           Drafter]
                               |
                              END
```

### The Four Agents

**Agent 1 — Resume Screener**
The most important agent. It acts as an expert HR screener with 15 years of experience. It evaluates four dimensions:
- Technical skills match (40%)
- Years of relevant experience (30%)
- Education and certifications (15%)
- Soft skills and communication quality (15%)

It outputs a score from 0-100, a PASS/FAIL decision, and a list of strengths and weaknesses.

**Agent 2 — Interview Scheduler**
For candidates who score 60 or above. Drafts a warm, professional interview invitation email with available time slots. The tone matters — every interaction with a candidate affects your employer brand.

**Agent 3 — Offer Letter Drafter**
For top candidates who score 75 or above. Drafts a complete, legally-appropriate formal offer letter with salary range, benefits, contingencies, and response deadline. This saves the HR team significant time on paperwork.

**Agent 4 — Rejection Emailer**
For candidates who score below 60. Writes a kind, professional rejection that preserves the company's reputation. Rejected candidates talk to other candidates and post on Glassdoor — a poor candidate experience hurts future recruiting.

---

## LangGraph: Why We Use a Workflow Graph

### The Problem with Simple Chains

In Projects 1-12, you often chained AI calls in sequence. For the HR pipeline, a simple chain does not work because:

1. Not every resume needs all four agents
2. The path depends on the score (which we do not know until Agent 1 runs)
3. Some paths converge back to the same endpoint

### How LangGraph Solves This

LangGraph lets you define a **stateful directed graph** where:
- Each node is an agent or function
- Edges define possible transitions between nodes
- Conditional edges use a routing function to decide the path dynamically
- State flows through the entire graph, accumulating results

```python
# The state carries all data through every agent
class RecruitmentState(TypedDict):
    resume_text: str
    score: int
    pass_fail: str
    interview_email: str
    offer_letter: str
    rejection_email: str
    pipeline_status: str
```

Every agent receives the full state, adds its contribution, and returns the updated state. LangGraph handles the routing automatically based on your conditional edge functions.

---

## Ethical Considerations: AI Bias in Hiring

This section is mandatory reading before using AI in any hiring context.

### The Problem

AI screening systems can perpetuate and amplify human biases present in training data. This has been documented in multiple real cases:

**Amazon's AI Resume Screening (2018):** Amazon built and then scrapped an AI recruiting tool because it was systematically downgrading resumes that included the word "women's" (as in "women's chess club") because the training data reflected a male-dominated industry.

**Resume Name Discrimination:** Research studies have shown that resumes with names perceived as Black or female receive significantly fewer callbacks than identical resumes with names perceived as white or male. An AI trained on historical callback data will learn and replicate this bias.

**Education Prestige Bias:** Training data from companies that historically hired from elite universities will create models that over-weight university prestige, disadvantaging equally qualified candidates from less prestigious schools.

**Geographic Bias:** If most successful hires lived in certain zip codes (often correlating with income/race), the model may learn to penalize candidates from other areas.

### Types of Bias in AI Hiring Systems

**Historical Bias:** The AI learns from past hiring decisions that were themselves biased.

**Representation Bias:** If the training set does not represent the full diversity of qualified candidates, the model will underperform on underrepresented groups.

**Measurement Bias:** Using proxies for "good performance" (like staying at a job a long time) that correlate with demographic factors unrelated to job performance.

**Feedback Loop Bias:** If biased predictions lead to biased hiring, and those hires become future training data, the bias compounds over time.

### Legal Considerations

**United States:**
- Title VII of the Civil Rights Act prohibits employment discrimination based on race, color, religion, sex, or national origin
- The EEOC has issued guidance that AI hiring tools must not have "disparate impact" on protected classes
- New York City Local Law 144 (2023) requires bias audits of AI tools used in hiring
- The EEOC has filed enforcement actions against companies using discriminatory AI screening

**European Union:**
- The EU AI Act classifies AI in hiring as "high risk" requiring conformity assessments
- GDPR requires transparency about automated decision-making and gives candidates the right to human review

### Mitigation Strategies

**Audit your training data:** Regularly check whether your system has disparate rejection rates across demographic groups.

**Use structured criteria:** Define objective evaluation criteria (skills, experience, certifications) rather than subjective cultural fit scores.

**Human review:** Always have humans review borderline cases. AI should assist, not replace, human judgment.

**Transparency:** Tell candidates when AI was used in their screening. Some jurisdictions require this.

**Regular audits:** Test your system quarterly with synthetic resumes that are identical except for demographic signals.

**Diverse training data:** If fine-tuning your models, ensure training data represents the full diversity of successful employees.

**The bottom line:** AI screening can be fair and effective, but only if built and monitored with intentional care. The system in this project uses Claude (not historical hiring data), which reduces some biases but does not eliminate them. Always pair AI screening with human oversight.

---

## Project Setup

### Step 1: Create Your Environment File

```bash
cd project13-hr-recruiter
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed anthropic-0.40.0 langchain-0.3.0 ...
```

### Step 3: Verify Your Setup

Before running the full server, you can test that your API key works:

```python
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('ANTHROPIC_API_KEY')
print('API key found:', 'Yes' if key and key.startswith('sk-ant') else 'No')
"
```

### Step 4: Run the Server

```bash
python hr_recruiter.py
```

You will see:
```
Starting HR Recruitment Pipeline API...
API Documentation available at: http://localhost:8000/docs
INFO:     Started server process [XXXXX]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Open the Interactive API Docs

Visit: **http://localhost:8000/docs**

FastAPI automatically generates an interactive Swagger UI where you can:
- Read documentation for each endpoint
- Test endpoints directly from your browser
- See request and response schemas

---

## Testing the Pipeline

### Test with the Strong Candidate (expect PASS + Offer Letter)

```bash
curl -X POST http://localhost:8000/screen \
  -H "Content-Type: application/json" \
  -d "{
    \"resume_text\": $(cat strong_candidate.txt | python3 -c \"import sys,json; print(json.dumps(sys.stdin.read()))\"),
    \"job_description\": $(cat senior_python_dev.txt | python3 -c \"import sys,json; print(json.dumps(sys.stdin.read()))\")
  }"
```

Or use Python:

```python
import requests
import json

# Read the sample files
with open("strong_candidate.txt") as f:
    resume = f.read()
with open("senior_python_dev.txt") as f:
    job_desc = f.read()

# Make the API call
response = requests.post(
    "http://localhost:8000/screen",
    json={"resume_text": resume, "job_description": job_desc}
)

result = response.json()
print(f"Candidate: {result['candidate_name']}")
print(f"Score: {result['score']}/100")
print(f"Decision: {result['pass_fail']}")
print(f"Pipeline reached: {result['pipeline_status']}")

# If they passed, show the interview email
if result['interview_email']:
    print("\n--- Interview Email ---")
    print(result['interview_email'])

# If top scorer, show offer letter
if result['offer_letter']:
    print("\n--- Offer Letter ---")
    print(result['offer_letter'])
```

### Test with the Average Candidate (expect PASS, interview only)

```python
with open("average_candidate.txt") as f:
    resume = f.read()

response = requests.post(
    "http://localhost:8000/screen",
    json={"resume_text": resume, "job_description": job_desc}
)
result = response.json()
print(f"Score: {result['score']}/100 — {result['pass_fail']}")
```

### Test with the Weak Candidate (expect FAIL + rejection email)

```python
with open("weak_candidate.txt") as f:
    resume = f.read()

response = requests.post(
    "http://localhost:8000/screen",
    json={"resume_text": resume, "job_description": job_desc}
)
result = response.json()
print(f"Score: {result['score']}/100 — {result['pass_fail']}")
if result['rejection_email']:
    print("\n--- Rejection Email ---")
    print(result['rejection_email'])
```

### Check Pipeline Statistics

```bash
curl http://localhost:8000/pipeline-status
```

---

## File Structure

```
project13-hr-recruiter/
├── hr_recruiter.py          # Main application: agents + LangGraph + FastAPI
├── requirements.txt         # Python dependencies
├── .env.example             # Template for your API key
├── .env                     # Your actual API key (never commit this!)
├── senior_python_dev.txt    # Sample job description
├── strong_candidate.txt     # Sample resume: high scorer (expect 80-95/100)
├── average_candidate.txt    # Sample resume: mid scorer (expect 60-75/100)
├── weak_candidate.txt       # Sample resume: low scorer (expect 20-40/100)
└── README.md                # This file
```

---

## Understanding the Code

### Why TypedDict for State?

```python
class RecruitmentState(TypedDict):
    resume_text: str
    score: int
    pass_fail: str
    ...
```

TypedDict gives Python type checking for dictionary keys without the overhead of a full class. LangGraph requires a TypedDict (or Pydantic model) for state so it can:
1. Validate that all required fields exist
2. Merge partial state updates from each agent
3. Track the full state through every node

### Why Conditional Edges?

```python
workflow.add_conditional_edges(
    "resume_screener",
    route_after_screening,
    {"interview_scheduler": "interview_scheduler", "rejection_emailer": "rejection_emailer"}
)
```

Without conditional edges, you would need to either:
- Run all agents on every resume (wasteful and slow)
- Hard-code multiple separate pipelines (unmaintainable)

Conditional edges let the graph branch dynamically based on runtime data.

### Why FastAPI instead of just running the pipeline?

A CLI script works fine for testing. FastAPI gives you:
- **REST API**: Any system (frontend, mobile app, ATS software) can integrate
- **Async handling**: Multiple resumes can be processed concurrently
- **Validation**: Pydantic automatically validates input and returns helpful errors
- **Documentation**: Auto-generated Swagger UI for free
- **Production-ready**: Can be deployed behind a load balancer with multiple workers

---

## Common Issues and Solutions

### Issue: "API key not found" error
**Solution:** Make sure your `.env` file exists (not just `.env.example`) and contains your real API key.

### Issue: LangGraph import error
**Solution:** Run `pip install langgraph==0.2.0` specifically. Different versions have different APIs.

### Issue: Score parsing fails and always returns 50
**Solution:** This means Claude's response format deviated from the expected template. Check the `screen_result` field in the response — Claude may have formatted the score differently. The parser looks for a line starting with "SCORE:".

### Issue: Pipeline takes 15-30 seconds
**This is normal.** Each agent call to Claude takes 3-8 seconds. A pipeline with 3 agents (strong candidate) takes 9-24 seconds total. This is acceptable for a hiring workflow where results are high-value.

### Issue: "context length exceeded" error
**Solution:** Very long resumes (10+ pages) may exceed token limits. In production, add a preprocessing step to truncate or summarize overly long resumes.

---

## What to Try Next

1. **Add more job descriptions:** Create files for different roles and see how the same candidate scores differently against different jobs.

2. **Tune the thresholds:** Change the PASS threshold from 60 to 70 and see how it affects your pipeline routing.

3. **Add a database:** Replace the in-memory `pipeline_stats` dict with SQLite or PostgreSQL to persist results across server restarts.

4. **Add email sending:** Integrate with SendGrid or AWS SES to actually send the generated emails.

5. **Build a frontend:** Create a simple HTML form that submits to your API and displays the results nicely.

6. **Add logging:** Log every decision to a file for compliance and auditing (required in some jurisdictions).

---

## Key Concepts Learned

- **LangGraph state management:** TypedDict state flows through all agents
- **Conditional routing:** Graphs branch dynamically based on runtime values
- **Multi-agent specialization:** Each agent has a focused role and specific system prompt
- **FastAPI integration:** Wrapping a LangGraph pipeline in a production web API
- **AI in enterprise HR:** Real-world business context for your technical skills
- **Ethical AI:** Understanding and mitigating bias in automated decision systems

---

## Further Reading

- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- Anthropic API reference: https://docs.anthropic.com
- EEOC guidance on AI hiring tools: https://www.eeoc.gov/ai-hiring
- NYC Local Law 144 (AI hiring bias audit): https://www.nyc.gov/site/dca/businesses/automated-employment-decision-tools.page
- EU AI Act overview: https://artificialintelligenceact.eu/
