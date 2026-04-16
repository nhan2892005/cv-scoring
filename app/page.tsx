"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import { useSession, signIn, signOut } from "next-auth/react";
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
  const { data: session, status } = useSession();
  const [jdText, setJdText] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [model, setModel] = useState("claude-sonnet-4-6");
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);
  const [position, setPosition] = useState("Software Engineer");
  const [level, setLevel] = useState("Junior");
  const [compareMarket, setCompareMarket] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  const isGroq = ["llama", "mixtral", "gemma"].some((k) => model.includes(k));

  function addLog(msg: string) {
    setLogs((l) => [...l, msg]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 50);
  }

  const handleSubmit = useCallback(async () => {
    if (!session) {
      setError("Please sign in with Google to use the evaluation utility.");
      return;
    }
    if (!jdText.trim() || !cvFile) return;
    setRunning(true);
    setResult(null);
    setError(null);
    setLogs([]);

    const form = new FormData();
    form.append("jd_text", jdText);
    form.append("cv_file", cvFile);
    form.append("model", model);
    form.append("position", position);
    form.append("level", level);
    form.append("compare_market", String(compareMarket));

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
  }, [jdText, cvFile, model, position, level, compareMarket, session]);

  const ev = result?.evaluation;
  const imp = ev?.improvements;
  const sug = ev?.suggestions;
  const dim = ev?.dimension_scores;
  const mkt = ev?.market_comparison;

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
            {session && (
              <div className="header-auth">
                <div className="user-info">
                  {session.user?.image && (
                    <img src={session.user.image} alt="" className="user-avatar" />
                  )}
                  <span className="user-name">{session.user?.name}</span>
                </div>
                <button className="btn-logout" onClick={() => signOut()}>
                  Log out
                </button>
              </div>
            )}
            {!session && status !== "loading" && (
              <div className="header-auth">
                <button className="btn-google-header" onClick={() => signIn("google")}>
                  <svg viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  <span>Sign in with Google</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {status === "loading" && (
        <div className="auth-screen">
          <div className="loader">Loading...</div>
        </div>
      )}

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
            <div className="card">
              <div className="card-label">Job Description</div>
              <textarea
                placeholder="Paste the full job description here…"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            </div>

            <div className="card">
              <div className="card-label">Candidate CV</div>
              <label
                className={`upload-zone${dragging ? " drag-over" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
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
                <div className="upload-icon"><UploadIcon /></div>
                <div className="upload-title">
                  {cvFile ? cvFile.name : "Drop CV here or click to browse"}
                </div>
                <div className="upload-sub">PDF, DOCX, or TXT — text-based export</div>
                {cvFile && (
                  <div className="upload-filename">{(cvFile.size / 1024).toFixed(0)} KB</div>
                )}
              </label>
            </div>
          </div>

          {/* Context selectors */}
          <div className="config-grid">
            <div className="config-item">
              <span className="config-label">Position</span>
              <input
                type="text"
                list="positions"
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                placeholder="Select or type..."
              />
              <datalist id="positions">
                <option value="Software Engineer" />
                <option value="Frontend Developer" />
                <option value="Backend Developer" />
                <option value="Fullstack Developer" />
                <option value="Mobile Developer" />
                <option value="DevOps Engineer" />
                <option value="Data Scientist" />
                <option value="AI/ML Engineer" />
                <option value="Product Manager" />
                <option value="Project Manager" />
                <option value="QA/Tester" />
                <option value="UI/UX Designer" />
              </datalist>
            </div>

            <div className="config-item">
              <span className="config-label">Level</span>
              <input
                type="text"
                list="levels"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                placeholder="Select or type..."
              />
              <datalist id="levels">
                <option value="Intern / Fresher" />
                <option value="Junior" />
                <option value="Middle / Specialist" />
                <option value="Senior" />
                <option value="Lead / Staff" />
                <option value="Manager / Director" />
              </datalist>
            </div>

            <div className="config-item">
              <span className="config-label">AI Model</span>
              <select value={model} onChange={(e) => setModel(e.target.value)}>
                <optgroup label="Claude (Anthropic)">
                  <option value="llama-3.1-8b-instant">claude-opus-4-6</option>
                  <option value="llama-3.1-8b-instant">claude-sonnet-4-6</option>
                  <option value="llama-3.1-8b-instant">claude-haiku-4-5</option>
                </optgroup>
                <optgroup label="Llama (Groq)">
                  <option value="llama-3.3-70b-versatile">llama-3.1-70b-versatile</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                </optgroup>
                <optgroup label="GPT OSS (Groq)">
                  <option value="openai/gpt-oss-120b">openai/gpt-oss-120b</option>
                  <option value="openai/gpt-oss-20b">openai/gpt-oss-20b</option>
                </optgroup>
              </select>
            </div>

            <div className="config-item flex-center">
              <label className="toggle-btn">
                <input
                  type="checkbox"
                  checked={compareMarket}
                  onChange={(e) => setCompareMarket(e.target.checked)}
                />
                <span className="toggle-slider"></span>
                <span className="toggle-text">Market Compare</span>
              </label>
            </div>
          </div>

          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={running || !jdText.trim() || !cvFile}
          >
            {running ? "Analyzing…" : "Run Evaluation"}
          </button>

          {logs.length > 0 && (
            <div className="log-box" ref={logRef}>
              {logs.map((l, i) => (
                <span
                  key={i}
                  className={`log-line${l.startsWith("✅") ? " success" : l.startsWith("❌") ? " error" : ""}`}
                >
                  {l}{"\n"}
                </span>
              ))}
            </div>
          )}

          {error && <div className="error-banner">⚠ {error}</div>}

          {/* ─── Results ─────────────────────────────────── */}
          {ev && dim && imp && sug && (
            <div className="results">
              <hr className="divider" />

              <div className="section-heading">Evaluation Summary</div>
              <div className="results-grid-top">
                <div className="score-card">
                  <div className="score-label">Overall Score</div>
                  <div className="score-number">
                    {ev.overall_score}<span className="score-denom"> /100</span>
                  </div>
                  <div>
                    <span className="grade-pill" style={{ background: gradeColor(ev.grade), color: "#fff" }}>
                      {ev.grade}
                    </span>
                  </div>
                  <div className="score-conf">Confidence: {Math.round(ev.confidence * 100)}%</div>
                </div>

                <div className="decision-card" style={{ borderLeftColor: recColor(ev.hiring_decision.recommendation) }}>
                  <div className="decision-label-sm">Hiring Recommendation</div>
                  <div className="decision-value" style={{ color: recColor(ev.hiring_decision.recommendation) }}>
                    {ev.hiring_decision.recommendation}
                  </div>
                  <div className="decision-reason">{ev.hiring_decision.reason}</div>
                  <div className="decision-summary">{ev.summary}</div>
                </div>
              </div>

              <hr className="divider" />

              <div className="section-heading">Strengths &amp; Weaknesses</div>
              <div className="sw-grid">
                <div>
                  <div className="card-label">Strengths</div>
                  {ev.strengths.map((s, i) => <div key={i} className="list-item">{s}</div>)}
                </div>
                <div>
                  <div className="card-label">Weaknesses</div>
                  {ev.weaknesses.map((w, i) => <div key={i} className="list-item">{w}</div>)}
                </div>
              </div>

              <hr className="divider" />

              <div className="section-heading">Score Breakdown</div>
              <MetricBar label="JD Match"          value={dim.jd_match}          max={40} />
              <MetricBar label="CV Quality"         value={dim.cv_quality}         max={25} />
              <MetricBar label="Experience Depth"   value={dim.experience_depth}   max={10} />
              <MetricBar label="Formatting / ATS"   value={dim.formatting}         max={15} />
              <MetricBar label="Risk Indicator"     value={dim.risk}               max={10} />

              <hr className="divider" />

              <div className="section-heading">Issues &amp; Improvements</div>

              <Accordion title="Content Issues — bullet rewrites" defaultOpen>
                {imp.content_issues.length === 0 ? (
                  <p className="empty-text">No major content issues detected.</p>
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
                    {imp.skill_gaps.critical_missing.map((s, i) => <span key={i} className="badge badge-red">{s}</span>)}
                  </div>
                  <div>
                    <div className="card-label">Secondary Missing</div>
                    {imp.skill_gaps.secondary_missing.map((s, i) => <span key={i} className="badge badge-amber">{s}</span>)}
                  </div>
                  <div>
                    <div className="card-label">Transferable</div>
                    {imp.skill_gaps.transferable.map((s, i) => <span key={i} className="badge badge-green">{s}</span>)}
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
                {imp.experience_issues.map((x, i) => <div key={i} className="list-item">{x}</div>)}
              </Accordion>

              <Accordion title="Formatting / ATS">
                {imp.formatting_issues.map((x, i) => <div key={i} className="list-item">{x}</div>)}
              </Accordion>

              <Accordion title="Red Flags">
                {imp.red_flags.length === 0 ? (
                  <p className="empty-text">No red flags detected.</p>
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

              <div className="section-heading">Suggestions</div>
              <Tabs tabs={["Micro Fixes", "Macro Fixes", "Strategic Advice"]}>
                {(active) => {
                  const lists = [sug.micro_fixes, sug.macro_fixes, sug.strategic_advice];
                  return (
                    <div>
                      {lists[active].map((s, i) => <div key={i} className="list-item">{s}</div>)}
                    </div>
                  );
                }}
              </Tabs>

              {/* ─── Market Insight ──────────────────────────── */}
              {mkt && (
                <>
                  <hr className="divider" />
                  <div className="section-heading">📊 Market Insight</div>

                  {/* Rank + Context */}
                  <div className="market-top-grid">
                    <div className="market-rank-card">
                      <div className="market-rank-ring">
                        <svg viewBox="0 0 120 120" className="rank-svg">
                          <circle cx="60" cy="60" r="52" className="rank-track" />
                          <circle
                            cx="60" cy="60" r="52"
                            className="rank-fill"
                            strokeDasharray={`${(1 - mkt.market_rank_top_pct / 100) * 327} 327`}
                          />
                        </svg>
                        <div className="rank-value">
                          <span className="rank-number">Top {mkt.market_rank_top_pct}%</span>
                        </div>
                      </div>
                      <div className="market-rank-label">Market Ranking</div>
                    </div>

                    <div className="market-context-card">
                      <div className="card-label">Market Context</div>
                      <p className="market-context-text">{mkt.market_context}</p>
                    </div>
                  </div>

                  {/* Market Trends */}
                  {mkt.market_trends.length > 0 && (
                    <Accordion title="🔥 What the Market Needs Now" defaultOpen>
                      <div className="market-trends-list">
                        {mkt.market_trends.map((trend, i) => (
                          <div key={i} className="market-trend-item">
                            <span className="trend-index">{i + 1}</span>
                            <span>{trend}</span>
                          </div>
                        ))}
                      </div>
                    </Accordion>
                  )}

                  {/* Skill Alignment */}
                  {mkt.skill_alignment.length > 0 && (
                    <Accordion title="🎯 How to Become What the Market Wants">
                      <div className="skill-alignment-list">
                        {mkt.skill_alignment.map((item, i) => (
                          <div key={i} className="alignment-item">
                            <span className="alignment-arrow">→</span>
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    </Accordion>
                  )}

                  {/* Improvement Priority */}
                  {mkt.improvement_priority.length > 0 && (
                    <Accordion title="⚡ Top Priorities (Highest Impact First)">
                      <div className="priority-list">
                        {mkt.improvement_priority.map((item, i) => (
                          <div key={i} className="priority-item">
                            <span className="priority-badge">#{i + 1}</span>
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    </Accordion>
                  )}

                  {/* Smart Action Plan */}
                  {mkt.smart_action_plan.length > 0 && (
                    <Accordion title="🗺️ Smart Action Plan (Phased Roadmap)" defaultOpen>
                      <div className="action-plan-timeline">
                        {mkt.smart_action_plan.map((phase, i) => (
                          <div key={i} className="plan-phase">
                            <div className="phase-header">
                              <span className="phase-dot" />
                              <span className="phase-title">{phase.phase}</span>
                            </div>
                            <div className="phase-actions">
                              {phase.actions.map((action, j) => (
                                <div key={j} className="phase-action-item">{action}</div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </Accordion>
                  )}
                </>
              )}

              <hr className="divider" />


              <div className="download-row">
                <button className="btn-outline" onClick={() => setShowJson((v) => !v)}>
                  {showJson ? "Hide" : "Show"} Raw JSON
                </button>
                <a
                  className="btn-outline"
                  href={`data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(result, null, 2))}`}
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