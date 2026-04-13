"""Streamlit UI for AI CV Screening — SaaS-grade redesign.

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

st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Design tokens + global styles ----------
st.markdown(
    """
    <style>
      /* ---------- Design tokens ---------- */
      :root {
        --bg: #f7f8fb;
        --surface: #ffffff;
        --border: #e5e7eb;
        --border-strong: #d1d5db;
        --muted: #6b7280;
        --text: #0f172a;
        --text-soft: #334155;
        --primary: #4f46e5;
        --primary-600: #4338ca;
        --primary-50: #eef2ff;
        --success: #059669;
        --success-50: #ecfdf5;
        --warning: #d97706;
        --warning-50: #fffbeb;
        --danger: #dc2626;
        --danger-50: #fef2f2;
        --radius-sm: 8px;
        --radius: 12px;
        --radius-lg: 16px;
        --shadow-xs: 0 1px 2px rgba(15,23,42,0.04);
        --shadow-sm: 0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
      }

      html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
        color: var(--text);
      }
      .stApp { background: var(--bg); }

      /* ---------- Container ---------- */
      .main .block-container {
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 1120px;
      }

      /* ---------- Header ---------- */
      .eyebrow {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--primary);
        background: var(--primary-50);
        padding: 5px 10px;
        border-radius: 999px;
        margin-bottom: 14px;
      }
      h1.brand {
        font-weight: 700;
        font-size: 2rem;
        letter-spacing: -0.02em;
        line-height: 1.15;
        color: var(--text);
        margin: 0 0 10px 0;
      }
      .sub {
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.55;
        max-width: 640px;
        margin-bottom: 2rem;
      }

      /* ---------- Panels ---------- */
      .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.25rem 1.35rem 1.35rem;
        box-shadow: var(--shadow-xs);
        height: 100%;
      }
      .panel-head {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 14px;
      }
      .panel-icon {
        width: 32px; height: 32px;
        border-radius: 9px;
        background: var(--primary-50);
        color: var(--primary);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.95rem;
      }
      .panel-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text);
        margin: 0;
      }
      .panel-hint {
        color: var(--muted);
        font-size: 0.78rem;
        margin: 0;
      }

      /* ---------- Inputs ---------- */
      .stTextArea textarea {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        background: #fcfcfd !important;
        font-size: 0.9rem !important;
        padding: 12px 14px !important;
        transition: border-color 120ms, box-shadow 120ms;
      }
      .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
      }
      [data-testid="stFileUploader"] section {
        border-radius: var(--radius) !important;
        border: 1.5px dashed var(--border-strong) !important;
        background: #fcfcfd !important;
        padding: 1.2rem !important;
      }
      [data-testid="stFileUploader"] section:hover {
        border-color: var(--primary) !important;
        background: var(--primary-50) !important;
      }

      /* ---------- Primary button ---------- */
      .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: 1px solid var(--primary-600) !important;
        border-radius: var(--radius) !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.7rem 1.4rem !important;
        letter-spacing: -0.005em !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 120ms !important;
      }
      .stButton > button:hover {
        background: var(--primary-600) !important;
        transform: translateY(-1px);
      }
      .stButton > button:active { transform: translateY(0); }

      /* ---------- Report section ---------- */
      .report-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 3rem 0 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border);
      }
      .report-head h2 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
      }
      .section-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
        margin: 2rem 0 0.75rem;
      }

      /* ---------- Score card ---------- */
      .score-card {
        background: linear-gradient(140deg, #4f46e5 0%, #6366f1 45%, #7c3aed 100%);
        color: white;
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.6rem;
        box-shadow: 0 10px 25px -12px rgba(79,70,229,0.4);
      }
      .score-card .lbl {
        opacity: 0.78;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 600;
      }
      .score-card .big {
        font-size: 3.4rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.03em;
        margin-top: 10px;
      }
      .score-card .big small {
        font-size: 1.1rem;
        opacity: 0.7;
        font-weight: 500;
        letter-spacing: 0;
      }
      .grade-chip {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        color: white;
        font-weight: 600;
        font-size: 0.78rem;
        letter-spacing: 0.01em;
      }
      .score-meta {
        margin-top: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
      }
      .score-meta .conf {
        opacity: 0.85;
        font-size: 0.82rem;
      }

      /* ---------- Decision card ---------- */
      .decision-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--primary);
        border-radius: var(--radius);
        padding: 1.15rem 1.3rem;
        height: 100%;
      }
      .decision-card .dec-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }
      .decision-card .dec-value {
        font-size: 1.15rem;
        font-weight: 700;
        margin: 4px 0 8px;
        letter-spacing: -0.01em;
      }
      .decision-card .dec-reason {
        color: var(--text-soft);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      /* ---------- List cards ---------- */
      .list-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.1rem 1.2rem;
        height: 100%;
      }
      .list-card h4 {
        margin: 0 0 0.7rem;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--muted);
      }
      .list-card ul { margin: 0; padding-left: 1.1rem; }
      .list-card li {
        font-size: 0.88rem;
        color: var(--text-soft);
        line-height: 1.55;
        margin-bottom: 6px;
      }

      /* ---------- Progress bars ---------- */
      .stProgress > div > div > div > div {
        background: var(--primary) !important;
        border-radius: 999px !important;
      }
      .stProgress > div > div > div {
        background: #eef0f4 !important;
        border-radius: 999px !important;
      }

      /* ---------- Expanders ---------- */
      .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        border-radius: var(--radius) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
      }
      [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        background: var(--surface) !important;
        margin-bottom: 10px !important;
      }

      /* ---------- Tabs ---------- */
      .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: var(--surface);
        padding: 6px;
        border-radius: var(--radius);
        border: 1px solid var(--border);
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        padding: 8px 14px !important;
      }
      .stTabs [aria-selected="true"] {
        background: var(--primary-50) !important;
        color: var(--primary) !important;
      }

      /* ---------- Dividers ---------- */
      hr { border-color: var(--border) !important; }

      /* Hide streamlit chrome */
      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown('<div class="eyebrow">AI · Recruiter Panel</div>', unsafe_allow_html=True)
st.markdown('<h1 class="brand">Resume Screening, powered by Claude</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Paste a job description, upload a CV, and get a recruiter-grade evaluation '
    "with scores, weak-bullet rewrites, skill-gap analysis, and a hire decision.</p>",
    unsafe_allow_html=True,
)

# ---------- Input grid ----------
col_jd, col_cv = st.columns(2, gap="large")

with col_jd:
    st.markdown(
        '<div class="panel"><div class="panel-head">'
        '<div class="panel-icon">📋</div>'
        '<div><p class="panel-title">Job Description</p>'
        '<p class="panel-hint">Paste the full JD — role, must-haves, nice-to-haves.</p></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    jd_text = st.text_area(
        "JD",
        height=320,
        key="jd_text",
        label_visibility="collapsed",
        placeholder="e.g. Senior Backend Engineer — 5+ yrs Python, distributed systems...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cv:
    st.markdown(
        '<div class="panel"><div class="panel-head">'
        '<div class="panel-icon">📄</div>'
        '<div><p class="panel-title">Candidate CV</p>'
        '<p class="panel-hint">PDF, DOCX, or TXT — use a text export, not a scan.</p></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "CV",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    st.write("")
    JOB_TITLES = [
        "AI Engineer",
        "Machine Learning Engineer",
        "Data Scientist",
        "Data Engineer",
        "Data Analyst",
        "MLOps Engineer",
        "LLM Engineer",
        "Computer Vision Engineer",
        "NLP Engineer",
        "Research Scientist",
        "Software Engineer",
        "Backend Engineer",
        "Frontend Engineer",
        "Full-Stack Engineer",
        "Mobile Engineer (iOS)",
        "Mobile Engineer (Android)",
        "DevOps Engineer",
        "Site Reliability Engineer (SRE)",
        "Cloud Engineer",
        "Platform Engineer",
        "Security Engineer",
        "QA / Test Engineer",
        "Embedded Engineer",
        "Game Developer",
        "Blockchain Engineer",
        "Solutions Architect",
        "Engineering Manager",
        "Product Manager",
        "Technical Product Manager",
        "UI/UX Designer",
        "Business Analyst",
    ]
    LEVELS = ["Intern", "Fresher", "Junior", "Mid", "Senior", "Lead", "Principal", "Manager"]

    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown(
            '<div style="font-size:0.78rem;font-weight:600;color:var(--muted);'
            'margin-bottom:4px">Job Title</div>',
            unsafe_allow_html=True,
        )
        job_title = st.selectbox(
            "Job Title",
            JOB_TITLES,
            index=0,
            label_visibility="collapsed",
            placeholder="Search a role...",
        )
    with dc2:
        st.markdown(
            '<div style="font-size:0.78rem;font-weight:600;color:var(--muted);'
            'margin-bottom:4px">Level</div>',
            unsafe_allow_html=True,
        )
        level = st.selectbox(
            "Level",
            LEVELS,
            index=3,
            label_visibility="collapsed",
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# Right-sized CTA (not stretched)
btn_l, btn_c, btn_r = st.columns([1, 1.2, 1])
with btn_c:
    analyze = st.button("🚀  Analyze Candidate", type="primary", use_container_width=True)


# ---------- Helpers ----------
def grade_color(grade: str) -> str:
    return {
        "Strong Hire": "#059669",
        "Good Fit": "#10b981",
        "Moderate": "#d97706",
        "Weak": "#dc2626",
    }.get(grade, "#6b7280")


def recommendation_color(rec: str) -> str:
    return {"Hire": "#059669", "Consider": "#d97706", "Reject": "#dc2626"}.get(rec, "#6b7280")


def render_score_bar(label: str, value: float, max_value: float) -> None:
    pct = 0 if max_value == 0 else min(1.0, value / max_value)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:500;color:var(--text-soft);margin-bottom:4px">{label}</div>',
            unsafe_allow_html=True,
        )
        st.progress(pct)
    with c2:
        st.markdown(
            f'<div style="text-align:right;font-size:0.92rem;font-weight:600;padding-top:2px">'
            f'{value:.0f}<span style="color:var(--muted);font-weight:400"> / {max_value:.0f}</span></div>',
            unsafe_allow_html=True,
        )


# ---------- Run analysis ----------
if not analyze:
    st.stop()

api_key = os.getenv("ANTHROPIC_API_KEY", "")
model = os.getenv("CV_SCORING_MODEL", DEFAULT_MODEL)

if not jd_text.strip():
    st.error("Please paste a Job Description.")
    st.stop()
if not uploaded:
    st.error("Please upload a CV.")
    st.stop()
if not api_key:
    st.error("ANTHROPIC_API_KEY is not set. Add it to your .env file and restart.")
    st.stop()

try:
    cv_text = parse_cv(uploaded)
except Exception as e:
    st.error(f"Failed to parse CV: {e}")
    st.stop()

if len(cv_text) < 80:
    st.warning("Parsed CV looks very short — scanned PDF? Try a text-based export.")

with st.status("🧠  Senior recruiter panel is reviewing...", expanded=True) as status:
    def log(msg: str) -> None:
        st.write(msg)

    log(f"📄 CV parsed locally — {len(cv_text):,} characters extracted")
    log(f"🎯 Target role: {level} {job_title}")
    jd_full = (
        f"TARGET ROLE: {job_title}\n"
        f"SENIORITY LEVEL: {level}\n\n"
        f"{jd_text}"
    )
    try:
        result = screen_candidate(
            jd_full, cv_text, api_key=api_key, model=model, progress=log
        )
    except Exception as e:
        status.update(label="❌  AI pipeline failed", state="error")
        st.error(f"AI pipeline error: {e}")
        st.stop()
    status.update(label="✅  Analysis complete", state="complete", expanded=False)

ev = result.evaluation

# ---------- Report header ----------
st.markdown(
    '<div class="report-head"><h2>Evaluation Report</h2>'
    '<span style="font-size:0.8rem;color:var(--muted)">Claude · senior recruiter panel</span></div>',
    unsafe_allow_html=True,
)

# ---------- Section: Overall Score + Decision ----------
top_l, top_r = st.columns([1, 1.35], gap="large")
with top_l:
    grade = ev.get("grade", "Weak")
    score = ev.get("overall_score", 0)
    conf = float(ev.get("confidence", 0)) * 100
    st.markdown(
        f"""
        <div class="score-card">
          <div class="lbl">Overall Score</div>
          <div class="big">{score}<small> / 100</small></div>
          <div class="score-meta">
            <span class="grade-chip" style="background:{grade_color(grade)}">{grade}</span>
            <span class="conf">Confidence · {conf:.0f}%</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_r:
    rec = ev.get("hiring_decision", {}).get("recommendation", "Consider")
    reason = ev.get("hiring_decision", {}).get("reason", "")
    st.markdown(
        f"""
        <div class="decision-card" style="border-left-color:{recommendation_color(rec)}">
          <div class="dec-label">Hiring Decision</div>
          <div class="dec-value" style="color:{recommendation_color(rec)}">{rec}</div>
          <div class="dec-reason">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(
    '<div style="background:var(--surface);border:1px solid var(--border);'
    'border-radius:var(--radius);padding:1.1rem 1.3rem">'
    '<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;'
    'text-transform:uppercase;color:var(--muted);margin-bottom:6px">Hiring Manager Summary</div>'
    f'<div style="color:var(--text-soft);font-size:0.92rem;line-height:1.6">{ev.get("summary","")}</div>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------- Strengths / Weaknesses ----------
st.markdown('<div class="section-label">Strengths & Weaknesses</div>', unsafe_allow_html=True)
cA, cB = st.columns(2, gap="medium")
with cA:
    items = "".join(f"<li>{s}</li>" for s in ev.get("strengths", []))
    st.markdown(
        f'<div class="list-card" style="border-left:3px solid var(--success)">'
        f'<h4>✅ Strengths</h4><ul>{items or "<li>—</li>"}</ul></div>',
        unsafe_allow_html=True,
    )
with cB:
    items = "".join(f"<li>{w}</li>" for w in ev.get("weaknesses", []))
    st.markdown(
        f'<div class="list-card" style="border-left:3px solid var(--warning)">'
        f'<h4>⚠️ Weaknesses</h4><ul>{items or "<li>—</li>"}</ul></div>',
        unsafe_allow_html=True,
    )

# ---------- Breakdown ----------
st.markdown('<div class="section-label">Score Breakdown</div>', unsafe_allow_html=True)
dims = ev.get("dimension_scores", {})
max_map = {"jd_match": 40, "cv_quality": 25, "experience_depth": 10, "formatting": 15, "risk": 10}
labels = {
    "jd_match": "JD Match",
    "cv_quality": "CV Quality",
    "experience_depth": "Experience Depth",
    "formatting": "Formatting / ATS",
    "risk": "Risk (higher = safer)",
}
st.markdown(
    '<div style="background:var(--surface);border:1px solid var(--border);'
    'border-radius:var(--radius);padding:1.3rem 1.4rem">',
    unsafe_allow_html=True,
)
for key, mx in max_map.items():
    render_score_bar(labels[key], float(dims.get(key, 0)), mx)
    st.write("")
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Issues & Improvements ----------
st.markdown('<div class="section-label">Issues & Improvements</div>', unsafe_allow_html=True)
imp = ev.get("improvements", {})

with st.expander("📝  Content Issues — weak bullets & rewrites", expanded=True):
    issues = imp.get("content_issues", [])
    if not issues:
        st.success("No major content issues detected.")
    for i, issue in enumerate(issues, 1):
        st.markdown(f"**Issue {i} — `{issue.get('issue_type','')}`**")
        st.markdown(f"🔻 *Original:* {issue.get('original','')}")
        st.markdown(f"❓ *Problem:* {issue.get('problem','')}")
        st.markdown(f"✨ *Improved:* **{issue.get('improved_version','')}**")
        st.divider()

with st.expander("🎯  Skill Gaps"):
    gaps = imp.get("skill_gaps", {})
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("**🔴 Critical Missing**")
        for s in gaps.get("critical_missing", []):
            st.markdown(f"- {s}")
    with g2:
        st.markdown("**🟡 Secondary Missing**")
        for s in gaps.get("secondary_missing", []):
            st.markdown(f"- {s}")
    with g3:
        st.markdown("**🟢 Transferable**")
        for s in gaps.get("transferable", []):
            st.markdown(f"- {s}")

with st.expander("📐  Positioning"):
    for p in imp.get("positioning_issues", []):
        st.markdown(f"**Problem:** {p.get('problem','')}")
        st.markdown(f"**Rewritten Summary:**\n\n> {p.get('rewritten_summary','')}")
        st.divider()

with st.expander("📈  Experience Issues"):
    for x in imp.get("experience_issues", []):
        st.markdown(f"- {x}")

with st.expander("🧾  Formatting / ATS Issues"):
    for x in imp.get("formatting_issues", []):
        st.markdown(f"- {x}")

with st.expander("🚩  Red Flags"):
    flags = imp.get("red_flags", [])
    if not flags:
        st.success("No red flags detected.")
    for f in flags:
        st.markdown(f"- **{f.get('flag','')}** — {f.get('risk_explanation','')}")

# ---------- Suggestions ----------
st.markdown('<div class="section-label">Suggestions</div>', unsafe_allow_html=True)
sug = ev.get("suggestions", {})
tab1, tab2, tab3 = st.tabs(["🔧  Micro Fixes", "🏗️  Macro Fixes", "🧭  Strategic"])
with tab1:
    for s in sug.get("micro_fixes", []):
        st.markdown(f"- {s}")
with tab2:
    for s in sug.get("macro_fixes", []):
        st.markdown(f"- {s}")
with tab3:
    for s in sug.get("strategic_advice", []):
        st.markdown(f"- {s}")

# ---------- Raw + download ----------
st.write("")
with st.expander("🔍  Raw JSON (JD + CV understanding + Evaluation)"):
    st.json(
        {
            "jd_understanding": result.jd_understanding,
            "cv_understanding": result.cv_understanding,
            "evaluation": ev,
        }
    )

st.download_button(
    "⬇️  Download full report (JSON)",
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
