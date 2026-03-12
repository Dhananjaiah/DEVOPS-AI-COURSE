# Project 14 Transcript: AI-Powered Sales Pipeline Automation

**Setting:** Continuation of Phase 5, building momentum after completing the HR pipeline.

---

**Coach:** You just built a hiring pipeline. Now we are going to build a sales pipeline. Different domain, same architecture pattern — LangGraph, multiple specialized agents, FastAPI. Are you starting to see the pattern?

**Student:** Yeah, I think I do. It is always: define the state, write agents that modify the state, build the graph with edges, wrap it in FastAPI.

**Coach:** Exactly right. That pattern works for hiring, sales, customer support, content creation, code review — almost any multi-step business process. Once you understand the pattern, you can apply it anywhere. Today the domain is B2B sales. Do you know what B2B means?

**Student:** Business-to-business. Selling to companies instead of individual consumers.

**Coach:** Correct. And B2B sales has a very specific problem. Look at the sample leads file. How many leads are there, and how different are they from each other?

**Student:** Five leads. The first one, DataVault Analytics, has a $150K-$300K budget and is losing $50K per month in downtime. The last one, Derek's Dog Walking, has "under $1,000" budget and says he "might want to grow someday." These two are not the same at all.

**Coach:** And yet, in many sales organizations, both of these leads end up in the same spreadsheet. A human SDR has to read through all five, figure out which ones to prioritize, write a different email for each, log everything in Salesforce, and set follow-up reminders. That is hours of work. Our pipeline will do all of that automatically. Let us start it up.

**Student:** Running `python sales_pipeline.py`... server is up on port 8000.

**Coach:** Now open a terminal and run the test script to process all five leads. Watch the terminal output as it runs.

**Student:** Running `python test_pipeline.py`... I can see it processing them one by one. DataVault Analytics...

```
STARTING SALES PIPELINE: DataVault Analytics (a3f9b2c1)
[Agent 1] Lead Qualifier analyzing: DataVault Analytics...
[Agent 1] DataVault Analytics: Score 9/10 — Hot
[Agent 2] Email Drafter creating Hot email for DataVault Analytics...
[Agent 2] Email drafted for Sarah Mitchell at DataVault Analytics
[Agent 3] CRM Updater recording DataVault Analytics in database...
[Agent 3] Lead a3f9b2c1 saved to CRM with status: New
[Agent 4] Follow-up Scheduler planning next steps for DataVault Analytics...
[Agent 4] Follow-up scheduled for DataVault Analytics: first touch March 13
PIPELINE COMPLETE: Hot lead — score 9/10
```

**Student:** 9 out of 10! And it happened automatically. Now let me wait for all five...

**Coach:** While it runs, tell me why we made this pipeline sequential instead of branching like the HR one.

**Student:** Because every lead needs all four outputs. The HR pipeline skipped the offer letter for low scorers because it was not needed. But here, even a cold lead needs an email, needs to go in the CRM, and needs a follow-up schedule.

**Coach:** Correct. The personalization is inside the agents, not in the routing. Agent 2 writes a different type of email depending on the score. But the same four agents run for every lead. That is a key design decision.

**Student:** All five are done now. Let me look at the summary report.

```
PIPELINE SUMMARY REPORT
============================================================
Total leads processed: 5
  DataVault Analytics              9/10  Hot
  NexGen Manufacturing Corp        8/10  Hot
  GreenLeaf Logistics              6/10  Warm
  Maple Dental Group               5/10  Warm
  Derek's Dog Walking              2/10  Cold
```

**Student:** The ranking makes total sense. The two Hot leads have huge budgets and acute problems. Derek is Cold because he has no budget and no real pain.

**Coach:** Now let us look at the actual emails that were generated. Run `curl http://localhost:8000/leads/{lead_id}` for the DataVault Analytics lead and find the email.

**Student:** Got it. The subject line is: "Cutting your analytics downtime from hours to seconds — 15 min?" And the email starts with "Sarah, I saw that DataVault Analytics is running critical financial analytics on legacy Oracle infrastructure — when $50K per month is on the line from downtime, every hour counts." That is incredibly specific to their situation!

**Coach:** Now check the Cold lead email — Derek's Dog Walking.

**Student:** Subject: "How small service businesses are growing 30% without adding staff." The email starts with "Derek, small service businesses like yours have traditionally relied on word-of-mouth and personal relationships to grow — but there's a shift happening..." And it offers a free ebook. No hard sell at all.

**Coach:** The same company, the same product, completely different emails. This is what good sales people do intuitively — they read the room. Our AI is reading the room by looking at the score. Why does this matter so much?

**Student:** Because sending Derek the same urgent "let us schedule a demo" email that DataVault gets would be completely wrong. He is not ready to buy.

**Coach:** Exactly. And sending DataVault the soft thought leadership email when they are actively losing money and need a solution NOW would cost you the deal. Timing and tone are everything in sales. Let us look at the CRM data.

**Student:** Running `curl http://localhost:8000/leads`...

```json
{
  "leads": [
    {"company": "DataVault Analytics", "lead_score": 9, "lead_category": "Hot",
     "next_follow_up": "2026-03-13T..."},
    {"company": "NexGen Manufacturing Corp", "lead_score": 8, "lead_category": "Hot",
     "next_follow_up": "2026-03-13T..."},
    ...
  ],
  "total": 5,
  "hot_leads": 2,
  "warm_leads": 2,
  "cold_leads": 1
}
```

**Student:** The CRM is already populated! And the follow-up dates are set.

**Coach:** In real Salesforce, each of those records would have tasks assigned to specific reps, calendar reminders, and automated email sequences. What we built is the core intelligence layer — the part that requires judgment. The CRM is just storage.

**Student:** I'm curious about the follow-up schedule that was generated. What does it say for the Hot lead?

**Coach:** Look at the `follow_up_schedule` field in the full lead record.

**Student:** Running `curl http://localhost:8000/leads/a3f9b2c1`... The follow-up plan says: "Touch 1 — March 13 (Tomorrow): Call Sarah Mitchell directly at the number on her LinkedIn profile. Open with the $50K monthly loss figure. Propose a 15-minute Zoom call for Friday. Send a LinkedIn connection request after the call. Touch 2 — March 15: Send a follow-up email with a case study of a financial services company that reduced downtime by 94% using CloudSuite Pro. Include ROI calculator spreadsheet..." It goes on with a complete action plan.

**Coach:** This took Claude about 8 seconds to generate. A skilled SDR might take 20 minutes to create a sequence this personalized. The rep can now spend their time actually calling Sarah, not figuring out what to say.

**Student:** I see the business value now. You are automating the planning, not the human relationship.

**Coach:** That is a beautifully put distinction. AI handles the research, qualification, email writing, scheduling — all the cognitive but repetitive work. The human still makes the actual call, builds the relationship, and closes the deal. AI makes humans more effective, not redundant.

**Student:** One thing I noticed: the pipeline takes about 25-30 seconds per lead because of the four API calls. That would be slow if you had 300 leads at once.

**Coach:** Sharp observation. In production, you would process leads in parallel using Python's `asyncio` or a task queue like Celery with Redis. You could process 20 leads simultaneously and cut total time from 150 minutes (300 leads × 30 seconds) to about 7 minutes. We will not build that here, but now you know what the next optimization would be.

**Student:** What about leads that come in from a web form? Could this pipeline run automatically?

**Coach:** Absolutely. Replace the manual API call with a webhook. Most CRMs can send a webhook to your API when a new lead is created. Set it up once and every new lead is automatically qualified, emailed, and scheduled — with zero human intervention for the initial outreach.

**Student:** So the SDR wakes up in the morning and all 50 new leads from yesterday are already scored, emailed, and have follow-up tasks in Salesforce?

**Coach:** Exactly. Their morning becomes: "Which of the 12 Hot leads should I call first?" instead of "Let me read through 50 leads and figure out what to do." That is the practical AI transformation story — not replacing the SDR, but making them dramatically more effective.

**Student:** This project has been eye-opening. I had no idea this is what happens behind the scenes when a company's marketing form says "someone will follow up soon."

**Coach:** Now you do — and you can build it. On to Project 15, which is the most complex one in the course: a production enterprise RAG system with authentication, logging, and document management.
