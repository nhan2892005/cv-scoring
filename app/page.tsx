"use client";
import { useState, useRef, useCallback } from "react";
import { ScreeningResult, ProgressEvent } from "@/lib/types";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function gradeColor(grade: string) {
  return (
    {
      "Strong Hire": "#059669",
      "Good Fit": "#059669",
      Moderate: "#d97706",
      Weak: "#dc2626",
    }[grade] ?? "#6b7280"
  );
}

function recColor(rec: string) {
  return { Hire: "#059669", Consider: "#d97706", Reject: "#dc2626" }[rec] ?? "#6b7280";
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function Accordion({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="accordion">
      <div className="accordion-header" onClick={() => setOpen((o) => !o)}>
        {title}
        <span className={`accordion-chevron${open ? " open" : ""}`}>▼</span>
      </div>
      {open && <div className="accordion-body">{children}</div>}
    </div>
  );
}

function Tabs({
  tabs,
  children,
}: {
  tabs: string[];
  children: (active: number) => React.ReactNode;
}) {
  const [active, setActive] = useState(0);
  return (
    <div>
      <div className="tabs">
        {tabs.map((t, i) => (
          <button
            key={t}
            className={`tab-btn${active === i ? " active" : ""}`}
            onClick={() => setActive(i)}
          >
            {t}
          </button>
        ))}
      </div>
      {children(active)}
    </div>
  );
}

function MetricBar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="metric-row">
      <div className="metric-lbl">{label}</div>
      <div className="metric-track">
        <div className="metric-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="metric-val">
        {value} / {max}
      </div>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <polyline points="9 15 12 12 15 15" />
    </svg>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [jdText, setJdText] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [model, setModel] = useState("claude-sonnet-4-6");
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  const isGroq = ["llama", "mixtral", "gemma"].some((k) => model.includes(k));

  function addLog(msg: string) {
    setLogs((l) => [...l, msg]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }

  const handleSubmit = useCallback(async () => {
    if (!jdText.trim() || !cvFile) return;
    setRunning(true);
    setResult(null);
    setError(null);
    setLogs([]);

    const form = new FormData();
    form.append("jd_text", jdText);
    form.append("cv_file", cvFile);
    form.append("model", model);

    try {
      const res = await fetch("/api/analyze", { method: "POST", body: form });
      if (!res.body) throw new Error("No stream body returned.");

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const ev: ProgressEvent = JSON.parse(part.slice(6));
          if (ev.type === "progress") addLog(ev.message);
          else if (ev.type === "result") {
            setResult(ev.data);
            addLog("✅ Analysis complete");
          } else if (ev.type === "error") {
            setError(ev.message);
            addLog(`❌ ${ev.message}`);
          }
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setRunning(false);
    }
  }, [jdText, cvFile, model]);

  const ev = result?.evaluation;
  const imp = ev?.improvements;
  const sug = ev?.suggestions;
  const dim = ev?.dimension_scores;

  return (
    <>
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-inner">
            <div className="header-brand">
              <div className="header-logo">CV</div>
              <span className="header-title">CV Evaluation</span>
            </div>
            <span className="header-tag">Powered by BaoVo</span>
          </div>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="hero">
          <div className="container">
            <div className="hero-label">AI Hiring Assistant</div>
            <h1>Screen candidates <strong>smarter</strong>, not faster.</h1>
            <p className="hero-sub">
              Professional AI-powered CV analysis, multi-dimensional scoring, and
              concrete improvement suggestions — in seconds.
            </p>
          </div>
        </section>

        <div className="container">
          {/* Input form */}
          <div className="form-grid">
            {/* JD */}
            <div className="card">
              <div className="card-label">Job Description</div>
              <textarea
                placeholder="Paste the full job description here…"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            </div>

            {/* CV upload */}
            <div className="card">
              <div className="card-label">Candidate CV</div>
              <label
                className={`upload-zone${dragging ? " drag-over" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  const f = e.dataTransfer.files[0];
                  if (f) setCvFile(f);
                }}
              >
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
                />
                <div className="upload-icon">
                  <UploadIcon />
                </div>
                <div className="upload-title">
                  {cvFile ? cvFile.name : "Drop CV here or click to browse"}
                </div>
                <div className="upload-sub">PDF, DOCX, or TXT — text-based export</div>
                {cvFile && (
                  <div className="upload-filename">
                    {(cvFile.size / 1024).toFixed(0)} KB
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Model selector */}
          <div className="model-selector-row">
            <div className="model-selector">
              <span className="model-selector-label">Model</span>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                <optgroup label="Claude (Anthropic)">
                  <option value="claude-opus-4-6">claude-opus-4-6</option>
                  <option value="claude-sonnet-4-6">claude-sonnet-4-6</option>
                  <option value="claude-haiku-4-5">claude-haiku-4-5</option>
                </optgroup>
                <optgroup label="Llama (Groq)">
                  <option value="llama-3.2-70b-versatile">llama-3.2-70b-versatile</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                  <option value="llama3-70b-8192">llama3-70b-8192</option>
                </optgroup>
                <optgroup label="Other (Groq)">
                  <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                  <option value="gemma2-9b-it">gemma2-9b-it</option>
                </optgroup>
              </select>
              <span className={`model-badge ${isGroq ? "groq" : "anthropic"}`}>
                {isGroq ? "Groq" : "Anthropic"}
              </span>
            </div>
          </div>

          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={running || !jdText.trim() || !cvFile}
          >
            {running ? "Analyzing…" : "Run Evaluation"}
          </button>

          {/* Progress log */}
          {logs.length > 0 && (
            <div className="log-box" ref={logRef}>
              {logs.map((l, i) => (
                <span
                  key={i}
                  className={`log-line${l.startsWith("✅") ? " success" : l.startsWith("❌") ? " error" : ""}`}
                >
                  {l}
                  {"\n"}
                </span>
              ))}
            </div>
          )}

          {error && <div className="error-banner">⚠ {error}</div>}

          {/* ─── Results ─────────────────────────────────── */}
          {ev && dim && imp && sug && (
            <div className="results">
              <hr className="divider" />

              {/* ① Score + Decision */}
              <div className="section-heading">Evaluation Summary</div>
              <div className="results-grid-top">
                <div className="score-card">
                  <div className="score-label">Overall Score</div>
                  <div className="score-number">
                    {ev.overall_score}
                    <span className="score-denom"> /100</span>
                  </div>
                  <div>
                    <span
                      className="grade-pill"
                      style={{
                        background: gradeColor(ev.grade),
                        color: "#fff",
                      }}
                    >
                      {ev.grade}
                    </span>
                  </div>
                  <div className="score-conf">
                    Confidence: {Math.round(ev.confidence * 100)}%
                  </div>
                </div>

                <div
                  className="decision-card"
                  style={{
                    borderLeftColor: recColor(ev.hiring_decision.recommendation),
                  }}
                >
                  <div className="decision-label-sm">Hiring Recommendation</div>
                  <div
                    className="decision-value"
                    style={{ color: recColor(ev.hiring_decision.recommendation) }}
                  >
                    {ev.hiring_decision.recommendation}
                  </div>
                  <div className="decision-reason">
                    {ev.hiring_decision.reason}
                  </div>
                  <div className="decision-summary">{ev.summary}</div>
                </div>
              </div>

              <hr className="divider" />

              {/* ② Strengths / Weaknesses */}
              <div className="section-heading">Strengths &amp; Weaknesses</div>
              <div className="sw-grid">
                <div>
                  <div className="card-label">Strengths</div>
                  {ev.strengths.map((s, i) => (
                    <div key={i} className="list-item">
                      {s}
                    </div>
                  ))}
                </div>
                <div>
                  <div className="card-label">Weaknesses</div>
                  {ev.weaknesses.map((w, i) => (
                    <div key={i} className="list-item">
                      {w}
                    </div>
                  ))}
                </div>
              </div>

              <hr className="divider" />

              {/* ③ Score Breakdown */}
              <div className="section-heading">Score Breakdown</div>
              <MetricBar label="JD Match" value={dim.jd_match} max={40} />
              <MetricBar label="CV Quality" value={dim.cv_quality} max={25} />
              <MetricBar label="Experience Depth" value={dim.experience_depth} max={10} />
              <MetricBar label="Formatting / ATS" value={dim.formatting} max={15} />
              <MetricBar label="Risk Indicator" value={dim.risk} max={10} />

              <hr className="divider" />

              {/* ④ Issues */}
              <div className="section-heading">Issues &amp; Improvements</div>

              <Accordion title="Content Issues — bullet rewrites" defaultOpen>
                {imp.content_issues.length === 0 ? (
                  <p className="empty-text">
                    No major content issues detected.
                  </p>
                ) : (
                  imp.content_issues.map((issue, i) => (
                    <div key={i} className="issue-card">
                      <div className="issue-type">{issue.issue_type}</div>
                      <div className="issue-original">{issue.original}</div>
                      <div className="issue-problem">{issue.problem}</div>
                      <div className="issue-improved">{issue.improved_version}</div>
                    </div>
                  ))
                )}
              </Accordion>

              <Accordion title="Skill Gaps">
                <div className="skill-gaps-grid">
                  <div>
                    <div className="card-label">Critical Missing</div>
                    {imp.skill_gaps.critical_missing.map((s, i) => (
                      <span key={i} className="badge badge-red">{s}</span>
                    ))}
                  </div>
                  <div>
                    <div className="card-label">Secondary Missing</div>
                    {imp.skill_gaps.secondary_missing.map((s, i) => (
                      <span key={i} className="badge badge-amber">{s}</span>
                    ))}
                  </div>
                  <div>
                    <div className="card-label">Transferable</div>
                    {imp.skill_gaps.transferable.map((s, i) => (
                      <span key={i} className="badge badge-green">{s}</span>
                    ))}
                  </div>
                </div>
              </Accordion>

              <Accordion title="Positioning">
                <div style={{ paddingTop: "0.5rem" }}>
                  {imp.positioning_issues.map((p, i) => (
                    <div key={i} className="pos-block">
                      <div className="pos-problem">Problem: {p.problem}</div>
                      <div className="pos-rewrite">{p.rewritten_summary}</div>
                    </div>
                  ))}
                </div>
              </Accordion>

              <Accordion title="Experience Issues">
                {imp.experience_issues.map((x, i) => (
                  <div key={i} className="list-item">
                    {x}
                  </div>
                ))}
              </Accordion>

              <Accordion title="Formatting / ATS">
                {imp.formatting_issues.map((x, i) => (
                  <div key={i} className="list-item">
                    {x}
                  </div>
                ))}
              </Accordion>

              <Accordion title="Red Flags">
                {imp.red_flags.length === 0 ? (
                  <p className="empty-text">
                    No red flags detected.
                  </p>
                ) : (
                  imp.red_flags.map((f, i) => (
                    <div key={i} className="flag-row">
                      <div className="flag-name">{f.flag}</div>
                      <div>{f.risk_explanation}</div>
                    </div>
                  ))
                )}
              </Accordion>

              <hr className="divider" />

              {/* ⑤ Suggestions */}
              <div className="section-heading">Suggestions</div>
              <Tabs tabs={["Micro Fixes", "Macro Fixes", "Strategic Advice"]}>
                {(active) => {
                  const lists = [sug.micro_fixes, sug.macro_fixes, sug.strategic_advice];
                  return (
                    <div>
                      {lists[active].map((s, i) => (
                        <div key={i} className="list-item">
                          {s}
                        </div>
                      ))}
                    </div>
                  );
                }}
              </Tabs>

              <hr className="divider" />

              {/* ⑥ Download / Raw JSON */}
              <div className="download-row">
                <button className="btn-outline" onClick={() => setShowJson((v) => !v)}>
                  {showJson ? "Hide" : "Show"} Raw JSON
                </button>
                <a
                  className="btn-outline"
                  href={`data:application/json;charset=utf-8,${encodeURIComponent(
                    JSON.stringify(result, null, 2)
                  )}`}
                  download="cv_evaluation_report.json"
                >
                  Download JSON
                </a>
              </div>

              {showJson && (
                <pre className="json-pre" style={{ marginTop: "0.75rem" }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
