# AI CV Screening — Hiring Assistant + CV Coach

Streamlit app that screens a CV against a Job Description using **Claude Sonnet 4.6**
with adaptive thinking, acting as a panel of senior experts
(Senior Hiring Manager + Recruiter + CV Coach). Not keyword matching — it does
semantic reasoning, multi-dimensional scoring, concrete bullet rewrites,
skill-gap diagnosis, red-flag detection, and a hire/consider/reject verdict.

## Architecture

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌─────────────┐
│  JD text   │───▶ │ JD extract │                   ┌─▶ │ Evaluation  │
└────────────┘     └────────────┘                   │   │  + Scoring  │
                                    ─ merge ─ ─ ─ ─ ┤   │ + Rewrites  │
┌────────────┐     ┌────────────┐                   │   │ + Decision  │
│ CV (PDF/   │───▶ │ CV extract │ ──────────────────┘   └─────────────┘
│ DOCX/TXT)  │     └────────────┘                              │
└────────────┘                                                 ▼
                                                        Streamlit UI
```

Stages:
1. **JD Understanding** — extract required/nice-to-have skills, seniority, hidden expectations.
2. **CV Understanding** — extract profile, trajectory, bullets verbatim, red-flag signals.
3. **Evaluation** — full rubric scoring + weak-bullet rewrites + gap analysis + hiring decision.

Scoring rubric (100 pts): `jd_match 40 · cv_quality 25 · experience_depth 10 · formatting 15 · risk 10`

## Files

- [app.py](app.py) — Streamlit UI
- [ai_engine.py](ai_engine.py) — LLM pipeline orchestration
- [prompts.py](prompts.py) — Senior-recruiter-grade prompts
- [cv_parser.py](cv_parser.py) — PDF / DOCX / TXT extraction
- [samples/sample_jd.txt](samples/sample_jd.txt), [samples/sample_cv.txt](samples/sample_cv.txt) — demo inputs

## Setup

```bash
cd /Users/vothuongbao/CV_Scoring
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and put your ANTHROPIC_API_KEY
```

## Run

```bash
streamlit run app.py
```

Then in the browser:
1. Paste JD in the sidebar (or load `samples/sample_jd.txt`).
2. Upload a CV (PDF/DOCX/TXT — try `samples/sample_cv.txt`).
3. Click **🚀 Analyze**.

## Model

Default **`claude-sonnet-4-6`** with adaptive thinking
(`thinking={"type": "adaptive"}`) — Claude decides when and how much to reason
per request. Override the model by:
- setting `CV_SCORING_MODEL` in `.env` (e.g. `claude-opus-4-6` for max quality,
  or `claude-haiku-4-5` for cheapest), or
- editing the **Model** field in the sidebar at runtime.

Each analysis makes 3 Claude calls: JD extraction → CV extraction → full
evaluation with scoring, rewrites, and hiring decision. Requests are streamed
(`messages.stream` + `get_final_message`) to avoid HTTP timeouts on long
structured JSON outputs.

## Demo

With `samples/sample_jd.txt` (Senior Backend / Fintech) and `samples/sample_cv.txt`
(a mid-level engineer with vague bullets), expect roughly:

- Score: ~45–55 / 100, grade **Moderate / Weak**
- Decision: **Consider** or **Reject**
- Content issues: every bullet flagged as weak, concrete rewrites added (impact + metrics)
- Critical missing: AWS, distributed systems, on-call, mentoring at scale
- Positioning: rewritten summary repositioning toward backend depth
- Strategic advice: specific AWS / distributed-systems learning path to pass HR

## Extending to multi-agent

`ai_engine.py` already splits the pipeline by stage. To evolve into a true
multi-agent system (HR agent + Tech agent + Hiring Manager agent), add one
call per persona in `screen_candidate`, then a final reconciliation call that
merges their JSON verdicts.
