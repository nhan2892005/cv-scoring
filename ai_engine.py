"""AI pipeline on Claude API: JD understanding -> CV understanding -> Evaluation.

Uses the Anthropic SDK with Claude Sonnet 4.6. Every stage returns strict JSON;
we stream to avoid HTTP timeouts on long outputs. A `progress` callback lets the
UI log each pipeline step as it happens.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

import anthropic

ProgressFn = Callable[[str], None]

from prompts import (
    CV_EXTRACTION_PROMPT,
    EVALUATION_PROMPT,
    JD_EXTRACTION_PROMPT,
)

DEFAULT_MODEL = os.getenv("CV_SCORING_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = (
    "You are a panel of senior hiring experts: a Senior Hiring Manager (10+ yrs), "
    "a Senior Technical Recruiter, and a Senior CV Coach. "
    "You reason semantically like a real recruiter, never do keyword matching, "
    "and you ALWAYS return strict valid JSON only — no prose, no markdown fences."
)


@dataclass
class ScreeningResult:
    jd_understanding: dict[str, Any]
    cv_understanding: dict[str, Any]
    evaluation: dict[str, Any]


def _client(api_key: str | None = None) -> anthropic.Anthropic:
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Put it in .env or pass it via the sidebar."
        )
    return anthropic.Anthropic(api_key=key)


def _chat_json(
    client: anthropic.Anthropic,
    model: str,
    user_prompt: str,
    max_tokens: int = 16000,
    progress: ProgressFn | None = None,
) -> dict:
    """Stream a Claude request and parse the full JSON response."""
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        message = stream.get_final_message()

    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if progress:
        usage = getattr(message, "usage", None)
        if usage is not None:
            progress(
                f"   ↳ tokens: in {usage.input_tokens}, out {usage.output_tokens}"
            )
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
        return json.loads(cleaned)


def extract_jd(
    client: anthropic.Anthropic,
    jd_text: str,
    model: str = DEFAULT_MODEL,
    progress: ProgressFn | None = None,
) -> dict:
    prompt = JD_EXTRACTION_PROMPT.replace("{jd}", jd_text)
    return _chat_json(client, model, prompt, progress=progress)


def extract_cv(
    client: anthropic.Anthropic,
    cv_text: str,
    model: str = DEFAULT_MODEL,
    progress: ProgressFn | None = None,
) -> dict:
    prompt = CV_EXTRACTION_PROMPT.replace("{cv}", cv_text)
    return _chat_json(client, model, prompt, progress=progress)


def evaluate(
    client: anthropic.Anthropic,
    jd_json: dict,
    cv_json: dict,
    cv_raw: str,
    model: str = DEFAULT_MODEL,
    progress: ProgressFn | None = None,
) -> dict:
    prompt = EVALUATION_PROMPT.format(
        jd_json=json.dumps(jd_json, ensure_ascii=False, indent=2),
        cv_json=json.dumps(cv_json, ensure_ascii=False, indent=2),
        cv_raw=cv_raw[:8000],
    )
    result = _chat_json(client, model, prompt, max_tokens=16000, progress=progress)
    return _normalize_evaluation(result)


def screen_candidate(
    jd_text: str,
    cv_text: str,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    progress: ProgressFn | None = None,
) -> ScreeningResult:
    def log(msg: str) -> None:
        if progress:
            progress(msg)

    log(f"🔌 Connecting to Claude ({model})...")
    client = _client(api_key)

    log("📋 Step 1/3 — Reading Job Description (extracting required skills, seniority, hidden expectations)")
    jd_json = extract_jd(client, jd_text, model=model, progress=progress)
    log(f"   ✓ JD parsed — role: {jd_json.get('role_title','?')} · seniority: {jd_json.get('seniority_level','?')}")

    log("📄 Step 2/3 — Reading CV (extracting profile, trajectory, bullets, red-flag signals)")
    cv_json = extract_cv(client, cv_text, model=model, progress=progress)
    log(
        f"   ✓ CV parsed — candidate: {cv_json.get('candidate_name','?')} · "
        f"trajectory: {cv_json.get('career_trajectory','?')[:60]}"
    )

    log("🧠 Step 3/3 — Senior panel evaluating (scoring, rewrites, hiring decision)")
    evaluation = evaluate(client, jd_json, cv_json, cv_text, model=model, progress=progress)
    log(
        f"   ✓ Evaluation done — score: {evaluation.get('overall_score','?')}/100 · "
        f"grade: {evaluation.get('grade','?')} · "
        f"decision: {evaluation.get('hiring_decision',{}).get('recommendation','?')}"
    )

    return ScreeningResult(
        jd_understanding=jd_json,
        cv_understanding=cv_json,
        evaluation=evaluation,
    )


def _normalize_evaluation(ev: dict) -> dict:
    """Enforce schema shape so the UI never crashes on missing keys."""
    ev.setdefault("overall_score", 0)
    ev.setdefault("grade", "Weak")
    ev.setdefault("confidence", 0.0)
    ev.setdefault("summary", "")
    ev.setdefault("strengths", [])
    ev.setdefault("weaknesses", [])
    dims = ev.setdefault("dimension_scores", {})
    for k in ("jd_match", "cv_quality", "experience_depth", "formatting", "risk"):
        dims.setdefault(k, 0)
    imp = ev.setdefault("improvements", {})
    imp.setdefault("content_issues", [])
    imp.setdefault(
        "skill_gaps",
        {"critical_missing": [], "secondary_missing": [], "transferable": []},
    )
    imp.setdefault("positioning_issues", [])
    imp.setdefault("experience_issues", [])
    imp.setdefault("formatting_issues", [])
    imp.setdefault("red_flags", [])
    sug = ev.setdefault("suggestions", {})
    sug.setdefault("micro_fixes", [])
    sug.setdefault("macro_fixes", [])
    sug.setdefault("strategic_advice", [])
    ev.setdefault(
        "hiring_decision",
        {"recommendation": "Consider", "reason": "", "top_risks": []},
    )
    return ev
