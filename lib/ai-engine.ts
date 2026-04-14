// lib/ai-engine.ts  — server-side only
import Anthropic from "@anthropic-ai/sdk";
import Groq from "groq-sdk";
import {
  Evaluation,
  JDUnderstanding,
  CVUnderstanding,
  ScreeningResult,
} from "./types";
import {
  SYSTEM_PROMPT,
  JD_EXTRACTION_PROMPT,
  CV_EXTRACTION_PROMPT,
  EVALUATION_PROMPT,
} from "./prompts";

export const DEFAULT_MODEL = process.env.CV_SCORING_MODEL ?? "claude-sonnet-4-6";

export function isGroqModel(model: string) {
  return ["llama", "mixtral", "gemma", "tên-model-khác"].some((k) => model.toLowerCase().includes(k));
}

function parseJSON<T>(raw: string): T {
  let text = raw.trim();
  if (text.startsWith("```")) {
    text = text.replace(/^```[a-z]*\n?/, "").replace(/```$/, "").trim();
  }
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start !== -1 && end !== -1) text = text.slice(start, end + 1);
  return JSON.parse(text) as T;
}

async function callGroq<T>(model: string, prompt: string, maxTokens = 8000): Promise<T> {
  const key = process.env.GROQ_API_KEY;
  if (!key) throw new Error("GROQ_API_KEY is not set in .env.local");

  const client = new Groq({ apiKey: key });
  const stream = await client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: prompt },
    ],
    max_tokens: Math.min(maxTokens, 8000), // Groq output limit
    temperature: 0,
    stream: true,
  });

  const chunks: string[] = [];
  for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta?.content;
    if (delta) chunks.push(delta);
  }
  return parseJSON<T>(chunks.join(""));
}

async function callClaude<T>(model: string, prompt: string, maxTokens = 8000): Promise<T> {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error("ANTHROPIC_API_KEY is not set in .env.local");

  const client = new Anthropic({ apiKey: key });
  const stream = await client.messages.stream({
    model,
    max_tokens: maxTokens,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: prompt }],
  });
  const msg = await stream.finalMessage();
  const text = msg.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("");

  return parseJSON<T>(text);
}

async function callLLM<T>(model: string, prompt: string, maxTokens = 8000): Promise<T> {
  return isGroqModel(model)
    ? callGroq<T>(model, prompt, maxTokens)
    : callClaude<T>(model, prompt, maxTokens);
}

export async function extractJD(model: string, jdText: string): Promise<JDUnderstanding> {
  return callLLM<JDUnderstanding>(model, JD_EXTRACTION_PROMPT(jdText));
}

export async function extractCV(model: string, cvText: string): Promise<CVUnderstanding> {
  return callLLM<CVUnderstanding>(model, CV_EXTRACTION_PROMPT(cvText));
}

export async function evaluate(
  model: string,
  jdJson: JDUnderstanding,
  cvJson: CVUnderstanding,
  cvRaw: string
): Promise<Evaluation> {
  const ev = await callLLM<Evaluation>(
    model,
    EVALUATION_PROMPT(
      JSON.stringify(jdJson, null, 2),
      JSON.stringify(cvJson, null, 2),
      cvRaw
    ),
    isGroqModel(model) ? 8000 : 16000 // Groq caps at 8k output
  );
  return normalizeEvaluation(ev);
}

export async function screenCandidate(
  jdText: string,
  cvText: string,
  model: string,
  onProgress: (msg: string) => void
): Promise<ScreeningResult> {
  const provider = isGroqModel(model) ? "Groq" : "Claude";
  onProgress(`🔌 Connecting to ${provider} (${model})…`);

  onProgress("📋 Step 1/3 — Reading Job Description…");
  const jd = await extractJD(model, jdText);
  onProgress(`   ✓ JD parsed — ${jd.role_title} · ${jd.seniority_level}`);

  onProgress("📄 Step 2/3 — Parsing CV…");
  const cv = await extractCV(model, cvText);
  onProgress(`   ✓ CV parsed — ${cv.candidate_name} · ${cv.career_trajectory.slice(0, 60)}`);

  onProgress("🧠 Step 3/3 — Senior panel evaluating…");
  const evaluation = await evaluate(model, jd, cv, cvText);
  onProgress(
    `   ✓ Done — ${evaluation.overall_score}/100 · ${evaluation.grade} · ${evaluation.hiring_decision.recommendation}`
  );

  return { jd_understanding: jd, cv_understanding: cv, evaluation };
}

function normalizeEvaluation(ev: Partial<Evaluation>): Evaluation {
  const base: Evaluation = {
    overall_score: 0,
    grade: "Weak",
    confidence: 0,
    summary: "",
    strengths: [],
    weaknesses: [],
    dimension_scores: {
      jd_match: 0,
      cv_quality: 0,
      experience_depth: 0,
      formatting: 0,
      risk: 0,
    },
    improvements: {
      content_issues: [],
      skill_gaps: { critical_missing: [], secondary_missing: [], transferable: [] },
      positioning_issues: [],
      experience_issues: [],
      formatting_issues: [],
      red_flags: [],
    },
    suggestions: { micro_fixes: [], macro_fixes: [], strategic_advice: [] },
    hiring_decision: { recommendation: "Consider", reason: "", top_risks: [] },
  };
  return { ...base, ...ev } as Evaluation;
}
