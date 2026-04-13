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
    page_title="AI Resume Screening",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Design tokens + global styles ----------
st.markdown(
    """
    <style>
      /* ---------- Formal Minimalist Design Tokens ---------- */
      :root {
        --bg-primary: #FFFFFF;
        --bg-secondary: #F9FAFB;
        --text-primary: #000000;
        --text-secondary: #4B5563;
        --border-default: #D1D5DB;
        --border-strong: #000000;
        --action-primary: #000000;
        --action-hover: #374151;
        --status-pass: #065F46;
        --status-warn: #92400E;
        --status-fail: #991B1B;
      }

      html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: var(--text-primary);
      }
      .stApp { background: var(--bg-primary); }

      /* ---------- Container ---------- */
      .main .block-container {
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 1120px;
      }

      /* ---------- Header Formatting ---------- */
      .eyebrow {
        display: inline-block;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        margin-bottom: 8px;
      }
      h1.brand {
        font-weight: 700;
        font-size: 28px;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin: 0 0 16px 0;
        border-bottom: 2px solid var(--text-primary);
        padding-bottom: 8px;
      }
      .sub {
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 1.6;
        max-width: 640px;
        margin-bottom: 2rem;
      }

      /* ---------- Panels / Cards ---------- */
      .panel {
        background: var(--bg-primary);
        border: 1px solid var(--border-default);
        border-radius: 0px;
        padding: 16px;
        box-shadow: none;
        height: 100%;
      }
      .panel-head {
        margin-bottom: 16px;
        border-bottom: 1px solid var(--border-default);
        padding-bottom: 8px;
      }
      .panel-title {
        font-weight: 600;
        font-size: 16px;
        color: var(--text-primary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0;
      }
      .panel-hint {
        color: var(--text-secondary);
        font-size: 12px;
        margin: 4px 0 0 0;
      }

      /* ---------- Inputs ---------- */
      .stTextArea textarea, .stTextInput input, .stSelectbox > div[data-baseweb="select"] > div {
        border-radius: 0px !important;
        border: 1px solid var(--border-default) !important;
        background: var(--bg-primary) !important;
        font-size: 14px !important;
        box-shadow: none !important;
        color: var(--text-primary) !important;
      }
      .stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox > div[data-baseweb="select"] > div:focus-within {
        border: 1px solid var(--border-strong) !important;
        box-shadow: none !important;
      }
      [data-testid="stFileUploader"] section {
        border-radius: 0px !important;
        border: 1px dashed var(--border-strong) !important;
        background: var(--bg-secondary) !important;
        padding: 16px !important;
      }

      /* ---------- Buttons ---------- */
      .stButton > button {
        background: var(--action-primary) !important;
        color: white !important;
        border: 1px solid var(--action-primary) !important;
        border-radius: 0px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.02em !important;
        box-shadow: none !important;
        text-transform: uppercase !important;
        transition: background 150ms ease !important;
      }
      .stButton > button:hover {
        background: var(--action-hover) !important;
      }

      /* ---------- Report Sections ---------- */
      .report-head {
        margin: 3rem 0 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--text-primary);
      }
      .report-head h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 700;
        text-transform: uppercase;
      }
      .section-label {
        font-size: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-primary);
        margin: 2rem 0 1rem;
        border-bottom: 1px solid var(--border-default);
        padding-bottom: 4px;
      }

      /* ---------- Score & Decision Cards ---------- */
      .score-card {
        background: var(--bg-primary);
        color: var(--text-primary);
        border: 1px solid var(--border-strong);
        border-radius: 0px;
        padding: 16px;
      }
      .score-card .lbl {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
      }
      .score-card .big {
        font-size: 36px;
        font-weight: 700;
        margin-top: 8px;
        line-height: 1;
      }
      .score-meta {
        margin-top: 12px;
        font-size: 12px;
        font-weight: 600;
      }

      .decision-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-strong);
        border-radius: 0px;
        padding: 16px;
        height: 100%;
      }
      .decision-card .dec-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
      }
      .decision-card .dec-value {
        font-size: 24px;
        font-weight: 700;
        margin: 8px 0;
        text-transform: uppercase;
      }
      .decision-card .dec-reason {
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 1.5;
      }

      /* ---------- Lists ---------- */
      .list-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-default);
        border-radius: 0px;
        padding: 16px;
        height: 100%;
      }
      .list-card h4 {
        margin: 0 0 12px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-primary);
      }
      .list-card ul { margin: 0; padding-left: 16px; }
      .list-card li {
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 8px;
      }

      /* ---------- Progress Bars ---------- */
      .stProgress > div > div > div > div {
        background: var(--text-primary) !important;
        border-radius: 0px !important;
      }
      .stProgress > div > div > div {
        background: var(--border-default) !important;
        border-radius: 0px !important;
      }

      /* ---------- Expanders & Tabs ---------- */
      .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        border-radius: 0px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border-default) !important;
      }
      [data-testid="stExpander"] {
        border: 1px solid var(--border-default) !important;
        border-radius: 0px !important;
        background: var(--bg-primary) !important;
        margin-bottom: 16px !important;
        box-shadow: none !important;
      }
      
      .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: transparent;
        padding: 0px;
        border-bottom: 1px solid var(--border-default);
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 0px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 12px 24px !important;
        border: none !important;
        background: transparent !important;
      }
      .stTabs [aria-selected="true"] {
        border-bottom: 2px solid var(--border-strong) !important;
        color: var(--text-primary) !important;
      }

      hr { border-color: var(--border-default) !important; margin: 2rem 0 !important; }
      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown('<div class="eyebrow">Recruiter Assessment Panel</div>',
            unsafe_allow_html=True)
st.markdown('<h1 class="brand">CANDIDATE SCREENING REPORT</h1>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Input job requirements and candidate profile to generate a formal evaluation report.</p>',
    unsafe_allow_html=True,
)

# ---------- Input grid ----------
col_jd, col_cv = st.columns(2, gap="large")

with col_jd:
    st.markdown(
        '<div class="panel"><div class="panel-head">'
        '<div><p class="panel-title">1. Job Description</p>'
        '<p class="panel-hint">Paste full requirements and role context.</p></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    jd_text = st.text_area(
        "JD",
        height=320,
        key="jd_text",
        label_visibility="collapsed",
        placeholder="Enter standard job description text here...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cv:
    st.markdown(
        '<div class="panel"><div class="panel-head">'
        '<div><p class="panel-title">2. Candidate Profile</p>'
        '<p class="panel-hint">Upload text-extractable document (PDF, DOCX, TXT).</p></div>'
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
    LEVELS = ["Intern", "Fresher", "Junior", "Mid",
              "Senior", "Lead", "Principal", "Manager"]

    dc1, dc2 = st.columns(2, gap="small")
    with dc1:
        st.markdown(
            '<div style="font-size:12px;font-weight:600;color:var(--text-secondary);'
            'margin-bottom:4px;text-transform:uppercase;">Job Title</div>',
            unsafe_allow_html=True,
        )

        def _search_jobs(term: str) -> list[str]:
            term = (term or "").strip()
            if not term:
                return JOB_TITLES
            low = term.lower()
            matches = [j for j in JOB_TITLES if low in j.lower()]
            if term not in matches:
                matches = [term] + matches
            return matches

        job_title = st_searchbox(
            _search_jobs,
            key="job_title_search",
            placeholder="Enter role...",
            default_use_searchterm=True,
        )
    with dc2:
        st.markdown(
            '<div style="font-size:12px;font-weight:600;color:var(--text-secondary);'
            'margin-bottom:4px;text-transform:uppercase;">Level</div>',
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

# Right-sized CTA
btn_l, btn_c, btn_r = st.columns([1, 1.2, 1])
with btn_c:
    analyze = st.button("Generate Evaluation Report",
                        type="primary", use_container_width=True)


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
            f'<div style="font-size:12px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;margin-bottom:4px">{label}</div>',
            unsafe_allow_html=True,
        )
        st.progress(pct)
    with c2:
        st.markdown(
            f'<div style="text-align:right;font-size:14px;font-weight:700;padding-top:2px">'
            f'{value:.0f}<span style="color:var(--text-secondary);font-weight:400"> / {max_value:.0f}</span></div>',
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
    '<div class="report-head"><h2>Evaluation Results</h2></div>',
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
        <div class="score-card">
          <div class="lbl">Overall Composite Score</div>
          <div class="big">{score} <span style="font-size: 14px; font-weight: normal; color: var(--text-secondary);">/ 100</span></div>
          <div class="score-meta">
            <span>GRADE: {get_grade_label(grade)}</span>
            <span style="margin-left: 16px; color: var(--text-secondary);">CONF: {conf:.0f}%</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_r:
    rec = ev.get("hiring_decision", {}).get("recommendation", "Consider")
    reason = ev.get("hiring_decision", {}).get("reason", "")

    # Decide label color conceptually, but use black border physically
    st.markdown(
        f"""
        <div class="decision-card">
          <div class="dec-label">Hiring Recommendation</div>
          <div class="dec-value">{get_recommendation_label(rec)}</div>
          <div class="dec-reason">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown(
    '<div style="border:1px solid var(--border-default); background:var(--bg-secondary); padding:16px;">'
    '<div style="font-size:12px;font-weight:600;text-transform:uppercase;color:var(--text-primary);margin-bottom:8px;">Executive Summary</div>'
    f'<div style="color:var(--text-secondary);font-size:14px;line-height:1.6">{ev.get("summary", "")}</div>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------- Strengths / Weaknesses ----------
st.markdown('<div class="section-label">Profile Assessment</div>',
            unsafe_allow_html=True)
cA, cB = st.columns(2, gap="medium")
with cA:
    items = "".join(f"<li>{s}</li>" for s in ev.get("strengths", []))
    st.markdown(
        f'<div class="list-card">'
        f'<h4>IDENTIFIED STRENGTHS</h4><ul>{items or "<li>None identified</li>"}</ul></div>',
        unsafe_allow_html=True,
    )
with cB:
    items = "".join(f"<li>{w}</li>" for w in ev.get("weaknesses", []))
    st.markdown(
        f'<div class="list-card">'
        f'<h4>IDENTIFIED WEAKNESSES</h4><ul>{items or "<li>None identified</li>"}</ul></div>',
        unsafe_allow_html=True,
    )

# ---------- Breakdown ----------
st.markdown('<div class="section-label">Score Analytics</div>',
            unsafe_allow_html=True)
dims = ev.get("dimension_scores", {})
max_map = {"jd_match": 40, "cv_quality": 25,
           "experience_depth": 10, "formatting": 15, "risk": 10}
labels = {
    "jd_match": "REQUIREMENT MATCH",
    "cv_quality": "DOCUMENT QUALITY",
    "experience_depth": "EXPERIENCE DEPTH",
    "formatting": "FORMATTING / PARSING",
    "risk": "RISK ASSESSMENT (HIGHER = SAFER)",
}
st.markdown(
    '<div style="border:1px solid var(--border-default); padding:16px;">',
    unsafe_allow_html=True,
)
for key, mx in max_map.items():
    render_score_bar(labels[key], float(dims.get(key, 0)), mx)
    st.write("")
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Issues & Improvements ----------
st.markdown('<div class="section-label">Detailed Audit</div>',
            unsafe_allow_html=True)
imp = ev.get("improvements", {})

with st.expander("CONTENT AUDIT", expanded=True):
    issues = imp.get("content_issues", [])
    if not issues:
        st.markdown("*No significant content issues detetced.*")
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
