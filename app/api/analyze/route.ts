// app/api/analyze/route.ts
import { NextRequest } from "next/server";
import { parseCVBuffer } from "@/lib/cv-parser";
import { screenCandidate, isGroqModel, DEFAULT_MODEL } from "@/lib/ai-engine";
import { ProgressEvent } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 120; // 2 min timeout for Vercel Pro / self-hosted

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
        const formData = await req.formData();
        const jdText = formData.get("jd_text") as string | null;
        const cvFile = formData.get("cv_file") as File | null;
        const model = (formData.get("model") as string | null) ?? DEFAULT_MODEL;

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

        send({ type: "progress", message: `📂 Parsing CV (${cvFile.name})…` });

        const bytes = await cvFile.arrayBuffer();
        const buffer = Buffer.from(bytes);
        const cvText = await parseCVBuffer(buffer, cvFile.name);

        if (cvText.length < 80) {
          send({
            type: "progress",
            message: "⚠️  CV looks very short — scanned PDF? Text may be limited.",
          });
        }

        send({
          type: "progress",
          message: `   ✓ CV parsed — ${cvText.length.toLocaleString()} characters`,
        });

        const result = await screenCandidate(jdText, cvText, model, (msg) => {
          send({ type: "progress", message: msg });
        });

        send({ type: "result", data: result });
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
