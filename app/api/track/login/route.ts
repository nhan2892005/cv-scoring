import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth-options";
import { appendLoginTrace } from "@/lib/google-sheets";

function extractIP(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0].trim() ??
    req.headers.get("x-real-ip") ??
    "unknown"
  );
}

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.email) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Fire-and-forget — we don't want to block the client
    appendLoginTrace({
      email: session.user.email,
      name: session.user.name ?? "",
      image: session.user.image ?? "",
      ip: extractIP(req),
      userAgent: req.headers.get("user-agent") ?? "unknown",
    }).catch((err) => console.error("[login-trace] sheets error:", err));

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[login-trace] error:", err);
    // Always return 200 — tracking must never break the UI
    return NextResponse.json({ ok: false });
  }
}