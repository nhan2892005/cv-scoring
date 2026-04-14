"""Streamlit UI for AI CV Screening — resumescreening.ai-inspired layout.

Run:  streamlit run app.py
"""
from __future__ import annotations

import json
import os

import streamlit as st
from dotenv import load_dotenv
from streamlit_searchbox import st_searchbox

from ai_engine import DEFAULT_MODEL, screen_candidate
from cv_parser import parse_cv

load_dotenv()

st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="🎯",
    layout="wide",
)

# ---------- Global styles ----------
st.markdown(
    """
    <style>
      .main .block-container {padding-top: 2rem; max-width: 1200px;}
      h1.brand {font-weight: 800; font-size: 2.2rem; margin-bottom: 0.2rem;}
      .brand-accent {color: #2563eb;}
      .sub {color: #64748b; font-size: 0.95rem; margin-bottom: 1.6rem;}
      .panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
      }
      .panel h3 {margin-top: 0; margin-bottom: 0.6rem; font-size: 1rem; color:#0f172a;}
      .score-card {
        background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
        color: white; border-radius: 14px; padding: 1.4rem;
      }
      .score-card .big {font-size: 3rem; font-weight: 800; line-height: 1;}
      .score-card .lbl {opacity: 0.85; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;}
      .grade-chip {
        display:inline-block; padding:6px 14px; border-radius:999px;
        color:white; font-weight:700; font-size:0.85rem;
      }
      .decision-box {
        padding: 14px 16px; border-radius: 10px;
        background: #f8fafc; border-left: 6px solid #2563eb; margin-top: 12px;
      }
      .stButton>button[kind="primary"] {
        background: linear-gradient(135deg,#2563eb,#7c3aed);
        border: none; font-weight: 700; padding: 0.75rem 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    '<h1 class="brand">🎯 AI <span class="brand-accent">Resume Screening</span></h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub">1. Paste the job description on the left. '
    "2. Upload a CV on the right. "
    "3. Click <b>Analyze</b> for a full recruiter-grade breakdown.</div>",
    unsafe_allow_html=True,
)

# ---------- Input: two-column layout ----------
col_jd, col_cv = st.columns(2, gap="large")

with col_jd:
    st.markdown('<div class="panel"><h3>📋 Job Description</h3>', unsafe_allow_html=True)
    jd_text = st.text_area(
        "Paste the full JD here",
        height=340,
        key="jd_text",
        label_visibility="collapsed",
        placeholder="Paste the full job description here...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cv:
    st.markdown('<div class="panel"><h3>📄 Upload CV</h3>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "PDF / DOCX / TXT",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )
    st.caption("Accepts PDF, DOCX, or TXT. Use a text-based export (not a scanned image).")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
analyze = st.button(
    "🚀 Analyze CV",
    type="primary",
    use_container_width=True,
)

# ---------- Helpers ----------
def grade_color(grade: str) -> str:
    return {
        "Strong Hire": "#16a34a",
        "Good Fit": "#22c55e",
        "Moderate": "#f59e0b",
        "Weak": "#ef4444",
    }.get(grade, "#64748b")


def recommendation_color(rec: str) -> str:
    return {"Hire": "#16a34a", "Consider": "#f59e0b", "Reject": "#ef4444"}.get(rec, "#64748b")


def render_score_bar(label: str, value: float, max_value: float) -> None:
    pct = 0 if max_value == 0 else min(1.0, value / max_value)
    st.markdown(f"**{label}** — {value:.0f} / {max_value:.0f}")
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
    st.warning("Parsed CV looks very short. Consider using a raw text export.")

with st.status("🧠 Senior recruiter panel is reviewing...", expanded=True) as status:
    def log(msg: str) -> None:
        st.write(msg)

    log(f"📄 CV parsed locally — {len(cv_text):,} characters extracted")
    try:
        result = screen_candidate(
            jd_text, cv_text, api_key=api_key, model=model, progress=log
        )
    except Exception as e:
        status.update(label="❌ AI pipeline failed", state="error")
        st.error(f"AI pipeline error: {e}")
        st.stop()
    status.update(label="✅ Analysis complete", state="complete", expanded=False)

ev  = result.evaluation
imp = ev.get("improvements", {})
sug = ev.get("suggestions", {})
dim = ev.get("dimension_scores", {})

# ---------- Section 1: Overall Score ----------
st.divider()
st.subheader("📊 Evaluation Report")

top_l, top_r = st.columns([1, 2], gap="large")
with top_l:
    grade = ev.get("grade", "Weak")
    score = ev.get("overall_score", 0)
    conf  = float(ev.get("confidence", 0)) * 100
    st.markdown(
        f"""
        <div class="score-card">
          <div class="lbl">Overall Score</div>
          <div class="big">{score}<span style="font-size:1.2rem;opacity:0.8">/100</span></div>
          <div style="margin-top:10px">
            <span class="grade-chip" style="background:{grade_color(grade)}">{grade}</span>
            <span style="margin-left:10px;opacity:0.9">Confidence: {conf:.0f}%</span>
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
        <div class="decision-box" style="border-left-color:{recommendation_color(rec)}">
          <b style="color:{recommendation_color(rec)};font-size:1.05rem">Decision: {rec}</b>
          <div style="margin-top:6px;color:#334155">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Hiring manager summary**")
    st.write(ev.get("summary", ""))

# ---------- Section 2: Strengths / Weaknesses ----------
st.markdown("### ✅ Strengths & ⚠️ Weaknesses")
cA, cB = st.columns(2)
with cA:
    st.markdown("**Strengths**")
    for s in ev.get("strengths", []):
        st.markdown(f"- {s}")
with cB:
    st.markdown("**Weaknesses**")
    for w in ev.get("weaknesses", []):
        st.markdown(f"- {w}")

# ---------- Section 3: Breakdown ----------
st.markdown("### 📈 Score Breakdown")
dims = ev.get("dimension_scores", {})
max_map = {
    "jd_match": 40,
    "cv_quality": 25,
    "experience_depth": 10,
    "formatting": 15,
    "risk": 10,
}
labels = {
    "jd_match": "JD Match",
    "cv_quality": "CV Quality",
    "experience_depth": "Experience Depth",
    "formatting": "Formatting / ATS",
    "risk": "Risk (higher = safer)",
}
for key, mx in max_map.items():
    render_score_bar(labels[key], float(dims.get(key, 0)), mx)

# ---------- Section 4: Issues & Improvements ----------
st.markdown("### 🛠️ Issues & Improvements")
imp = ev.get("improvements", {})

with st.expander("📝 Content Issues — weak bullets & rewrites", expanded=True):
    issues = imp.get("content_issues", [])
    if not issues:
        st.success("No major content issues detected.")
    for i, issue in enumerate(issues, 1):
        st.markdown(f"**Issue {i} — `{issue.get('issue_type','')}`**")
        st.markdown(f"🔻 *Original:* {issue.get('original','')}")
        st.markdown(f"❓ *Problem:* {issue.get('problem','')}")
        st.markdown(f"✨ *Improved:* **{issue.get('improved_version','')}**")
        st.divider()

with st.expander("🎯 Skill Gaps"):
    gaps = imp.get("skill_gaps", {})
    g1, g2, g3 = st.columns(3, gap="large")
    with g1:
        st.markdown("**🔴 Critical Missing**")
        for s in gaps.get("critical_missing", []):
            st.markdown(f'<span class="gap-badge gap-critical">{s}</span>', unsafe_allow_html=True)
    with g2:
        st.markdown("**🟡 Secondary Missing**")
        for s in gaps.get("secondary_missing", []):
            st.markdown(f'<span class="gap-badge gap-secondary">{s}</span>', unsafe_allow_html=True)
    with g3:
        st.markdown("**🟢 Transferable**")
        for s in gaps.get("transferable", []):
            st.markdown(f'<span class="gap-badge gap-transfer">{s}</span>', unsafe_allow_html=True)

with st.expander("📐 Positioning"):
    for p in imp.get("positioning_issues", []):
        st.markdown(f"**Problem:** {p.get('problem','')}")
        st.markdown(f"**Rewritten Summary:**\n\n> {p.get('rewritten_summary','')}")
        st.divider()

with st.expander("📈 Experience Issues"):
    for x in imp.get("experience_issues", []):
        st.markdown(f'<div class="suggestion-item">{x}</div>', unsafe_allow_html=True)

with st.expander("🧾 Formatting / ATS Issues"):
    for x in imp.get("formatting_issues", []):
        st.markdown(f'<div class="suggestion-item">{x}</div>', unsafe_allow_html=True)

with st.expander("🚩 Red Flags"):
    flags = imp.get("red_flags", [])
    if not flags:
        st.markdown("*No primary risk indicators detected.*")
    for f in flags:
        st.markdown(f"- **{f.get('flag','')}** — {f.get('risk_explanation','')}")

# ---------- Section 5: Suggestions ----------
st.markdown("### 💡 Suggestions")
sug = ev.get("suggestions", {})
tab1, tab2, tab3 = st.tabs(["🔧 Micro Fixes", "🏗️ Macro Fixes", "🧭 Strategic Advice"])
with tab1:
    for s in sug.get("micro_fixes", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

with tab2:
    for s in sug.get("macro_fixes", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

with tab3:
    for s in sug.get("strategic_advice", []):
        st.markdown(f'<div class="suggestion-item">{s}</div>', unsafe_allow_html=True)

# ---------- Raw + download ----------
with st.expander("🔍 Raw JSON (JD + CV understanding + Evaluation)"):
    st.json(
        {
            "jd_understanding": result.jd_understanding,
            "cv_understanding": result.cv_understanding,
            "evaluation": ev,
        }
    )

st.download_button(
    "⬇️ Download full report (JSON)",
    data=json.dumps(
        {
            "jd_understanding": result.jd_understanding,
            "cv_understanding": result.cv_understanding,
            "evaluation": ev,
        },
        indent=2,
        ensure_ascii=False,
    ),
    file_name="cv_screening_report.json",
    mime="application/json",
    use_container_width=True,
)