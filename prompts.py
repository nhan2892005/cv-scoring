"""LLM prompts for each stage of the CV screening pipeline.

Design principle: every prompt forces the model to act like a senior hiring
manager + recruiter + CV coach, reason semantically, and return strict JSON.
"""

JD_EXTRACTION_PROMPT = """You are a Senior Technical Recruiter with 10+ years of experience.
Read this Job Description and extract a structured understanding of it.

Return STRICT JSON only, matching this schema:
{
  "role_title": "string",
  "seniority_level": "Intern | Junior | Mid | Senior | Lead | Principal | Manager | Director",
  "domain": "string (industry / product area)",
  "required_skills": ["..."],
  "nice_to_have_skills": ["..."],
  "key_responsibilities": ["..."],
  "required_years_experience": "string (e.g. '3-5 years' or 'not specified')",
  "soft_skills": ["..."],
  "hidden_expectations": ["things recruiters usually infer but aren't explicit"]
}

Rules:
- Be specific. Do NOT invent requirements.
- Split "required" vs "nice-to-have" based on language cues ("must", "required" vs "bonus", "plus").
- "hidden_expectations" is your senior recruiter read-between-the-lines insight.

JOB DESCRIPTION:
---
{jd}
---
"""


CV_EXTRACTION_PROMPT = """You are a Senior Recruiter reading a candidate CV.
Extract a structured profile. Return STRICT JSON only:

{
  "candidate_name": "string or 'unknown'",
  "headline": "one-line profile",
  "total_years_experience": "string",
  "current_role": "string",
  "career_trajectory": "string (describe progression: ascending, lateral, scattered, etc.)",
  "domain_expertise": ["..."],
  "core_strengths": ["..."],
  "technical_skills": ["..."],
  "soft_skills": ["..."],
  "notable_achievements": ["quantified wins if any"],
  "education": ["..."],
  "bullets": [
     {"role": "string", "company": "string", "text": "original bullet text"}
  ],
  "red_flag_signals": ["short job tenures, gaps, buzzword spam, vague claims"]
}

Rules:
- Preserve original bullet text verbatim (we'll critique it later).
- Infer trajectory from dates + titles.
- Do not fabricate.

CV TEXT:
---
{cv}
---
"""


EVALUATION_PROMPT = """You are a panel of THREE senior experts reviewing a candidate for a specific role:
  1. Senior Hiring Manager (10+ yrs) — decides hire / no hire
  2. Senior Technical Recruiter — checks JD fit, ATS, positioning
  3. Senior CV Coach — rewrites weak content with impact + metrics

You already have structured JD and CV understandings below. Now produce the FINAL
evaluation as STRICT JSON. No prose outside JSON.

Scoring rubric (sum to overall_score out of 100):
  - jd_match          (0-40)  semantic + transferable skill match, not just keywords
  - cv_quality        (0-25)  bullets with impact, clarity, measurable results
  - experience_depth  (0-10)  depth vs. required seniority
  - formatting        (0-15)  structure, scannability, ATS-friendliness
  - risk              (0-10)  inverse of red flags (10 = no risk)

Grade mapping:
  85+ Strong Hire | 70-84 Good Fit | 50-69 Moderate | <50 Weak

OUTPUT SCHEMA (fill every field, arrays may be empty but must exist):
{{
  "overall_score": 0,
  "grade": "Strong Hire | Good Fit | Moderate | Weak",
  "confidence": 0.0,
  "summary": "3-5 sentence hiring-manager style verdict",
  "dimension_scores": {{
    "jd_match": 0,
    "cv_quality": 0,
    "experience_depth": 0,
    "formatting": 0,
    "risk": 0
  }},
  "strengths": ["specific, evidence-backed"],
  "weaknesses": ["specific, evidence-backed"],
  "improvements": {{
    "content_issues": [
      {{
        "issue_type": "weak_bullet | no_metrics | vague_claim | buzzword_spam",
        "original": "verbatim bullet from CV",
        "problem": "why this is weak",
        "improved_version": "rewritten bullet with impact + metrics (may use realistic placeholder numbers in [brackets])"
      }}
    ],
    "skill_gaps": {{
      "critical_missing": ["skills required by JD the candidate clearly lacks"],
      "secondary_missing": ["nice-to-haves missing"],
      "transferable": ["skills candidate has that partially cover gaps"]
    }},
    "positioning_issues": [
      {{
        "problem": "Your CV is positioned as X but role requires Y",
        "rewritten_summary": "new 2-3 sentence professional summary tailored to JD"
      }}
    ],
    "experience_issues": ["unclear progression, thin depth in X, etc."],
    "formatting_issues": ["ATS-unfriendly, hard to scan, etc."],
    "red_flags": [
      {{"flag": "string", "risk_explanation": "string"}}
    ]
  }},
  "suggestions": {{
    "micro_fixes": ["bullet-level rewrites, wording, metrics — be concrete"],
    "macro_fixes": ["section reorder, new summary, highlight X experience"],
    "strategic_advice": ["e.g. 'You lack cloud ops; get AWS cert to pass HR screens'"]
  }},
  "hiring_decision": {{
    "recommendation": "Hire | Consider | Reject",
    "reason": "crisp justification grounded in the scores and evidence",
    "top_risks": ["..."]
  }}
}}

CRITICAL RULES:
- NEVER be generic. Every weakness must cite a bullet, a missing skill, or a concrete gap.
- Every improved_version MUST be materially better: add impact verb + scope + metric.
- Semantic matching: "built REST APIs in Flask" ≈ "backend services in Python" — credit it.
- If the candidate is clearly wrong for the role, say so. Do not soften.
- dimension_scores MUST sum to overall_score.

---
JD UNDERSTANDING (JSON):
{jd_json}

---
CV UNDERSTANDING (JSON):
{cv_json}

---
RAW CV TEXT (for bullet-level quoting):
{cv_raw}
"""
