# sales_pipeline.py
# Project 14: AI-Powered Sales Pipeline Automation
# This builds a complete B2B sales automation system using LangGraph and Claude
# It qualifies leads, drafts personalized outreach, updates a simulated CRM, and schedules follow-ups

# --- IMPORTS ---
import os                              # Access environment variables and file paths
import json                            # Read/write JSON for the simulated CRM database
from typing import TypedDict, Optional, List  # Type hints for code clarity
from datetime import datetime, timedelta      # Date calculations for follow-up scheduling
from dotenv import load_dotenv         # Load API keys from .env file
from langchain_anthropic import ChatAnthropic  # Claude AI via LangChain
from langchain_core.messages import HumanMessage, SystemMessage  # Message types
from langgraph.graph import StateGraph, END  # Build the workflow graph
from fastapi import FastAPI, HTTPException   # Web API framework
from pydantic import BaseModel               # Data validation for API requests
import uvicorn                               # ASGI server
import uuid                                  # Generate unique IDs for leads

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()  # Read ANTHROPIC_API_KEY from .env file

# --- CRM DATABASE FILE PATH ---
# We simulate a CRM using a local JSON file
# In production, this would be Salesforce, HubSpot, or a PostgreSQL database
CRM_FILE = "crm_data.json"  # Path to the local JSON CRM database

# --- INITIALIZE CLAUDE AI MODEL ---
llm = ChatAnthropic(
    model="claude-opus-4-6",           # Most capable Claude model
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=1500                    # Reasonable limit for sales emails
)

# --- PIPELINE STATE DEFINITION ---
# All data flows through this state as it moves through the LangGraph pipeline
class SalesPipelineState(TypedDict):
    lead_id: str                       # Unique identifier for this lead
    company: str                       # Company name
    contact_name: str                  # Primary contact person
    contact_email: str                 # Email address
    industry: str                      # What sector they are in
    company_size: str                  # Number of employees
    annual_budget: str                 # Their estimated budget
    pain_points: str                   # Problems they are trying to solve
    current_solution: str              # What they use now (competitor or nothing)
    lead_score: int                    # Numeric score 1-10 from Agent 1
    lead_category: str                 # Hot/Warm/Cold from Agent 1
    qualification_analysis: str        # Full analysis text from Agent 1
    recommended_action: str            # What to do next (from Agent 1)
    outreach_email: str                # Personalized email from Agent 2
    crm_record: dict                   # The record written to our CRM by Agent 3
    follow_up_schedule: str            # Follow-up plan from Agent 4
    pipeline_stage: str                # Current stage in the workflow
    error: Optional[str]               # Any errors that occurred

# ============================================================
# CRM HELPER FUNCTIONS
# ============================================================
# These functions simulate a real CRM integration

def load_crm() -> dict:
    """Load the CRM database from the JSON file. Returns empty dict if file doesn't exist."""
    if os.path.exists(CRM_FILE):       # Check if CRM file exists
        with open(CRM_FILE, 'r') as f:  # Open the file for reading
            return json.load(f)        # Parse and return the JSON data
    return {}                          # Return empty dict if no CRM file yet

def save_crm(crm_data: dict):
    """Save the CRM database back to the JSON file."""
    with open(CRM_FILE, 'w') as f:     # Open the file for writing
        json.dump(crm_data, f, indent=2, default=str)  # Write formatted JSON


# ============================================================
# AGENT 1: LEAD QUALIFIER
# ============================================================
# Analyzes the lead data and determines their likelihood to purchase
def lead_qualifier_agent(state: SalesPipelineState) -> SalesPipelineState:
    """
    Agent 1: Lead Qualifier
    Analyzes company and lead data to score the lead on a 1-10 scale.
    Categorizes as Hot (8-10), Warm (5-7), or Cold (1-4).
    """
    print(f"\n[Agent 1] Lead Qualifier analyzing: {state['company']}...")

    # System prompt makes Claude an expert sales analyst
    system_prompt = """You are an expert B2B sales analyst with 20 years of experience qualifying leads.
You have a deep understanding of buyer behavior and conversion signals.

Scoring criteria (1-10 scale):
- Budget fit: Do they have budget aligned with your solution? (2 points max)
- Company size: Is this an ideal customer profile? Mid-market 100-5000 employees is best (2 points)
- Pain point urgency: How acute is the problem they need solved? (2 points)
- Solution fit: How well does our product solve their stated problems? (2 points)
- Competitive position: Are they using a competitor or nothing? (2 points)

Categories:
- HOT (8-10): Reach out IMMEDIATELY, high conversion probability
- WARM (5-7): Nurture with value-added content, follow up in 3 days
- COLD (1-4): Add to email drip campaign, check back in 1 week

Always respond in this EXACT format:
SCORE: [1-10]
CATEGORY: [HOT, WARM, or COLD]
ANALYSIS: [3-4 sentences explaining the score]
STRENGTHS:
- [buying signal 1]
- [buying signal 2]
CONCERNS:
- [concern 1]
- [concern 2]
RECOMMENDED_ACTION: [specific next step in 1-2 sentences]"""

    # Build the context about this specific lead
    human_message = f"""Please qualify this B2B sales lead:

Company: {state['company']}
Contact: {state['contact_name']} | Email: {state['contact_email']}
Industry: {state['industry']}
Company Size: {state['company_size']} employees
Annual Budget: {state['annual_budget']}
Pain Points: {state['pain_points']}
Current Solution: {state['current_solution']}"""

    # Call Claude to analyze and score the lead
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    analysis = response.content        # Store the full analysis text

    # Extract the numeric score from the response
    score = 5                          # Default to middle score
    for line in analysis.split('\n'):  # Check each line
        if line.startswith('SCORE:'):
            try:
                score = int(line.split(':')[1].strip())  # Parse integer score
                score = max(1, min(10, score))           # Clamp between 1-10
            except:
                score = 5              # Keep default on parse failure

    # Extract the category (Hot/Warm/Cold)
    category = "Warm"                  # Default category
    for line in analysis.split('\n'):
        if line.startswith('CATEGORY:'):
            cat = line.split(':')[1].strip().upper()  # Get category text
            if cat in ["HOT", "WARM", "COLD"]:        # Validate it
                category = cat.capitalize()            # Normalize to Title Case

    # Extract the recommended action
    recommended_action = "Follow up soon"  # Default action
    for line in analysis.split('\n'):
        if line.startswith('RECOMMENDED_ACTION:'):
            recommended_action = line.split(':', 1)[1].strip()  # Get the action text

    print(f"[Agent 1] {state['company']}: Score {score}/10 — {category}")

    # Return updated state with qualification results
    return {
        **state,
        "lead_score": score,
        "lead_category": category,
        "qualification_analysis": analysis,
        "recommended_action": recommended_action,
        "pipeline_stage": "qualified"
    }


# ============================================================
# AGENT 2: EMAIL DRAFTER
# ============================================================
# Creates a personalized outreach email based on the lead's profile and temperature
def email_drafter_agent(state: SalesPipelineState) -> SalesPipelineState:
    """
    Agent 2: Email Drafter
    Creates a personalized outreach email matched to the lead's temperature.
    Hot leads get urgent, direct emails. Cold leads get educational content.
    """
    print(f"\n[Agent 2] Email Drafter creating {state['lead_category']} email for {state['company']}...")

    # Different tones for different lead temperatures
    # This is a key insight from sales science: one template does not fit all
    if state['lead_category'] == "Hot":
        tone_instructions = """Write a DIRECT, URGENT outreach email. This is a hot lead.
- Reference their specific pain points immediately
- Propose a concrete next step (demo, call, meeting) with specific times
- Convey urgency without being pushy
- Keep it short (150-200 words) — hot leads are busy decision-makers
- Subject line should create curiosity or address the pain point directly"""
    elif state['lead_category'] == "Warm":
        tone_instructions = """Write a VALUE-FOCUSED, EDUCATIONAL email. This is a warm lead.
- Lead with a relevant insight or statistic about their industry
- Connect our solution to their stated pain points
- Offer a low-commitment resource (case study, webinar, article)
- Soft call to action — invite a conversation, not a hard sell
- Keep it to 200-250 words, professional and helpful in tone"""
    else:  # Cold lead
        tone_instructions = """Write a THOUGHT LEADERSHIP, LONG-TERM email. This is a cold lead.
- Start with an insightful observation about their industry challenge
- Do NOT pitch the product directly — build awareness and trust
- Share a relevant statistic or case study
- Offer a free resource with no strings attached
- Very soft close — just invite them to learn more when timing is right
- 200-250 words, consultative tone"""

    # System prompt sets up Claude as a top sales development rep
    system_prompt = f"""You are a world-class sales development representative (SDR) known for
extremely high email open and response rates. Your emails are personal, relevant, and never feel spammy.

{tone_instructions}

Always format your response as:
SUBJECT: [email subject line]
---
[email body]

Use [FIRST_NAME] as a placeholder for the contact's first name.
Sign off as "Alex Johnson, Account Executive" from "CloudSuite Pro"."""

    # Provide the lead context so Claude can personalize the email
    human_message = f"""Write an outreach email for this lead:

Company: {state['company']}
Contact: {state['contact_name']}
Industry: {state['industry']}
Company Size: {state['company_size']}
Their Pain Points: {state['pain_points']}
Current Solution: {state['current_solution']}
Lead Score: {state['lead_score']}/10 ({state['lead_category']})
Recommended Action: {state['recommended_action']}"""

    # Call Claude to generate the personalized email
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    # Replace the placeholder with the actual contact's first name
    email_text = response.content
    first_name = state['contact_name'].split()[0]  # Get first name from full name
    email_text = email_text.replace("[FIRST_NAME]", first_name)  # Personalize the email

    print(f"[Agent 2] Email drafted for {state['contact_name']} at {state['company']}")

    return {
        **state,
        "outreach_email": email_text,  # Store the personalized email
        "pipeline_stage": "email_drafted"
    }


# ============================================================
# AGENT 3: CRM UPDATER
# ============================================================
# Records the lead and all pipeline results in the simulated CRM database
def crm_updater_agent(state: SalesPipelineState) -> SalesPipelineState:
    """
    Agent 3: CRM Updater
    Writes/updates the lead record in our local JSON CRM database.
    Simulates what a real Salesforce or HubSpot integration would do.
    """
    print(f"\n[Agent 3] CRM Updater recording {state['company']} in database...")

    # Load the existing CRM data
    crm_data = load_crm()              # Read current CRM file

    # Build the CRM record for this lead
    # In Salesforce, each of these would be a field in the Lead object
    crm_record = {
        "lead_id": state['lead_id'],           # Unique identifier
        "company": state['company'],           # Company name
        "contact_name": state['contact_name'], # Primary contact
        "contact_email": state['contact_email'], # Email for outreach
        "industry": state['industry'],         # Industry segment
        "company_size": state['company_size'], # Company size
        "annual_budget": state['annual_budget'], # Budget info
        "pain_points": state['pain_points'],   # Their stated problems
        "lead_score": state['lead_score'],     # AI-generated score 1-10
        "lead_category": state['lead_category'], # Hot/Warm/Cold
        "status": "New",                       # Current deal stage
        "email_sent": True,                    # Mark that email was drafted
        "outreach_email_subject": state['outreach_email'].split('\n')[0].replace('SUBJECT: ', ''),
        "last_contact": datetime.now().isoformat(),  # Timestamp
        "created_at": datetime.now().isoformat(),    # Creation timestamp
        "notes": f"AI qualified. Score: {state['lead_score']}/10. {state['recommended_action']}",
        "qualification_summary": state['qualification_analysis'][:500],  # First 500 chars
        "pipeline_stage": "Outreach"           # CRM stage name
    }

    # Save the record to our CRM (keyed by lead_id)
    crm_data[state['lead_id']] = crm_record    # Upsert: insert or update
    save_crm(crm_data)                          # Write back to JSON file

    print(f"[Agent 3] Lead {state['lead_id']} saved to CRM with status: {crm_record['status']}")

    return {
        **state,
        "crm_record": crm_record,              # Store the record in state
        "pipeline_stage": "crm_updated"
    }


# ============================================================
# AGENT 4: FOLLOW-UP SCHEDULER
# ============================================================
# Determines when and how to follow up based on lead temperature
def follow_up_scheduler_agent(state: SalesPipelineState) -> SalesPipelineState:
    """
    Agent 4: Follow-up Scheduler
    Creates a structured follow-up plan based on lead score and category.
    Hot leads: follow up in 1 day. Warm: 3 days. Cold: 1 week.
    """
    print(f"\n[Agent 4] Follow-up Scheduler planning next steps for {state['company']}...")

    # Calculate follow-up dates based on lead temperature
    today = datetime.now()             # Current date and time

    if state['lead_category'] == "Hot":
        # Hot leads need immediate attention — every hour matters
        first_follow_up = today + timedelta(days=1)   # Tomorrow
        second_follow_up = today + timedelta(days=3)  # Day 3
        third_follow_up = today + timedelta(days=7)   # Day 7
        urgency = "HIGH — respond same business day if they reply"
        touch_sequence = "Call attempt + email sequence + LinkedIn message"
    elif state['lead_category'] == "Warm":
        # Warm leads need nurturing — give them space to think
        first_follow_up = today + timedelta(days=3)   # Day 3
        second_follow_up = today + timedelta(days=7)  # Day 7
        third_follow_up = today + timedelta(days=14)  # Day 14
        urgency = "MEDIUM — respond within 24 hours if they reply"
        touch_sequence = "Email sequence with value content"
    else:
        # Cold leads need long-term nurturing — do not waste too many touches
        first_follow_up = today + timedelta(days=7)   # 1 week
        second_follow_up = today + timedelta(days=21) # 3 weeks
        third_follow_up = today + timedelta(days=45)  # 6 weeks
        urgency = "LOW — add to drip campaign, revisit quarterly"
        touch_sequence = "Automated email drip with educational content"

    # System prompt for Claude to generate the detailed follow-up plan
    system_prompt = """You are a sales operations specialist who creates precise follow-up sequences.
Write a structured follow-up plan with specific actions, not just dates.
Include what to say in follow-up emails (brief summaries), LinkedIn strategy, and
when/how to escalate to a phone call. Keep it practical and actionable."""

    # Build context for the follow-up plan
    human_message = f"""Create a follow-up schedule for this lead:

Company: {state['company']}
Contact: {state['contact_name']} ({state['contact_email']})
Lead Category: {state['lead_category']} (Score: {state['lead_score']}/10)
Recommended Action: {state['recommended_action']}
Pain Points: {state['pain_points']}

Follow-up Dates:
- Touch 1: {first_follow_up.strftime('%A, %B %d, %Y')}
- Touch 2: {second_follow_up.strftime('%A, %B %d, %Y')}
- Touch 3: {third_follow_up.strftime('%A, %B %d, %Y')}

Urgency Level: {urgency}
Touch Sequence: {touch_sequence}

Write a specific, actionable follow-up plan for each touch."""

    # Call Claude to generate the detailed plan
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    # Update CRM with follow-up dates
    crm_data = load_crm()                          # Reload fresh CRM
    if state['lead_id'] in crm_data:               # Find this lead's record
        crm_data[state['lead_id']]['next_follow_up'] = first_follow_up.isoformat()
        crm_data[state['lead_id']]['follow_up_schedule'] = response.content[:300]  # Summary
        save_crm(crm_data)                         # Save updated CRM

    print(f"[Agent 4] Follow-up scheduled for {state['company']}: first touch {first_follow_up.strftime('%B %d')}")

    return {
        **state,
        "follow_up_schedule": response.content,   # Store the full schedule
        "pipeline_stage": "complete"               # Pipeline is done
    }


# ============================================================
# BUILD THE LANGGRAPH WORKFLOW
# ============================================================
def build_sales_pipeline() -> StateGraph:
    """
    Assembles all four sales agents into a sequential LangGraph workflow.
    Every lead goes through all four stages in order.
    """
    # Create the state graph
    workflow = StateGraph(SalesPipelineState)

    # ADD ALL FOUR AGENTS AS NODES
    workflow.add_node("lead_qualifier", lead_qualifier_agent)        # Agent 1
    workflow.add_node("email_drafter", email_drafter_agent)          # Agent 2
    workflow.add_node("crm_updater", crm_updater_agent)              # Agent 3
    workflow.add_node("follow_up_scheduler", follow_up_scheduler_agent)  # Agent 4

    # SET THE ENTRY POINT — where every pipeline run begins
    workflow.set_entry_point("lead_qualifier")

    # ADD SEQUENTIAL EDGES — each agent runs in order
    # Unlike Project 13, the sales pipeline is sequential (no branching)
    # Every lead goes through all four stages regardless of score
    workflow.add_edge("lead_qualifier", "email_drafter")         # 1 → 2
    workflow.add_edge("email_drafter", "crm_updater")            # 2 → 3
    workflow.add_edge("crm_updater", "follow_up_scheduler")      # 3 → 4
    workflow.add_edge("follow_up_scheduler", END)                # 4 → Done

    # Compile and return the runnable pipeline
    return workflow.compile()


# Build the pipeline once at startup
pipeline = build_sales_pipeline()   # Compile LangGraph workflow


# ============================================================
# FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title="AI Sales Pipeline Automation",
    description="LangGraph-powered B2B sales pipeline: qualifies leads, drafts emails, updates CRM",
    version="1.0.0"
)

# --- PYDANTIC MODELS ---
# Pydantic validates all incoming data automatically
class LeadData(BaseModel):
    company: str                       # Company name (required)
    contact_name: str                  # Full name of primary contact
    contact_email: str                 # Email address for outreach
    industry: str                      # Industry/sector
    company_size: str                  # Number of employees (e.g., "250-500")
    annual_budget: str                 # Estimated budget (e.g., "$50,000-$100,000")
    pain_points: str                   # Problems they want to solve
    current_solution: str              # What they currently use

class LeadResponse(BaseModel):
    lead_id: str                       # Generated unique ID
    company: str                       # Company name
    contact_name: str                  # Contact person
    lead_score: int                    # AI score 1-10
    lead_category: str                 # Hot/Warm/Cold
    qualification_analysis: str        # Full analysis from Agent 1
    recommended_action: str            # Specific recommended next step
    outreach_email: str                # Personalized email from Agent 2
    follow_up_schedule: str            # Follow-up plan from Agent 4
    pipeline_stage: str                # Final stage reached


# --- API ENDPOINTS ---

@app.post("/qualify-lead", response_model=LeadResponse)
async def qualify_lead(lead_data: LeadData):
    """
    POST /qualify-lead
    Runs a lead through the complete 4-agent sales pipeline.
    Returns score, category, personalized email, and follow-up schedule.
    """
    # Generate a unique ID for this lead
    lead_id = str(uuid.uuid4())[:8]    # Short 8-character UUID

    print(f"\n{'='*60}")
    print(f"STARTING SALES PIPELINE: {lead_data.company} ({lead_id})")
    print(f"{'='*60}")

    # Build the initial pipeline state from the incoming request data
    initial_state: SalesPipelineState = {
        "lead_id": lead_id,
        "company": lead_data.company,
        "contact_name": lead_data.contact_name,
        "contact_email": lead_data.contact_email,
        "industry": lead_data.industry,
        "company_size": lead_data.company_size,
        "annual_budget": lead_data.annual_budget,
        "pain_points": lead_data.pain_points,
        "current_solution": lead_data.current_solution,
        "lead_score": 0,               # Will be populated by Agent 1
        "lead_category": "",           # Will be populated by Agent 1
        "qualification_analysis": "",  # Will be populated by Agent 1
        "recommended_action": "",      # Will be populated by Agent 1
        "outreach_email": "",          # Will be populated by Agent 2
        "crm_record": {},              # Will be populated by Agent 3
        "follow_up_schedule": "",      # Will be populated by Agent 4
        "pipeline_stage": "starting",  # Initial stage
        "error": None                  # No errors yet
    }

    # Run the full 4-agent pipeline
    final_state = pipeline.invoke(initial_state)

    print(f"{'='*60}")
    print(f"PIPELINE COMPLETE: {final_state.get('lead_category')} lead — score {final_state.get('lead_score')}/10")
    print(f"{'='*60}")

    # Return all results
    return LeadResponse(
        lead_id=lead_id,
        company=final_state.get("company", ""),
        contact_name=final_state.get("contact_name", ""),
        lead_score=final_state.get("lead_score", 0),
        lead_category=final_state.get("lead_category", ""),
        qualification_analysis=final_state.get("qualification_analysis", ""),
        recommended_action=final_state.get("recommended_action", ""),
        outreach_email=final_state.get("outreach_email", ""),
        follow_up_schedule=final_state.get("follow_up_schedule", ""),
        pipeline_stage=final_state.get("pipeline_stage", "complete")
    )


@app.get("/leads")
async def get_all_leads():
    """
    GET /leads
    Returns all leads stored in the CRM database.
    In a real system, this would query Salesforce or HubSpot.
    """
    crm_data = load_crm()              # Load the CRM file

    if not crm_data:                   # If no leads yet
        return {"leads": [], "total": 0, "message": "No leads in CRM yet"}

    # Build a summary list (avoid returning the full analysis text which can be long)
    leads_summary = []
    for lead_id, record in crm_data.items():  # Iterate through all records
        leads_summary.append({
            "lead_id": record.get("lead_id"),
            "company": record.get("company"),
            "contact_name": record.get("contact_name"),
            "lead_score": record.get("lead_score"),
            "lead_category": record.get("lead_category"),
            "status": record.get("status"),
            "last_contact": record.get("last_contact"),
            "next_follow_up": record.get("next_follow_up", "Not scheduled")
        })

    # Sort by lead score descending (hottest leads first)
    leads_summary.sort(key=lambda x: x.get("lead_score", 0), reverse=True)

    return {
        "leads": leads_summary,
        "total": len(leads_summary),   # Total count for dashboard
        "hot_leads": sum(1 for l in leads_summary if l.get("lead_category") == "Hot"),
        "warm_leads": sum(1 for l in leads_summary if l.get("lead_category") == "Warm"),
        "cold_leads": sum(1 for l in leads_summary if l.get("lead_category") == "Cold")
    }


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """
    GET /leads/{lead_id}
    Returns the full details for a specific lead.
    """
    crm_data = load_crm()              # Load CRM

    # Search for the lead_id in the CRM records
    for record_key, record in crm_data.items():
        if record.get("lead_id") == lead_id:   # Match by lead_id field
            return record                       # Return full record

    # If not found, return 404
    raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found in CRM")


@app.get("/health")
async def health_check():
    """GET /health — Simple health check"""
    crm_data = load_crm()
    return {
        "status": "healthy",
        "service": "Sales Pipeline Automation",
        "leads_in_crm": len(crm_data)  # Show how many leads are tracked
    }


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("Starting Sales Pipeline Automation API...")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
