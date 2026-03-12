# hr_recruiter.py
# Project 13: AI-Powered HR Recruitment Pipeline
# This file builds a complete hiring pipeline using LangGraph and Claude
# The pipeline screens resumes, schedules interviews, and drafts offer letters automatically

# --- IMPORTS ---
import os                              # Access environment variables and file system
import json                            # Parse and format JSON data
from typing import TypedDict, Optional # Type hints for better code clarity
from dotenv import load_dotenv         # Load API keys from .env file
from langchain_anthropic import ChatAnthropic  # Claude AI via LangChain interface
from langchain_core.messages import HumanMessage, SystemMessage  # Message types for Claude
from langgraph.graph import StateGraph, END  # Build the workflow graph
from fastapi import FastAPI, HTTPException   # Web API framework
from pydantic import BaseModel               # Data validation for API requests
import uvicorn                               # ASGI server to run FastAPI
from datetime import datetime                # Get current timestamps

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()  # Read ANTHROPIC_API_KEY from .env file

# --- INITIALIZE CLAUDE AI MODEL ---
# claude-opus-4-6 is Anthropic's most capable model — best for complex reasoning tasks
llm = ChatAnthropic(
    model="claude-opus-4-6",           # Specify the exact model version
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),  # Use key from .env file
    max_tokens=1500                    # Limit response length to control costs
)

# --- PIPELINE STATE DEFINITION ---
# TypedDict defines the exact shape of data flowing through our LangGraph pipeline
# Every agent reads from this state and writes back to it
class RecruitmentState(TypedDict):
    resume_text: str                   # The candidate's resume (raw text)
    job_description: str               # The job requirements we're hiring for
    candidate_name: str                # Extracted candidate name
    screen_result: str                 # Full screening analysis from Agent 1
    score: int                         # Numeric score 0-100 from Agent 1
    pass_fail: str                     # "PASS" or "FAIL" decision
    interview_email: str               # Interview invitation email from Agent 2
    offer_letter: str                  # Job offer letter from Agent 3 (if score > 75)
    rejection_email: str               # Polite rejection email from Agent 4
    pipeline_status: str               # Current stage: screening/interview/offer/rejected
    error: Optional[str]               # Any error message if something goes wrong

# ============================================================
# AGENT 1: RESUME SCREENER
# ============================================================
# This agent acts as an expert HR screener
# It compares the resume against the job description and produces a score
def resume_screener_agent(state: RecruitmentState) -> RecruitmentState:
    """
    Agent 1: Resume Screener
    Evaluates a candidate's resume against the job requirements.
    Returns a numeric score and PASS/FAIL decision.
    """
    print("\n[Agent 1] Resume Screener is analyzing the candidate...")

    # Build the system prompt — this tells Claude what role to play
    system_prompt = """You are an expert HR screener with 15 years of experience at top tech companies.
Your job is to evaluate candidate resumes against job descriptions objectively and fairly.

When evaluating, consider:
- Technical skills match (40% of score)
- Years of relevant experience (30% of score)
- Education and certifications (15% of score)
- Soft skills and communication quality (15% of score)

Always respond in this EXACT format:
CANDIDATE_NAME: [extract from resume]
SCORE: [number 0-100]
DECISION: [PASS or FAIL]
STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]
WEAKNESSES:
- [weakness 1]
- [weakness 2]
REASONING: [2-3 sentences explaining the decision]

PASS requires a score of 60 or higher. Be objective and consistent."""

    # Build the human message with the actual resume and job description
    human_message = f"""Please screen this candidate:

JOB DESCRIPTION:
{state['job_description']}

CANDIDATE RESUME:
{state['resume_text']}"""

    # Call Claude with both the system prompt and human message
    response = llm.invoke([
        SystemMessage(content=system_prompt),   # Sets Claude's role and instructions
        HumanMessage(content=human_message)     # Provides the actual data to analyze
    ])

    # Store the full screening result in state
    screen_result = response.content  # Claude's complete analysis text

    # Extract the numeric score from Claude's response
    # We look for "SCORE: " and grab the number after it
    score = 50  # Default score if we can't parse it
    for line in screen_result.split('\n'):          # Loop through each line of response
        if line.startswith('SCORE:'):               # Find the score line
            try:
                score = int(line.split(':')[1].strip())  # Extract and convert to integer
            except:
                score = 50                          # Keep default if parsing fails

    # Extract candidate name from the response
    candidate_name = "Unknown Candidate"           # Default if we can't find it
    for line in screen_result.split('\n'):
        if line.startswith('CANDIDATE_NAME:'):
            candidate_name = line.split(':')[1].strip()  # Get name after the colon

    # Determine PASS or FAIL based on score threshold
    pass_fail = "PASS" if score >= 60 else "FAIL"  # 60 is the minimum passing score

    # Update the pipeline status based on decision
    pipeline_status = "screened_pass" if pass_fail == "PASS" else "screened_fail"

    print(f"[Agent 1] Result: {candidate_name} scored {score}/100 — {pass_fail}")

    # Return updated state — LangGraph merges this with existing state
    return {
        **state,                               # Keep all existing state fields
        "screen_result": screen_result,        # Add screening analysis
        "score": score,                        # Add numeric score
        "candidate_name": candidate_name,      # Add extracted name
        "pass_fail": pass_fail,                # Add PASS/FAIL decision
        "pipeline_status": pipeline_status     # Update pipeline stage
    }


# ============================================================
# AGENT 2: INTERVIEW SCHEDULER
# ============================================================
# This agent creates a professional interview invitation email
# Only runs when a candidate passes screening (score >= 60)
def interview_scheduler_agent(state: RecruitmentState) -> RecruitmentState:
    """
    Agent 2: Interview Scheduler
    Drafts a professional interview invitation email for passing candidates.
    """
    print(f"\n[Agent 2] Interview Scheduler is creating invitation for {state['candidate_name']}...")

    # Define available interview time slots for the email
    available_slots = [
        "Monday, March 16 at 10:00 AM EST",
        "Tuesday, March 17 at 2:00 PM EST",
        "Wednesday, March 18 at 11:00 AM EST",
        "Thursday, March 19 at 3:00 PM EST"
    ]

    # System prompt makes Claude act as a professional HR coordinator
    system_prompt = """You are a professional HR coordinator at a leading technology company.
You write clear, warm, and professional interview invitation emails.
The email should make the candidate excited about the opportunity while being informative.
Include: greeting, congratulations on passing screening, role name, interview format (video call via Zoom),
available time slots for them to choose from, what to expect (45-min technical + 30-min culture fit),
who they will meet with (generic titles only), and professional closing.
Keep the tone warm and professional. Use proper email formatting."""

    # Build the context for this specific candidate
    human_message = f"""Please draft an interview invitation email for this candidate:

Candidate Name: {state['candidate_name']}
Role: Senior Python Developer
Score: {state['score']}/100
Available Slots:
{chr(10).join(f'- {slot}' for slot in available_slots)}

Include all slots in the email so the candidate can choose their preference."""

    # Call Claude to generate the interview invitation
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    print(f"[Agent 2] Interview invitation email drafted for {state['candidate_name']}")

    # Return state with the new interview email added
    return {
        **state,
        "interview_email": response.content,   # Store the generated email
        "pipeline_status": "interview_scheduled"  # Update pipeline stage
    }


# ============================================================
# AGENT 3: OFFER LETTER DRAFTER
# ============================================================
# Only activates for top candidates with score >= 75
# Drafts a formal, legally-appropriate job offer letter
def offer_letter_drafter_agent(state: RecruitmentState) -> RecruitmentState:
    """
    Agent 3: Offer Letter Drafter
    Creates a formal job offer letter for high-scoring candidates (score >= 75).
    """
    print(f"\n[Agent 3] Offer Letter Drafter creating offer for {state['candidate_name']}...")

    # System prompt makes Claude act as an HR legal specialist
    system_prompt = """You are an HR legal specialist at a technology company with expertise in employment law.
You draft formal, professional offer letters that are legally appropriate.
The letter should include:
1. Date and formal header
2. Congratulations and role title
3. Start date (leave as [START DATE] placeholder)
4. Compensation: base salary range and note about final negotiation
5. Benefits overview (health, dental, 401k, PTO)
6. At-will employment clause (standard legal requirement)
7. Contingencies (background check, reference checks)
8. Response deadline (5 business days)
9. Contact information for questions
10. Professional closing with HR Director signature block

Use [PLACEHOLDER] for any specific values that would be confirmed later.
This is a template — be formal and complete."""

    # Build the human message with candidate-specific details
    human_message = f"""Draft a job offer letter for:

Candidate: {state['candidate_name']}
Position: Senior Python Developer
Salary Range: $140,000 - $165,000 annually
Department: Engineering
Reports To: VP of Engineering
Start Date: To be negotiated (use [START DATE])
Company: TechCorp Inc."""

    # Call Claude to generate the offer letter
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    print(f"[Agent 3] Offer letter drafted for {state['candidate_name']}")

    # Return state with offer letter added
    return {
        **state,
        "offer_letter": response.content,      # Store the generated offer letter
        "pipeline_status": "offer_drafted"     # Update pipeline stage to final step
    }


# ============================================================
# AGENT 4: REJECTION EMAILER
# ============================================================
# Handles candidates who scored below 60
# Writes a kind, professional rejection to preserve company reputation
def rejection_emailer_agent(state: RecruitmentState) -> RecruitmentState:
    """
    Agent 4: Rejection Emailer
    Writes a polite, professional rejection email for candidates who did not pass.
    """
    print(f"\n[Agent 4] Rejection Emailer drafting message for {state['candidate_name']}...")

    # System prompt — tone is critical here to protect company's employer brand
    system_prompt = """You are a compassionate HR professional who values candidate experience.
You write rejection emails that are:
- Kind and respectful (candidates talk to other candidates)
- Specific enough to be helpful but not discouraging
- Encouraging about future opportunities
- Brief (3-4 paragraphs maximum)
- Professional and warm in tone

Never say the candidate "failed" — use phrases like "not the right fit at this time" or
"we've decided to move forward with other candidates."
Always thank them for their time and encourage them to apply to future positions."""

    # Build the human message
    human_message = f"""Please draft a rejection email for:

Candidate: {state['candidate_name']}
Role Applied For: Senior Python Developer
Their score was below our minimum threshold.
Reason area: {state['pass_fail']} (score: {state['score']}/100)"""

    # Call Claude to generate the rejection email
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ])

    print(f"[Agent 4] Rejection email drafted for {state['candidate_name']}")

    # Return state with rejection email added
    return {
        **state,
        "rejection_email": response.content,  # Store the generated rejection email
        "pipeline_status": "rejected"         # Update pipeline stage
    }


# ============================================================
# ROUTING LOGIC
# ============================================================
# This function decides which agent runs next after screening
# LangGraph uses this to determine the path through the workflow
def route_after_screening(state: RecruitmentState) -> str:
    """
    Routing function: decides next step based on screening score.
    Returns the name of the next node to execute.
    """
    score = state.get("score", 0)      # Get the score, default to 0 if missing

    if score >= 75:
        # High score: go to interview scheduling first, then offer letter
        print(f"[Router] Score {score} >= 75: Routing to INTERVIEW (offer letter will follow)")
        return "interview_scheduler"   # Route to Agent 2
    elif score >= 60:
        # Decent score: go to interview scheduling only (no offer letter yet)
        print(f"[Router] Score {score} >= 60: Routing to INTERVIEW only")
        return "interview_scheduler"   # Route to Agent 2
    else:
        # Low score: go directly to rejection
        print(f"[Router] Score {score} < 60: Routing to REJECTION")
        return "rejection_emailer"     # Route to Agent 4


def route_after_interview(state: RecruitmentState) -> str:
    """
    Routing function: after interview scheduling, decide if offer letter is needed.
    Top candidates (score >= 75) also get an offer letter drafted proactively.
    """
    score = state.get("score", 0)      # Get the score again

    if score >= 75:
        # Top candidate: also draft an offer letter
        print(f"[Router] Score {score} >= 75: Also drafting OFFER LETTER")
        return "offer_letter_drafter"  # Route to Agent 3
    else:
        # Good candidate but not top tier: interview invitation only
        print(f"[Router] Score {score} < 75: Pipeline complete (interview only)")
        return END                     # End the pipeline here


# ============================================================
# BUILD THE LANGGRAPH WORKFLOW
# ============================================================
def build_recruitment_pipeline() -> StateGraph:
    """
    Assembles all agents into a LangGraph workflow.
    Returns a compiled, runnable pipeline.
    """
    # Create the graph, specifying our state shape
    workflow = StateGraph(RecruitmentState)

    # ADD NODES (agents) to the graph
    workflow.add_node("resume_screener", resume_screener_agent)    # Node 1
    workflow.add_node("interview_scheduler", interview_scheduler_agent)  # Node 2
    workflow.add_node("offer_letter_drafter", offer_letter_drafter_agent)  # Node 3
    workflow.add_node("rejection_emailer", rejection_emailer_agent)  # Node 4

    # SET THE ENTRY POINT — this is where every pipeline run starts
    workflow.set_entry_point("resume_screener")

    # ADD CONDITIONAL EDGES — the routing logic
    # After resume_screener, call route_after_screening to decide next step
    workflow.add_conditional_edges(
        "resume_screener",             # From this node...
        route_after_screening,         # ...use this function to decide...
        {
            "interview_scheduler": "interview_scheduler",  # ...route to interview
            "rejection_emailer": "rejection_emailer"       # ...or route to rejection
        }
    )

    # After interview_scheduler, decide if offer letter is needed
    workflow.add_conditional_edges(
        "interview_scheduler",         # From this node...
        route_after_interview,         # ...use this function to decide...
        {
            "offer_letter_drafter": "offer_letter_drafter",  # Route to offer letter
            END: END                   # Or end the pipeline
        }
    )

    # After offer_letter_drafter, always end
    workflow.add_edge("offer_letter_drafter", END)  # Final step: end pipeline

    # After rejection_emailer, always end
    workflow.add_edge("rejection_emailer", END)     # Final step: end pipeline

    # Compile the graph into a runnable application
    return workflow.compile()


# ============================================================
# PIPELINE STATISTICS TRACKER
# ============================================================
# Simple in-memory tracker to show pipeline statistics
pipeline_stats = {
    "total_processed": 0,    # Total resumes screened
    "passed": 0,             # Candidates who passed screening
    "rejected": 0,           # Candidates who failed screening
    "offers_drafted": 0,     # Offer letters created (score >= 75)
    "interviews_scheduled": 0  # Interview invitations sent
}

# Build the pipeline once at startup (not on every request)
pipeline = build_recruitment_pipeline()  # Compile the LangGraph workflow

# ============================================================
# FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title="AI HR Recruitment Pipeline",          # API title shown in docs
    description="LangGraph-powered hiring pipeline that screens resumes, schedules interviews, and drafts offers",
    version="1.0.0"                              # API version
)

# --- REQUEST/RESPONSE MODELS ---
# Pydantic models validate incoming data automatically
class ScreenRequest(BaseModel):
    resume_text: str          # The candidate's resume as plain text
    job_description: str      # The job requirements

class ScreenResponse(BaseModel):
    candidate_name: str       # Extracted from resume
    score: int                # Screening score 0-100
    pass_fail: str            # "PASS" or "FAIL"
    pipeline_status: str      # Final stage reached
    screen_result: str        # Full screening analysis
    interview_email: str      # Interview invitation (if passed)
    offer_letter: str         # Offer letter (if score >= 75)
    rejection_email: str      # Rejection email (if failed)


# --- API ENDPOINTS ---

@app.post("/screen", response_model=ScreenResponse)
async def screen_candidate(request: ScreenRequest):
    """
    POST /screen
    Runs a resume through the complete HR pipeline.
    Input: resume_text and job_description
    Output: screening score, decision, and all generated documents
    """
    # Validate that we received actual content
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty")
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    # Build the initial state for this pipeline run
    initial_state: RecruitmentState = {
        "resume_text": request.resume_text,
        "job_description": request.job_description,
        "candidate_name": "",          # Will be populated by screener
        "screen_result": "",           # Will be populated by screener
        "score": 0,                    # Will be populated by screener
        "pass_fail": "",               # Will be populated by screener
        "interview_email": "",         # Will be populated if score >= 60
        "offer_letter": "",            # Will be populated if score >= 75
        "rejection_email": "",         # Will be populated if score < 60
        "pipeline_status": "starting", # Initial status
        "error": None                  # No errors yet
    }

    # Run the pipeline — LangGraph handles all the routing automatically
    print("\n" + "="*60)
    print("STARTING RECRUITMENT PIPELINE")
    print("="*60)

    final_state = pipeline.invoke(initial_state)  # Execute the full pipeline

    # Update statistics based on the result
    pipeline_stats["total_processed"] += 1
    if final_state.get("pass_fail") == "PASS":
        pipeline_stats["passed"] += 1
        pipeline_stats["interviews_scheduled"] += 1
    else:
        pipeline_stats["rejected"] += 1
    if final_state.get("offer_letter"):
        pipeline_stats["offers_drafted"] += 1

    print("="*60)
    print(f"PIPELINE COMPLETE: {final_state.get('pipeline_status')}")
    print("="*60)

    # Return the complete results as a structured response
    return ScreenResponse(
        candidate_name=final_state.get("candidate_name", "Unknown"),
        score=final_state.get("score", 0),
        pass_fail=final_state.get("pass_fail", "FAIL"),
        pipeline_status=final_state.get("pipeline_status", "complete"),
        screen_result=final_state.get("screen_result", ""),
        interview_email=final_state.get("interview_email", ""),
        offer_letter=final_state.get("offer_letter", ""),
        rejection_email=final_state.get("rejection_email", "")
    )


@app.get("/pipeline-status")
async def get_pipeline_status():
    """
    GET /pipeline-status
    Returns statistics about how many candidates have been processed.
    Useful for HR managers to track pipeline activity.
    """
    return {
        "statistics": pipeline_stats,              # Return all stats
        "timestamp": datetime.now().isoformat(),   # When this was checked
        "pipeline_health": "operational"           # Always operational if server is running
    }


@app.get("/health")
async def health_check():
    """
    GET /health
    Simple health check endpoint.
    Returns 200 OK if the server is running.
    """
    return {"status": "healthy", "service": "HR Recruitment Pipeline"}


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    # Run the FastAPI server when this script is executed directly
    print("Starting HR Recruitment Pipeline API...")
    print("API Documentation available at: http://localhost:8000/docs")
    uvicorn.run(
        app,                    # The FastAPI application
        host="0.0.0.0",         # Listen on all network interfaces
        port=8000,              # Port number
        reload=False            # Disable auto-reload in production
    )
