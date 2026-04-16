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
  return ["llama", "mixtral", "gemma", "openai/gpt-oss"].some((k) => model.toLowerCase().includes(k));
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

let currentGroqKeyIndex = 0;

async function callGroq<T>(model: string, prompt: string, maxTokens = 8000): Promise<T> {
  const keysStr = process.env.GROQ_API_KEY;
  if (!keysStr) throw new Error("GROQ_API_KEY is not set in .env.local");

  const keys = keysStr.split(',').map(k => k.trim()).filter(Boolean);
  if (keys.length === 0) throw new Error("No valid GROQ_API_KEY found");

  let lastError: any;

  for (let attempt = 0; attempt < keys.length; attempt++) {
    const key = keys[currentGroqKeyIndex % keys.length];
    currentGroqKeyIndex++;

    try {
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
    } catch (error: any) {
      lastError = error;
      if (error?.status === 429 || error?.response?.status === 429 || error?.message?.includes("429")) {
        console.warn(`[Groq] Key rate limited, switching to next key. Attempt ${attempt + 1}/${keys.length}`);
        continue;
      }
      throw error;
    }
  }

  throw lastError;
}

async function callClaude<T>(model: string, prompt: string, maxTokens = 8000): Promise<T> {
  const key = process.env.ANTHROPIC_API_KEY;
  model = process.env.CLAUDE_MODEL || "none";
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

export type Lang = "en" | "vi";

function langDirective(lang: Lang): string {
  if (lang === "vi") {
    return (
      "\n\nLANGUAGE REQUIREMENT: Write ALL natural-language string values in the output JSON " +
      "in Vietnamese (Tiếng Việt). This includes: summary, strengths, weaknesses, reason, " +
      "problem descriptions, improved_version, rewritten_summary, all suggestion items, " +
      "red_flag descriptions, and any human-readable text. Keep JSON KEYS, enum values " +
      "(grade: Strong Hire/Good Fit/Moderate/Weak, recommendation: Hire/Consider/Reject, " +
      "issue_type), numbers, and technical terms (programming languages, frameworks, tools) " +
      "in English. Do NOT translate proper nouns.\n"
    );
  }
  return "\n\nLANGUAGE REQUIREMENT: Write all natural-language output in English.\n";
}

async function callLLM<T>(model: string, prompt: string, lang: Lang, maxTokens = 8000): Promise<T> {
  const finalPrompt = prompt + langDirective(lang);
  return isGroqModel(model)
    ? callGroq<T>(model, finalPrompt, maxTokens)
    : callClaude<T>(model, finalPrompt, maxTokens);
}

export async function extractJD(model: string, jdText: string, lang: Lang = "en"): Promise<JDUnderstanding> {
  return callLLM<JDUnderstanding>(model, JD_EXTRACTION_PROMPT(jdText), lang);
}

export async function extractCV(model: string, cvText: string, lang: Lang = "en"): Promise<CVUnderstanding> {
  return callLLM<CVUnderstanding>(model, CV_EXTRACTION_PROMPT(cvText), lang);
}

export async function evaluate(
  model: string,
  jdJson: JDUnderstanding,
  cvJson: CVUnderstanding,
  cvRaw: string,
  position: string,
  level: string,
  compareMarket: boolean,
  lang: Lang = "en"
): Promise<Evaluation> {
  const ev = await callLLM<Evaluation>(
    model,
    EVALUATION_PROMPT(
      JSON.stringify(jdJson, null, 2),
      JSON.stringify(cvJson, null, 2),
      cvRaw,
      position,
      level,
      compareMarket
    ),
    lang as Lang,
    isGroqModel(model) ? 8000 : 16000
  );
  return normalizeEvaluation(ev, compareMarket);
}

export async function screenCandidate(
  jdText: string,
  cvText: string,
  model: string,
  position: string,
  level: string,
  compareMarket: boolean,
  onProgress: (msg: string) => void,
  lang: Lang = "en"
): Promise<ScreeningResult> {
  onProgress("📋 Step 1/3 — Reading Job Description…");
  const jd = await extractJD(model, jdText, lang);
  onProgress(`   ✓ JD parsed — ${jd.role_title} · ${jd.seniority_level}`);

  onProgress("📄 Step 2/3 — Parsing CV…");
  const cv = await extractCV(model, cvText, lang);
  onProgress(`   ✓ CV parsed — ${cv.candidate_name} · ${cv.career_trajectory.slice(0, 60)}`);

  onProgress("🧠 Step 3/3 — Senior panel evaluating…");
  const evaluation = await evaluate(model, jd, cv, cvText, position, level, compareMarket, lang);
  onProgress(
    `   ✓ Done — ${evaluation.overall_score}/100 · ${evaluation.grade} · ${evaluation.hiring_decision.recommendation}`
  );

  if (compareMarket && evaluation.market_comparison) {
    onProgress(`📊 Market insight — Top ${evaluation.market_comparison.market_rank_top_pct}% of ${position} (${level})`);
  }

  return { jd_understanding: jd, cv_understanding: cv, evaluation };
}

function normalizeEvaluation(ev: Partial<Evaluation>, compareMarket: boolean): Evaluation {
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

  const result = { ...base, ...ev } as Evaluation;

  // Normalize market_comparison if it was requested but came back incomplete
  if (compareMarket && result.market_comparison) {
    result.market_comparison = {
      market_rank_top_pct: result.market_comparison.market_rank_top_pct ?? 50,
      market_context: result.market_comparison.market_context ?? "",
      market_trends: result.market_comparison.market_trends ?? [],
      skill_alignment: result.market_comparison.skill_alignment ?? [],
      improvement_priority: result.market_comparison.improvement_priority ?? [],
      smart_action_plan: result.market_comparison.smart_action_plan ?? [],
    };
  }

  return result;
}
