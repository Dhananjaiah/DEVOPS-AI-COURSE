# Project 14: AI-Powered Sales Pipeline Automation

## What You Will Build

A complete B2B sales automation system that qualifies incoming leads, drafts personalized outreach emails matched to the lead's temperature, updates a simulated CRM database, and schedules structured follow-up sequences. The system handles everything from lead data intake to a ready-to-send email in a single API call.

---

## Real World Context: AI in Modern Sales

### The Business Problem AI Solves

B2B sales is a numbers game. The average enterprise software company's sales team receives 200-500 new leads per month. Without AI:

- A sales development rep (SDR) manually reviews each lead profile: 5-10 minutes per lead
- They write a personalized email from scratch: 15-30 minutes per email
- They log everything in Salesforce manually: 5 minutes per lead
- They set calendar reminders for follow-ups: 3-5 minutes per lead

For 300 leads per month, that is **200+ hours of manual work** — more than a full-time job just for one SDR, before they even pick up the phone.

### How Leading CRM Companies Are Solving This

**Salesforce Einstein** is Salesforce's AI platform. It automatically:
- Scores leads based on firmographic data (company size, industry, website activity)
- Surfaces the highest-priority leads for each rep every morning
- Predicts deal win probability
- Drafts email suggestions based on deal stage

**HubSpot AI** (used by 200,000+ businesses) includes:
- Lead scoring that updates in real time as prospects take actions
- AI email assistant that writes personalized outreach
- Conversation intelligence that analyzes sales call recordings
- Deal pipeline prediction

**Outreach.io and Salesloft** are AI-first sales engagement platforms used by thousands of enterprise sales teams. Their AI determines the optimal time to send emails, personalizes content for each prospect, and identifies which prospects are showing buying signals.

**The ROI is measurable:**
- Companies using AI lead scoring report 25-35% higher conversion rates
- AI-personalized emails have 3-5x higher response rates than generic templates
- Sales reps using AI tools spend 35% more time actually selling (talking to prospects) vs. administrative work

---

## Architecture: The Four-Agent Pipeline

```
Lead Data Input
     |
     v
[Agent 1: Lead Qualifier]
  - Scores 1-10
  - Hot / Warm / Cold
  - Identifies key buying signals
  - Recommends next action
     |
     v
[Agent 2: Email Drafter]
  - Hot leads: urgent, direct, propose meeting
  - Warm leads: value-focused, offer resource
  - Cold leads: thought leadership, no hard pitch
     |
     v
[Agent 3: CRM Updater]
  - Writes record to crm_data.json
  - Stores score, category, email status
  - Timestamps last contact
     |
     v
[Agent 4: Follow-up Scheduler]
  - Hot: Day 1, Day 3, Day 7
  - Warm: Day 3, Day 7, Day 14
  - Cold: Day 7, Day 21, Day 45
  - Specific action plan for each touch
     |
     v
   DONE — lead is in CRM with full action plan
```

Unlike Project 13's branching pipeline, the sales pipeline is **sequential** — every lead goes through all four agents because:
- Every lead needs qualification (to decide the approach)
- Every lead needs an email (different tone based on score)
- Every lead needs to be in the CRM (for tracking)
- Every lead needs a follow-up plan (with different timing)

The personalization happens within each agent based on the lead's score, not by skipping agents.

---

## Lead Scoring Explained

### The 1-10 Scale

The Lead Qualifier agent scores each lead across five dimensions (2 points each, max 10):

| Dimension | What it measures |
|-----------|-----------------|
| Budget fit | Does their budget align with our solution's cost? |
| Company size | Is this our ideal customer profile? |
| Pain urgency | How acute and immediate is the problem? |
| Solution fit | How well does our product solve their specific problem? |
| Competitive position | Are they replacing a competitor or starting fresh? |

### Hot / Warm / Cold Categories

| Category | Score | What it means | Follow-up timing |
|----------|-------|---------------|-----------------|
| Hot | 8-10 | High urgency, strong fit, ready to buy | 1 day |
| Warm | 5-7 | Good fit but lower urgency or less clear need | 3 days |
| Cold | 1-4 | Poor fit or no clear buying intent right now | 1 week |

### Why Email Personalization by Temperature Matters

Research from sales science shows:

- A generic sales email gets a 2-3% response rate
- A personalized email addressing specific pain points gets 8-12% response rate
- An email sent to a "hot" lead who just searched for a solution gets 15-25% response rate

The same email sent to a hot lead and a cold lead performs very differently because:
- Hot leads are **actively looking** — they appreciate urgency and a clear proposal
- Cold leads are **not in buying mode** — they will delete pushy emails, but might read helpful insights
- Warm leads need **value first** — give before you ask

Our pipeline automatically writes three different types of emails using the same information. This is not just automation — it is **intelligent automation** that mimics what a skilled SDR would do.

---

## Project Setup

### Step 1: Navigate to the Project Folder

```bash
cd project14-sales-pipeline
```

### Step 2: Create Your Environment File

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Note: This project adds `pandas==2.2.0` for data analysis. The sales stats analysis can use pandas DataFrames for reporting.

### Step 4: Run the Server

```bash
python sales_pipeline.py
```

Visit **http://localhost:8000/docs** for the interactive API interface.

---

## Testing with Sample Leads

### Option 1: Use the Python Helper Script

Create a file called `test_pipeline.py` and paste this:

```python
import requests
import json

# Load all five sample leads
with open("sample_leads.json") as f:
    leads = json.load(f)

print("Processing 5 sample leads through the pipeline...")
print("=" * 60)

results = []
for lead in leads:
    print(f"\nProcessing: {lead['company']}...")
    response = requests.post(
        "http://localhost:8000/qualify-lead",
        json=lead
    )

    if response.status_code == 200:
        result = response.json()
        results.append(result)
        print(f"  Score: {result['lead_score']}/10 — {result['lead_category']}")
        print(f"  Action: {result['recommended_action']}")
    else:
        print(f"  ERROR: {response.text}")

# Summary report
print("\n" + "=" * 60)
print("PIPELINE SUMMARY REPORT")
print("=" * 60)
print(f"Total leads processed: {len(results)}")
for r in sorted(results, key=lambda x: x['lead_score'], reverse=True):
    print(f"  {r['company']:35} {r['lead_score']}/10  {r['lead_category']}")
```

Run it:
```bash
python test_pipeline.py
```

### Option 2: Use curl with a single lead

```bash
curl -X POST http://localhost:8000/qualify-lead \
  -H "Content-Type: application/json" \
  -d '{
    "company": "TechStartup Inc",
    "contact_name": "Jennifer Lee",
    "contact_email": "jlee@techstartup.com",
    "industry": "SaaS",
    "company_size": "100-250",
    "annual_budget": "$75,000-$150,000",
    "pain_points": "Our deployment pipeline takes 4 hours and breaks frequently. We are losing engineers to burnout.",
    "current_solution": "Jenkins from 2018, manual deployments"
  }'
```

### Expected Results for Sample Leads

Based on the sample data in `sample_leads.json`:

| Company | Expected Score | Expected Category |
|---------|---------------|-------------------|
| DataVault Analytics | 9-10 | Hot (large budget, acute pain, urgency) |
| NexGen Manufacturing Corp | 8-9 | Hot (board-approved budget, digital transformation) |
| GreenLeaf Logistics | 5-7 | Warm (real problem, modest budget) |
| Maple Dental Group | 4-6 | Warm/Cold (small, limited budget) |
| Derek's Dog Walking | 1-2 | Cold (no budget, no clear need) |

---

## Checking Your CRM

After processing leads, check the CRM database:

```bash
# View all leads
curl http://localhost:8000/leads

# View a specific lead (use an ID from the /leads response)
curl http://localhost:8000/leads/{lead_id}
```

Or look directly at the JSON file:
```bash
# The file is created automatically in the same directory
cat crm_data.json
```

---

## Understanding the Code

### Why Local JSON Instead of a Real Database?

The `crm_data.json` file is intentional for this learning project. It lets you:
- See exactly what gets written to the CRM (just open the JSON)
- Understand the data structure without setting up a database
- Focus on the AI pipeline logic, not database administration

In production, you would replace `load_crm()` and `save_crm()` with:
- **Salesforce:** `simple_salesforce` Python library
- **HubSpot:** HubSpot Python SDK
- **PostgreSQL:** `sqlalchemy` + `psycopg2`
- **MongoDB:** `pymongo`

The rest of the pipeline code stays exactly the same. This is the power of abstraction.

### Why Is the Sales Pipeline Sequential While HR Was Branching?

Great question. The design choice reflects the real business process:

**HR pipeline (branching):** Not every candidate needs an offer letter. Running Agent 3 on every resume wastes money and time. So we branch: only top candidates get offer letters.

**Sales pipeline (sequential):** Every lead needs all four outputs regardless of score. A cold lead still needs an email (just a different type). A cold lead still needs to be in the CRM (so you can track them over time). A cold lead still needs a follow-up schedule (just less frequent).

The personalization happens within each agent (different email tones, different follow-up intervals) rather than by skipping agents entirely.

### The CRM Record Structure

```python
crm_record = {
    "lead_id": "abc12345",
    "company": "DataVault Analytics",
    "contact_name": "Sarah Mitchell",
    "lead_score": 9,
    "lead_category": "Hot",
    "status": "New",                    # Will change as deal progresses
    "email_sent": True,
    "last_contact": "2026-03-12T...",
    "next_follow_up": "2026-03-13T...",
    "notes": "AI qualified. Score: 9/10. Call immediately.",
    "pipeline_stage": "Outreach"
}
```

This maps directly to standard Salesforce Lead fields. If you connected this to real Salesforce, you would use the `simple_salesforce` library and call `sf.Lead.create(crm_record)`.

---

## Analyzing Your Pipeline Performance

After processing several leads, you can analyze results using pandas:

```python
import pandas as pd
import json

# Load CRM data
with open("crm_data.json") as f:
    crm_data = json.load(f)

# Convert to DataFrame
leads_list = list(crm_data.values())
df = pd.DataFrame(leads_list)

# Basic stats
print("Pipeline Statistics:")
print(f"Total leads: {len(df)}")
print(f"Average score: {df['lead_score'].mean():.1f}/10")
print(f"\nLead breakdown:")
print(df['lead_category'].value_counts())

# Score distribution
print(f"\nScore distribution:")
print(df.groupby('lead_category')['lead_score'].describe())

# Industry breakdown
print(f"\nLeads by industry:")
print(df.groupby('industry')['lead_score'].mean().sort_values(ascending=False))
```

---

## File Structure

```
project14-sales-pipeline/
├── sales_pipeline.py        # Main application: 4 agents + LangGraph + FastAPI
├── requirements.txt         # Python dependencies
├── .env.example             # Template for API key
├── .env                     # Your actual API key (never commit this!)
├── sample_leads.json        # 5 sample leads of varying quality
├── crm_data.json            # Auto-created when you run the pipeline
└── README.md                # This file
```

---

## Common Issues

### Issue: CRM file gets corrupted
**Solution:** The JSON CRM is written after every pipeline run. If the server crashes mid-write (rare), the file might be corrupted. Delete `crm_data.json` and start fresh. In production, use a proper database with ACID transactions.

### Issue: Lead score seems too high/low
**This is normal variability.** Claude's scoring can vary slightly between runs because LLMs are probabilistic, not deterministic. You can reduce this by:
- Lowering the temperature parameter (add `temperature=0` to the ChatAnthropic constructor)
- Making the scoring rubric in the system prompt even more specific

### Issue: Email is generic and not personalized
**Check the pain_points field.** The more specific and detailed the pain points, the more personalized the email. "Our database is slow" produces a generic email. "Our Oracle database crashes every Monday morning when 200 traders run reports simultaneously, causing $50K in losses" produces a highly specific, compelling email.

---

## Key Concepts Learned

- **Sequential vs. branching LangGraph pipelines:** Knowing when to branch vs. sequence
- **Prompt engineering for sales:** Different tones for different contexts
- **Simulated external integrations:** The CRM pattern for learning real integration concepts
- **Business domain knowledge in AI systems:** AI that understands sales strategy, not just text
- **State accumulation:** Each agent adds information, later agents use earlier results

---

## Next Steps

- **Integrate real Salesforce:** Use `simple_salesforce` library to write real CRM records
- **Add email sending:** Use SendGrid API to actually send the drafted emails
- **Add webhook triggers:** Trigger the pipeline when a new form submission comes in
- **Build a dashboard:** Use Streamlit or a React frontend to visualize the CRM data
- **A/B test email templates:** Track open/reply rates for different email approaches
