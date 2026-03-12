# Project 13 Transcript: AI-Powered HR Recruitment Pipeline

**Setting:** Online learning session, student and AI coach working together.

---

**Coach:** Welcome to Phase 5! This is the real-world section of the course. Everything you build from here is production-grade. Before we touch any code, I want to ask you something: have you ever applied for a job at a big tech company?

**Student:** Yeah, a couple times. Usually I just never hear back, which is frustrating.

**Coach:** That silence is actually very common. Here is what is probably happening on the other end: companies like Google, Meta, and Amazon receive millions of applications per year. Google alone gets around 3 million applications annually for roughly 20,000 positions. That is a 150:1 ratio. They physically cannot have humans read every resume. So they use AI to do initial screening. Today you are going to build the system that decided your fate.

**Student:** Oh wow. That is kind of a strange feeling.

**Coach:** It should feel strange. That is why we have a whole ethics section in the README. But first, let us understand the architecture. Open `hr_recruiter.py` and tell me what you see at the top.

**Student:** I see it imports LangGraph's StateGraph, and there is a TypedDict called RecruitmentState. It has fields for resume_text, job_description, score, pass_fail, interview_email, offer_letter, rejection_email, and pipeline_status.

**Coach:** Perfect. Why do you think we use a TypedDict for the state instead of just a regular dictionary?

**Student:** Because... type safety? So we know exactly what fields are in the state?

**Coach:** Exactly. LangGraph needs to know the shape of your data so it can merge partial updates from each agent. Every agent receives the full state, makes changes to specific fields, and returns the updated state. LangGraph merges those changes automatically. Now look at the four agents. What does each one do?

**Student:** Agent 1 screens the resume, Agent 2 schedules interviews, Agent 3 writes offer letters for high scorers, and Agent 4 sends rejections to people who did not pass.

**Coach:** And what is the routing logic? Look at the `route_after_screening` function.

**Student:** If the score is 75 or above, it goes to interview scheduling. If it is 60 to 74, it also goes to interview scheduling. And below 60, it goes to the rejection emailer.

**Coach:** So both 60+ paths go to interview? What is the difference between them?

**Student:** Oh, I see — there is a second routing function `route_after_interview`. After the interview agent runs, it checks the score again. If the score is 75 or above, it also runs the offer letter drafter. If below 75, the pipeline ends after the interview email.

**Coach:** Exactly right. So top candidates get: screening + interview invitation + offer letter drafted proactively. Good candidates get: screening + interview invitation. Poor candidates get: screening + rejection email. Three different paths, all handled by the same LangGraph workflow. Let us run it and see.

**Student:** Okay, I have my `.env` file set up with my API key. Running `python hr_recruiter.py` now.

**Coach:** You should see the uvicorn server start. Now open a second terminal and we will test with three different resumes. Start with the strong candidate.

**Student:** Running this Python script to call the API with `strong_candidate.txt`...

```
STARTING RECRUITMENT PIPELINE
==================================================
[Agent 1] Resume Screener is analyzing the candidate...
[Agent 1] Result: Alexandra Chen scored 92/100 — PASS
[Router] Score 92 >= 75: Routing to INTERVIEW (offer letter will follow)
[Agent 2] Interview Scheduler is creating invitation for Alexandra Chen...
[Agent 2] Interview invitation email drafted for Alexandra Chen
[Router] Score 92 >= 75: Also drafting OFFER LETTER
[Agent 3] Offer Letter Drafter creating offer for Alexandra Chen...
[Agent 3] Offer letter drafted for Alexandra Chen
==================================================
PIPELINE COMPLETE: offer_drafted
```

**Coach:** Look at that — 92/100, and the pipeline ran all three positive agents. What does the interview email look like?

**Student:** It is a really professional email. It says "Dear Alexandra, we are delighted to inform you that your application for the Senior Python Developer position has exceeded our expectations..." and then lists all the interview slots.

**Coach:** Now look at the offer letter.

**Student:** It is a full formal offer letter! It has the date, her name, the role, salary range of $140K-$165K, benefits, an at-will employment clause, and a 5-business-day deadline to respond. This would take an HR person 30-45 minutes to write from scratch.

**Coach:** Now you understand the business value. Let us try the average candidate.

**Student:** Running with `average_candidate.txt`...

```
[Agent 1] Resume Screener is analyzing the candidate...
[Agent 1] Result: Marcus Johnson scored 67/100 — PASS
[Router] Score 67 >= 60: Routing to INTERVIEW only
[Agent 2] Interview Scheduler is creating invitation for Marcus Johnson...
[Agent 2] Interview invitation email drafted for Marcus Johnson
[Router] Score 67 < 75: Pipeline complete (interview only)
PIPELINE COMPLETE: interview_scheduled
```

**Student:** He got an interview invitation but no offer letter. That makes sense — he passed but is not a top-tier candidate.

**Coach:** Correct. The interview invitation goes out, and if Marcus impresses in the interview, an offer letter gets drafted by a human at that stage. The AI does not make the final hiring decision — it routes the workflow. Now try the weak candidate.

**Student:** Running with `weak_candidate.txt`...

```
[Agent 1] Resume Screener is analyzing the candidate...
[Agent 1] Result: Derek Smith scored 23/100 — FAIL
[Router] Score 23 < 60: Routing to REJECTION
[Agent 4] Rejection Emailer drafting message for Derek Smith...
[Agent 4] Rejection email drafted for Derek Smith
PIPELINE COMPLETE: rejected
```

**Student:** Poor Derek. What does the rejection say?

**Coach:** Read it out loud.

**Student:** "Dear Derek, thank you so much for taking the time to apply for the Senior Python Developer position at TechCorp Inc. We truly appreciate your interest in joining our team and the effort you put into your application. After careful consideration, we have decided to move forward with candidates whose experience more closely aligns with the specific requirements of this role at this time. This was a difficult decision, as we received many strong applications..." It goes on like that. It is actually really kind.

**Coach:** That kindness is intentional and strategic. Derek will remember how TechCorp treated him. He might apply again in 3 years when he has more experience. He will tell his developer friends about their positive rejection experience. Compare that to a company that just never responds — which one would you rather apply to?

**Student:** TechCorp for sure.

**Coach:** Now I want to talk about something uncomfortable. What if the AI is biased?

**Student:** Like... what do you mean?

**Coach:** Amazon built an AI recruiting tool that they had to scrap because it was systematically downgrading resumes with the word "women's" in them. Resumes that mentioned "women's chess club" or "women's coding bootcamp" scored lower. The AI was not explicitly told to discriminate — it learned from historical hiring data from a male-dominated industry.

**Student:** That is really disturbing. Could our system do that?

**Coach:** Our system uses Claude, not a model trained on historical hiring data, which reduces this particular risk. But consider this: what does Claude know? It was trained on human-generated text from the internet. If that text contains biases — and it does — Claude might score certain types of resumes lower. Names that signal demographic background, schools that signal socioeconomic status, career gaps that disproportionately affect women, gaps from caregiving responsibilities...

**Student:** So what do we do about it?

**Coach:** Read the ethics section in the README carefully. The key points are: audit your system regularly (do scores vary suspiciously by demographic signals?), always have humans review edge cases, be transparent with candidates about AI use, and never let AI be the only decision-maker for rejections.

**Student:** I noticed the system requires a score of 60 to pass. Who decided 60?

**Coach:** We did — in this educational example. In a real system, that threshold should be calibrated empirically. You would look at historical data: "candidates who scored above X eventually became high performers" and "candidates who scored below X rarely made it through the interview." Without that data, 60 is an arbitrary guess. This is another reason AI screening needs careful validation.

**Student:** Now let me check the pipeline statistics endpoint.

**Coach:** Yes, run `curl http://localhost:8000/pipeline-status`.

**Student:** It shows: total_processed: 3, passed: 2, rejected: 1, offers_drafted: 1, interviews_scheduled: 2. So I can track the funnel in real time.

**Coach:** That is your hiring funnel dashboard. In a real system, you would track this over time, compare it across job roles, and look for patterns. If your rejection rate is 98%, either the job requirements are too strict, or the AI threshold is too high. If your rejection rate is 20%, you might need stricter requirements.

**Student:** This is making me see job searching completely differently. When I apply and do not hear back, it is probably an AI that filtered me out.

**Coach:** Very likely. And here is the actionable takeaway: tailor your resume to the specific job description. Use the same keywords. AI systems often do keyword matching as part of their evaluation. A resume optimized for the actual requirements will score significantly higher.

**Student:** That feels a bit like gaming the system.

**Coach:** It is also just good communication — presenting yourself clearly and relevantly to your audience. Hiring has always rewarded candidates who understand what the employer needs and communicate how they meet those needs. AI screening just makes the stakes of clarity higher.

**Student:** One more question — could I use this system to screen my own resume before applying?

**Coach:** Absolutely. In fact, that is a great way to practice. Run your own resume against job descriptions you are interested in, see what score you get, read the weaknesses the AI identifies, and decide what to address. You have just built yourself a free resume consultant.

**Student:** I am going to do that tonight. This was a fantastic project.

**Coach:** Great work. Project 13 complete. Next up: automating a sales pipeline. We take the same multi-agent pattern and apply it to a completely different domain — lead qualification and CRM management.
