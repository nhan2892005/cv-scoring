"""Streamlit UI for AI CV Screening — SaaS-grade redesign.

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
    page_title="CV Scoring",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Design tokens + global styles ----------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');

      :root {
        --bg-main: #F8FAFC;
        --sidebar-bg: #FFFFFF;
        --accent-primary: #6366F1; /* Modern Indigo */
        --accent-indigo: #0F172A;
        --text-main: #1E293B;
        --text-muted: #64748B;
        --border-color: #E2E8F0;
        --input-bg: #FFFFFF;
        --glass-bg: rgba(255, 255, 255, 0.9);
      }

      /* Global Base Styles */
      html, body, .stApp, .stMarkdown, p, div, span, label {
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
      }

      .stApp {
        background: var(--bg-main);
      }

      /* ---------- Custom Header ---------- */
      .custom-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 70px;
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
        z-index: 1000;
      }
      .logo-text {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 22px;
        letter-spacing: -0.02em;
        color: var(--accent-indigo) !important;
      }
      .nav-links {
        display: flex;
        align-items: center;
        gap: 24px;
      }
      .nav-link {
        color: var(--text-main) !important;
        font-weight: 500;
        font-size: 14px;
        text-decoration: none;
      }
      .nav-link:hover { color: var(--accent-primary) !important; }
      
      .btn-signup {
        background: var(--accent-indigo);
        color: white !important;
        padding: 8px 20px;
        border-radius: 40px;
        font-weight: 600;
        text-decoration: none;
        font-size: 14px;
      }

      /* ---------- Sidebar Styling ---------- */
      [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
      }
      .new-job-btn {
        background: var(--accent-indigo);
        color: white !important;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 20px;
        cursor: pointer;
      }

      /* ---------- Main Content Layout ---------- */
      .main .block-container {
        padding-top: 100px !important;
        max-width: 1000px;
      }

      /* ---------- Cards/Panels ---------- */
      .panel-v2 {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.05);
        height: 100%;
      }
      .panel-title-v2 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 14px;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 20px;
      }

      /* ---------- INPUTS: THE BEAUTY FIX ---------- */
      /* Textareas and Inputs */
      .stTextArea textarea, .stTextInput input {
        border-radius: 12px !important;
        border: 1.2px solid var(--border-color) !important;
        background-color: white !important;
        color: var(--text-main) !important;
        padding: 16px !important;
        font-size: 15px !important;
        box-shadow: none !important;
      }
      
      /* Input backgrounds fix for searchbox wrappers */
      div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: white !important;
        border-radius: 12px !important;
      }
      
      /* Selectboxes and Dropdowns (BaseWeb Fix) */
      [data-baseweb="select"], [data-baseweb="select"] > div {
        background-color: white !important;
        border-radius: 12px !important;
        color: var(--text-main) !important;
      }
      [data-baseweb="select"] > div {
        border: 1.2px solid var(--border-color) !important;
        min-height: 48px !important;
      }
      
      /* Ensure text in selectbox is visible */
      [data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: var(--text-main) !important;
      }

      /* Dropdown Menus and Popovers (The lists that pop up) */
      [data-baseweb="popover"], [data-baseweb="popover"] > div, ul[role="listbox"], [data-baseweb="menu"] {
        background-color: white !important;
      }
      
      ul[role="listbox"], [data-baseweb="menu"] {
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        background-color: white !important;
      }
      
      ul[role="listbox"] li, [data-baseweb="menu"] li, [role="option"] {
        color: var(--text-main) !important;
        background-color: white !important; /* Fixed hover issue */
        padding: 10px 15px !important;
        font-size: 14px !important;
      }
      ul[role="listbox"] li:hover, [role="option"]:hover, [aria-selected="true"] {
        background-color: #F1F5F9 !important;
        color: var(--accent-primary) !important;
      }

      /* Focus states */
      .stTextArea textarea:focus, .stTextInput input:focus, div[data-baseweb="select"]:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
      }

      /* Placeholder override */
      ::placeholder { color: #94A3B8 !important; }

      /* File Uploader */
      [data-testid="stFileUploader"] section {
        border-radius: 16px !important;
        border: 2px dashed #CBD5E1 !important;
        background-color: white !important; /* Fixed upload background */
        padding: 30px !important;
      }
      [data-testid="stFileUploader"] section:hover { border-color: var(--accent-primary) !important; }
      [data-testid="stFileUploader"] button {
        background-color: white !important; /* Fixed button inside upload */
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
      }

      /* ---------- Informational Sections ---------- */
      .how-it-works {
        margin-top: 80px;
        padding: 60px 40px;
        background: white;
        border-radius: 32px;
        border: 1px solid var(--border-color);
        text-align: center;
      }
      .how-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 32px;
        margin-bottom: 24px;
        color: var(--accent-indigo) !important;
      }

      /* Score Boxes */
      .score-box {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
      }

      /* Primary Button */
      .stButton > button {
        border-radius: 12px !important; /* Matched to inputs for better rhythm */
        background: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        height: 54px !important;
        font-size: 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
      }
      .stButton > button:hover {
        background: #1F2937 !important; /* Slightly lighter on hover */
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2) !important;
      }
      .stButton > button:active {
        transform: translateY(0);
      }
      /* Force white text on search/submit button children */
      .stButton > button div, .stButton > button p, .stButton > button span {
        color: white !important;
      }
      
      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Custom UI Components (HTML) ----------
st.markdown(
    """
    <div class="custom-header">
      <div class="logo-container">
        <div class="logo-text">CV Scoring</div>
      </div>
      <div class="nav-links">
        <a href="#" class="nav-link">Sign in</a>
        <a href="#" class="btn-signup">Sign up for free</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="new-job-btn"><span>+</span> New job</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-empty-state">No jobs yet<br/>Create one to get started</div>', unsafe_allow_html=True)

# ---------- Main Content ----------
col_jd, col_cv = st.columns([1, 1], gap="large")

with col_jd:
    st.markdown(
        """
        <div class="panel-v2">
          <div class="panel-header-v2">
            <div class="panel-title-v2">First, enter job requirements here ↓</div>
            <div class="shortcut-hint">⌘S Save</div>
          </div>
        """,
        unsafe_allow_html=True,
    )
    jd_text = st.text_area(
        "JD",
        height=420,
        key="jd_text",
        label_visibility="collapsed",
        placeholder="Paste the Job Description here. For best results, include:\n\nREQUIRED SKILLS:\n- Python, React, SQL, etc.\n\nEXPERIENCE:\n- 3+ years in software engineering\n\nQUALIFICATIONS:\n- Bachelor's in CS or equivalent",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cv:
    st.markdown(
        """
        <div class="panel-v2">
          <div class="panel-header-v2">
            <div class="panel-title-v2">Candidate Details</div>
          </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "CV",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    st.write("")
    JOB_TITLES = [
        "AI Engineer", "Machine Learning Engineer", "Data Scientist", "Data Engineer",
        "Data Analyst", "MLOps Engineer", "LLM Engineer", "Computer Vision Engineer",
        "NLP Engineer", "Research Scientist", "Software Engineer", "Backend Engineer",
        "Frontend Engineer", "Full-Stack Engineer", "Mobile Engineer (iOS)",
        "Mobile Engineer (Android)", "DevOps Engineer", "Site Reliability Engineer (SRE)",
        "Cloud Engineer", "Platform Engineer", "Security Engineer", "QA / Test Engineer",
        "Embedded Engineer", "Game Developer", "Blockchain Engineer", "Solutions Architect",
        "Engineering Manager", "Product Manager", "Technical Product Manager",
        "UI/UX Designer", "Business Analyst",
    ]
    LEVELS = ["Intern", "Fresher", "Junior", "Mid", "Senior", "Lead", "Principal", "Manager"]

    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown('<div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.02em;">Target Position</div>', unsafe_allow_html=True)
        job_title = st.selectbox(
            "Target Position",
            JOB_TITLES,
            index=0,
            label_visibility="collapsed",
        )
    with dc2:
        st.markdown('<div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:4px;text-transform:uppercase;">Level</div>', unsafe_allow_html=True)
        level = st.selectbox("Level", LEVELS, index=3, label_visibility="collapsed")
    
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# CTA
analyze = st.button("Generate Evaluation Report", type="primary", use_container_width=True)


# ---------- Helpers ----------
def get_grade_label(grade: str) -> str:
    return f"[{grade.upper()}]"


def get_recommendation_label(rec: str) -> str:
    return f"[{rec.upper()}]"


def render_score_bar(label: str, value: float, max_value: float) -> None:
    pct = 0 if max_value == 0 else min(1.0, value / max_value)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(
            f'<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px">{label}</div>',
            unsafe_allow_html=True,
        )
        st.progress(pct)
    with c2:
        st.markdown(
            f'<div style="text-align:right;font-size:14px;font-weight:700;padding-top:2px;color:var(--text-main)">'
            f'{value:.0f}<span style="color:var(--text-muted);font-weight:400"> / {max_value:.0f}</span></div>',
            unsafe_allow_html=True,
        )


# ---------- How it works (Informational) ----------
st.markdown(
    """
    <div class="how-it-works">
      <div class="how-title">How does it work?</div>
      <div class="how-steps">
        1. Enter your job description on the left.<br/>
        2. Upload several resumes on the right.<br/>
        3. Get a sorted list of applicants in seconds.
      </div>
    </div>
    """,
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
    st.warning("Parsed CV looks very short. Consider using a raw text export.")

with st.status("PROCESSING EVALUATION...", expanded=True) as status:
    def log(msg: str) -> None:
        st.write(msg)

    log(f"DOCUMENT READ: {len(cv_text):,} characters extracted")
    log(f"TARGET DEFINED: {level} {job_title}")
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
        status.update(label="[FAIL] Processing Error", state="error")
        st.error(f"System error: {e}")
        st.stop()
    status.update(label="[COMPLETE] Evaluation Generated",
                  state="complete", expanded=False)

ev = result.evaluation

# ---------- Report header ----------
st.markdown(
    '<div style="margin-top: 4rem; padding-bottom: 1rem; border-bottom: 2px solid var(--accent-indigo);">'
    '<h2 style="font-family: \'Outfit\', sans-serif; font-weight: 700; margin: 0;">Evaluation Results</h2></div>',
    unsafe_allow_html=True,
)

# ---------- Section: Overall Score + Decision ----------
top_l, top_r = st.columns([1, 1], gap="large")
with top_l:
    grade = ev.get("grade", "Weak")
    score = ev.get("overall_score", 0)
    conf = float(ev.get("confidence", 0)) * 100
    st.markdown(
        f"""
        <div class="score-box">
          <div style="font-size: 14px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Overall Score</div>
          <div class="score-value">{score} <span style="font-size: 18px; color: var(--text-muted); font-weight: 400;">/ 100</span></div>
          <div style="margin-top: 15px; font-weight: 600;">
            <span style="background: { '#DCFCE7' if score > 70 else '#FEF3C7' if score > 40 else '#FEE2E2' }; color: { '#166534' if score > 70 else '#92400E' if score > 40 else '#991B1B' }; padding: 4px 12px; border-radius: 20px; font-size: 12px;">GRADE: {grade.upper()}</span>
            <span style="margin-left: 12px; color: var(--text-muted); font-size: 12px;">CONFIDENCE: {conf:.0f}%</span>
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
        <div class="panel-v2" style="background: var(--accent-indigo); color: white;">
          <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; opacity: 0.7; margin-bottom: 8px;">Recommendation</div>
          <div style="font-size: 28px; font-weight: 700; margin-bottom: 12px; font-family: 'Outfit';">[{rec.upper()}]</div>
          <div style="font-size: 14px; opacity: 0.9; line-height: 1.5;">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(
    f"""
    <div style="background: white; border: 1px solid var(--border-color); border-radius: 16px; padding: 24px;">
      <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 12px;">Executive Summary</div>
      <div style="color: var(--text-main); font-size: 15px; line-height: 1.7;">{ev.get("summary", "")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Strengths / Weaknesses ----------
st.markdown('<div style="font-family: \'Outfit\', sans-serif; font-size: 20px; font-weight: 600; margin: 3rem 0 1.5rem;">Profile Assessment</div>', unsafe_allow_html=True)
cA, cB = st.columns(2, gap="medium")
with cA:
    items = "".join(f"<li style='margin-bottom:8px'>{s}</li>" for s in ev.get("strengths", []))
    st.markdown(
        f'<div class="panel-v2" style="background:#F0FDF4; border-color:#BBF7D0">'
        f'<h4 style="font-size:13px; color:#166534; margin:0 0 15px">✓ CORE STRENGTHS</h4><ul style="padding-left:18px; font-size:14px; color:#14532D">{items or "<li>None identified</li>"}</ul></div>',
        unsafe_allow_html=True,
    )
with cB:
    items = "".join(f"<li style='margin-bottom:8px'>{s}</li>" for s in ev.get("weaknesses", []))
    st.markdown(
        f'<div class="panel-v2" style="background:#FEF2F2; border-color:#FECACA">'
        f'<h4 style="font-size:13px; color:#991B1B; margin:0 0 15px">✗ AREAS FOR IMPROVEMENT</h4><ul style="padding-left:18px; font-size:14px; color:#7F1D1D">{items or "<li>None identified</li>"}</ul></div>',
        unsafe_allow_html=True,
    )

# ---------- Breakdown ----------
st.markdown('<div style="font-family: \'Outfit\', sans-serif; font-size: 20px; font-weight: 600; margin: 3rem 0 1.5rem;">Score Analytics</div>', unsafe_allow_html=True)
dims = ev.get("dimension_scores", {})
max_map = {"jd_match": 40, "cv_quality": 25, "experience_depth": 10, "formatting": 15, "risk": 10}
labels = {
    "jd_match": "REQUIREMENT MATCH",
    "cv_quality": "DOCUMENT QUALITY",
    "experience_depth": "EXPERIENCE DEPTH",
    "formatting": "FORMATTING / PARSING",
    "risk": "RISK ASSESSMENT (HIGHER = SAFER)",
}
st.markdown('<div class="panel-v2">', unsafe_allow_html=True)
for key, mx in max_map.items():
    render_score_bar(labels[key], float(dims.get(key, 0)), mx)
    st.write("")
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Issues & Improvements ----------
st.markdown('<div style="font-family: \'Outfit\', sans-serif; font-size: 20px; font-weight: 600; margin: 3rem 0 1.5rem;">Detailed Audit</div>', unsafe_allow_html=True)
imp = ev.get("improvements", {})

with st.expander("CONTENT AUDIT", expanded=True):
    issues = imp.get("content_issues", [])
    if not issues:
        st.markdown("*No significant content issues detected.*")
    for i, issue in enumerate(issues, 1):
        st.markdown(f"**ITEM {i} — `{issue.get('issue_type', '').upper()}`**")
        st.markdown(f"**Original Text:** {issue.get('original', '')}")
        st.markdown(f"**Identified Problem:** {issue.get('problem', '')}")
        st.markdown(
            f"**Suggested Revision:** {issue.get('improved_version', '')}")
        st.divider()

with st.expander("SKILL GAP ANALYSIS"):
    gaps = imp.get("skill_gaps", {})
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("**CRITICAL MISSING**")
        for s in gaps.get("critical_missing", []):
            st.markdown(f"- {s}")
    with g2:
        st.markdown("**SECONDARY MISSING**")
        for s in gaps.get("secondary_missing", []):
            st.markdown(f"- {s}")
    with g3:
        st.markdown("**TRANSFERABLE**")
        for s in gaps.get("transferable", []):
            st.markdown(f"- {s}")

with st.expander("POSITIONING EVALUATION"):
    for p in imp.get("positioning_issues", []):
        st.markdown(f"**Observation:** {p.get('problem', '')}")
        st.markdown(
            f"**Alternative Framing:**\n{p.get('rewritten_summary', '')}")
        st.divider()

with st.expander("EXPERIENCE CONTINUITY"):
    for x in imp.get("experience_issues", []):
        st.markdown(f"- {x}")

with st.expander("STRUCTURAL COMPLIANCE"):
    for x in imp.get("formatting_issues", []):
        st.markdown(f"- {x}")

with st.expander("RISK INDICATORS"):
    flags = imp.get("red_flags", [])
    if not flags:
        st.markdown("*No primary risk indicators detected.*")
    for f in flags:
        st.markdown(
            f"- **{f.get('flag', '')}** — {f.get('risk_explanation', '')}")

# ---------- Suggestions ----------
st.markdown('<div class="section-label">Actionable Directives</div>',
            unsafe_allow_html=True)
sug = ev.get("suggestions", {})
tab1, tab2, tab3 = st.tabs(
    ["TACTICAL FIXES", "STRUCTURAL CHANGES", "STRATEGIC ADVICE"])
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
with st.expander("RAW SYSTEM PAYLOAD"):
    st.json(
        {
            "jd_understanding": result.jd_understanding,
            "cv_understanding": result.cv_understanding,
            "evaluation": ev,
        }
    )

st.download_button(
    "DOWNLOAD JSON REPORT",
    data=json.dumps(
        {
            "jd_understanding": result.jd_understanding,
            "cv_understanding": result.cv_understanding,
            "evaluation": ev,
        },
        indent=2,
        ensure_ascii=False,
    ),
    file_name="evaluation_record.json",
    mime="application/json",
    use_container_width=True,
)
