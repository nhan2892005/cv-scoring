"""Streamlit UI — CV Evaluation · Enterprise redesign.

Run:  streamlit run app.py
"""
from __future__ import annotations

import json
import os

import streamlit as st
from dotenv import load_dotenv

from ai_engine import DEFAULT_MODEL, screen_candidate
from cv_parser import parse_cv

load_dotenv()

st.set_page_config(page_title="CV Evaluation", layout="wide")


def load_css(file_name: str) -> None:
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
      <div class="wordmark"><span class="dot"></span>CV Evaluation</div>
      <div class="tagline">Automated screening and gap analysis for technical roles.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Inputs ───────────────────────────────────────────────────────────────────
col_jd, col_cv = st.columns(2, gap="large")

with col_jd:
    st.markdown('<div class="panel"><div class="panel-title">Job Description</div>', unsafe_allow_html=True)
    jd_text = st.text_area(
        "jd",
        height=320,
        key="jd_text",
        label_visibility="collapsed",
        placeholder="Paste the full job description here…",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cv:
    st.markdown('<div class="panel"><div class="panel-title">Candidate CV</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "cv",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )
    st.caption("PDF, DOCX, or TXT. Use a text-based export, not a scanned image.")
    st.markdown("</div>", unsafe_allow_html=True)

_, center_btn, _ = st.columns([1, 2, 1])
with center_btn:
    analyze = st.button("Run Evaluation", type="primary", use_container_width=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def grade_color(grade: str) -> str:
    return {
        "Strong Hire": "#0d7a4e",
        "Good Fit":    "#1b7a3e",
        "Moderate":    "#b45309",
        "Weak":        "#c0392b",
    }.get(grade, "#6b7a99")


def rec_color(rec: str) -> str:
    return {"Hire": "#0d7a4e", "Consider": "#b45309", "Reject": "#c0392b"}.get(rec, "#6b7a99")


def score_bar(label: str, value: float, max_value: float) -> None:
    pct = 0.0 if max_value == 0 else min(1.0, value / max_value)
    st.markdown(
        f"""
        <div class="metric-row">
          <div class="metric-label">{label}</div>
          <div class="metric-score">{value:.0f} / {max_value:.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(pct)


# ── Guard ────────────────────────────────────────────────────────────────────
if not analyze:
    st.stop()

model = os.getenv("CV_SCORING_MODEL", DEFAULT_MODEL)
is_groq = any(k in model.lower() for k in ("llama", "mixtral", "gemma"))
api_key = os.getenv("GROQ_API_KEY" if is_groq else "ANTHROPIC_API_KEY", "")
key_name = "GROQ_API_KEY" if is_groq else "ANTHROPIC_API_KEY"

if not jd_text.strip():
    st.error("Please paste a Job Description.")
    st.stop()
if not uploaded:
    st.error("Please upload a CV.")
    st.stop()
if not api_key:
    st.error(f"{key_name} is not set. Add it to your .env file and restart.")
    st.stop()

try:
    cv_text = parse_cv(uploaded)
except Exception as e:
    st.error(f"Could not parse CV: {e}")
    st.stop()

if len(cv_text) < 80:
    st.warning("Parsed CV looks very short — scanned PDF? Try a text-based export.")

with st.status("Reviewing candidate…", expanded=True) as status:
    def log(msg: str) -> None:
        st.write(msg)

    log(f"CV parsed — {len(cv_text):,} characters")
    try:
        result = screen_candidate(jd_text, cv_text, api_key=api_key, model=model, progress=log)
    except Exception as e:
        status.update(label="Analysis failed", state="error")
        st.error(f"Pipeline error: {e}")
        st.stop()
    status.update(label="Analysis complete", state="complete", expanded=False)

ev  = result.evaluation
imp = ev.get("improvements", {})
sug = ev.get("suggestions", {})
dim = ev.get("dimension_scores", {})

# ═══════════════════════════════════════════════════════════════════════════
# Section 1 — Score + Decision
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-label">Evaluation Summary</p>', unsafe_allow_html=True)

col_score, col_decision = st.columns([1, 2], gap="large")

with col_score:
    grade = ev.get("grade", "Weak")
    score = ev.get("overall_score", 0)
    conf  = float(ev.get("confidence", 0)) * 100
    st.markdown(
        f"""
        <div class="score-card">
          <div class="lbl">Overall Score</div>
          <div class="big">{score}<sub> /100</sub></div>
          <div>
            <span class="grade-chip" style="background:{grade_color(grade)}">{grade}</span>
          </div>
          <div style="margin-top:14px;font-size:0.75rem;color:var(--text-faint)">
            Confidence: {conf:.0f}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_decision:
    rec    = ev.get("hiring_decision", {}).get("recommendation", "Consider")
    reason = ev.get("hiring_decision", {}).get("reason", "")
    summary = ev.get("summary", "")
    color  = rec_color(rec)
    st.markdown(
        f"""
        <div class="decision-box" style="border-left-color:{color}">
          <div class="decision-label">Hiring Recommendation</div>
          <div class="decision-value" style="color:{color}">{rec}</div>
          <div class="decision-reason">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p class="section-label">Panel Summary</p>', unsafe_allow_html=True)
st.markdown(
    f'<p style="font-size:0.9rem;line-height:1.7;color:var(--text-body)">{summary}</p>',
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# Section 2 — Strengths / Weaknesses
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-label">Strengths & Weaknesses</p>', unsafe_allow_html=True)

cA, cB = st.columns(2, gap="large")
with cA:
    st.markdown('<div class="panel-title">Strengths</div>', unsafe_allow_html=True)
    for s in ev.get("strengths", []):
        st.markdown(
            f'<div class="suggestion-item">{s}</div>',
            unsafe_allow_html=True,
        )

with cB:
    st.markdown('<div class="panel-title">Weaknesses</div>', unsafe_allow_html=True)
    for w in ev.get("weaknesses", []):
        st.markdown(
            f'<div class="suggestion-item">{w}</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════════════
# Section 3 — Score Breakdown
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-label">Score Breakdown</p>', unsafe_allow_html=True)

max_map = {
    "jd_match":          ("JD Match",               40),
    "cv_quality":        ("CV Quality",              25),
    "experience_depth":  ("Experience Depth",        10),
    "formatting":        ("Formatting / ATS",        15),
    "risk":              ("Risk Indicator",           10),
}
for key, (label, mx) in max_map.items():
    score_bar(label, float(dim.get(key, 0)), mx)

# ═══════════════════════════════════════════════════════════════════════════
# Section 4 — Issues & Improvements
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-label">Issues & Improvements</p>', unsafe_allow_html=True)

with st.expander("Content Issues — bullet rewrites", expanded=True):
    issues = imp.get("content_issues", [])
    if not issues:
        st.success("No major content issues detected.")
    for issue in issues:
        st.markdown(
            f"""
            <div class="issue-card">
              <div class="issue-type">{issue.get('issue_type','')}</div>
              <div class="issue-original">{issue.get('original','')}</div>
              <div class="issue-problem">{issue.get('problem','')}</div>
              <div class="issue-improved">{issue.get('improved_version','')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with st.expander("Skill Gaps"):
    gaps = imp.get("skill_gaps", {})
    g1, g2, g3 = st.columns(3, gap="large")
    with g1:
        st.markdown('<div class="panel-title">Critical Missing</div>', unsafe_allow_html=True)
        for s in gaps.get("critical_missing", []):
            st.markdown(f'<span class="gap-badge gap-critical">{s}</span>', unsafe_allow_html=True)
    with g2:
        st.markdown('<div class="panel-title">Secondary Missing</div>', unsafe_allow_html=True)
        for s in gaps.get("secondary_missing", []):
            st.markdown(f'<span class="gap-badge gap-secondary">{s}</span>', unsafe_allow_html=True)
    with g3:
        st.markdown('<div class="panel-title">Transferable</div>', unsafe_allow_html=True)
        for s in gaps.get("transferable", []):
            st.markdown(f'<span class="gap-badge gap-transfer">{s}</span>', unsafe_allow_html=True)

with st.expander("Positioning"):
    for p in imp.get("positioning_issues", []):
        st.markdown(f"**Problem:** {p.get('problem','')}")
        st.markdown(f"> {p.get('rewritten_summary','')}")
        st.divider()

with st.expander("Experience Issues"):
    for x in imp.get("experience_issues", []):
        st.markdown(f'<div class="suggestion-item">{x}</div>', unsafe_allow_html=True)

with st.expander("Formatting / ATS"):
    for x in imp.get("formatting_issues", []):
        st.markdown(f'<div class="suggestion-item">{x}</div>', unsafe_allow_html=True)

with st.expander("Red Flags"):
    flags = imp.get("red_flags", [])
    if not flags:
        st.success("No red flags detected.")
    for f in flags:
        st.markdown(
            f"""
            <div class="flag-row">
              <div class="flag-name">{f.get('flag','')}</div>
              <div>{f.get('risk_explanation','')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════════════
# Section 5 — Suggestions
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown('<p class="section-label">Suggestions</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Micro Fixes", "Macro Fixes", "Strategic Advice"])

with tab1:
    for s in sug.get("micro_fixes", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

with tab2:
    for s in sug.get("macro_fixes", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

with tab3:
    for s in sug.get("strategic_advice", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Raw JSON + Download
# ═══════════════════════════════════════════════════════════════════════════
st.divider()

full_report = {
    "jd_understanding": result.jd_understanding,
    "cv_understanding": result.cv_understanding,
    "evaluation":       ev,
}

with st.expander("Raw JSON"):
    st.json(full_report)

st.download_button(
    "Download full report (JSON)",
    data=json.dumps(full_report, indent=2, ensure_ascii=False),
    file_name="cv_evaluation_report.json",
    mime="application/json",
    use_container_width=True,
)