import { NextRequest } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth-options";
import { parseCVBuffer } from "@/lib/cv-parser";
import { screenCandidate, isGroqModel, DEFAULT_MODEL } from "@/lib/ai-engine";
import { ProgressEvent } from "@/lib/types";
import { uploadCVToCloudinary } from "@/lib/cloudinary";
import { appendSubmitTrace } from "@/lib/google-sheets";

export const runtime = "nodejs";
export const maxDuration = 120;

function extractIP(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0].trim() ??
    req.headers.get("x-real-ip") ??
    "unknown"
  );
}

export async function POST(req: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      function send(event: ProgressEvent) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(event)}\n\n`)
        );
      }

      try {
        // ── Auth ──────────────────────────────────────────────────────────
        const session = await getServerSession(authOptions);
        const userEmail = session?.user?.email ?? "anonymous";
        const userName  = session?.user?.name  ?? "anonymous";
        const ip        = extractIP(req);

        // ── Form data ─────────────────────────────────────────────────────
        const formData = await req.formData();
        const jdText  = formData.get("jd_text")  as string | null;
        const cvFile  = formData.get("cv_file")  as File   | null;
        const model   = (formData.get("model")   as string | null) ?? DEFAULT_MODEL;
        const position = (formData.get("position") as string | null) ?? "";
        const level    = (formData.get("level")    as string | null) ?? "";
        const compareMarket = formData.get("compare_market") === "true";

        if (!jdText?.trim()) {
          send({ type: "error", message: "Job Description is required." });
          controller.close();
          return;
        }
        if (!cvFile) {
          send({ type: "error", message: "CV file is required." });
          controller.close();
          return;
        }

        const needsGroq = isGroqModel(model);
        if (needsGroq && !process.env.GROQ_API_KEY) {
          send({ type: "error", message: "GROQ_API_KEY is not set in .env.local" });
          controller.close();
          return;
        }
        if (!needsGroq && !process.env.ANTHROPIC_API_KEY) {
          send({ type: "error", message: "ANTHROPIC_API_KEY is not set in .env.local" });
          controller.close();
          return;
        }

        // ── Parse CV buffer ───────────────────────────────────────────────
        send({ type: "progress", message: `📂 Parsing CV (${cvFile.name})…` });
        const bytes  = await cvFile.arrayBuffer();
        const buffer = Buffer.from(bytes);
        const cvText = await parseCVBuffer(buffer, cvFile.name);

        if (cvText.length < 80) {
          send({ type: "progress", message: "⚠️  CV looks very short — scanned PDF? Text may be limited." });
        }
        send({ type: "progress", message: `   ✓ CV parsed — ${cvText.length.toLocaleString()} characters` });

        // ── Upload CV to Cloudinary (non-blocking for user) ───────────────
        let cvUrl = "";
        if (process.env.CLOUDINARY_API_KEY && process.env.CLOUDINARY_API_SECRET) {
          try {
            const uploaded = await uploadCVToCloudinary(buffer, cvFile.name, userEmail);
            cvUrl = uploaded.secure_url;
          } catch (cloudErr) {
            console.error("[cloudinary-upload] error:", cloudErr);
          }
        }

        // ── AI analysis ───────────────────────────────────────────────────
        const result = await screenCandidate(jdText, cvText, model, position, level, compareMarket, (msg) => {
          send({ type: "progress", message: msg });
        });


        send({ type: "result", data: result });

        // ── Log to Submit Trace (fire-and-forget) ─────────────────────────
        if (process.env.GOOGLE_SHEET_ID && process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
          appendSubmitTrace({
            email:          userEmail,
            name:           userName,
            ip,
            position,
            level,
            model,
            jdSnippet:      jdText.slice(0, 300).replace(/\n/g, " "),
            cvFilename:     cvFile.name,
            cvUrl,
            score:          result.evaluation.overall_score,
            grade:          result.evaluation.grade,
            recommendation: result.evaluation.hiring_decision.recommendation,
            confidence:     result.evaluation.confidence,
            summary:        result.evaluation.summary.slice(0, 200),
          }).catch((err) => console.error("[submit-trace] sheets error:", err));
        }

      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        send({ type: "error", message: msg });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}