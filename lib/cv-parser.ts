// lib/cv-parser.ts — server-side only
export async function parsePDF(buffer: Buffer): Promise<string> {
  // Dynamic import to avoid issues with Next.js bundler
  const pdfParse = (await import("pdf-parse")).default;
  const data = await pdfParse(buffer);
  return cleanText(data.text);
}

export async function parseDOCX(buffer: Buffer): Promise<string> {
  const mammoth = await import("mammoth");
  const result = await mammoth.extractRawText({ buffer });
  return cleanText(result.value);
}

export async function parseCVBuffer(
  buffer: Buffer,
  filename: string
): Promise<string> {
  const name = filename.toLowerCase();
  if (name.endsWith(".pdf")) return parsePDF(buffer);
  if (name.endsWith(".docx")) return parseDOCX(buffer);
  if (name.endsWith(".txt")) return cleanText(buffer.toString("utf-8"));
  throw new Error(`Unsupported file type: ${filename}. Use PDF, DOCX, or TXT.`);
}

function cleanText(text: string): string {
  const lines = text.split("\n").map((l) => l.trimEnd());
  const out: string[] = [];
  let blanks = 0;
  for (const line of lines) {
    if (!line.trim()) {
      blanks++;
      if (blanks <= 1) out.push("");
    } else {
      blanks = 0;
      out.push(line);
    }
  }
  return out.join("\n").trim();
}
