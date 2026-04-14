// lib/google-sheets.ts  — server-side only
import { google } from "googleapis";

function getAuth() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!raw) throw new Error("GOOGLE_SERVICE_ACCOUNT_KEY is not set");
  return new google.auth.GoogleAuth({
    credentials: JSON.parse(raw),
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
}

function sheetId() {
  const id = process.env.GOOGLE_SHEET_ID;
  if (!id) throw new Error("GOOGLE_SHEET_ID is not set");
  return id;
}

/* ── Login Trace ─────────────────────────────────────────────────────── */
export interface LoginTraceRow {
  email: string;
  name: string;
  image: string;
  ip: string;
  userAgent: string;
}

export async function appendLoginTrace(row: LoginTraceRow) {
  const sheets = google.sheets({ version: "v4", auth: getAuth() });
  await sheets.spreadsheets.values.append({
    spreadsheetId: sheetId(),
    range: "Login Trace!A:G",
    valueInputOption: "RAW",
    insertDataOption: "INSERT_ROWS",
    requestBody: {
      values: [[
        new Date().toISOString(),
        row.email,
        row.name,
        row.image,
        row.ip,
        row.userAgent,
        "google",
      ]],
    },
  });
}

/* ── Submit Trace ────────────────────────────────────────────────────── */
export interface SubmitTraceRow {
  email: string;
  name: string;
  ip: string;
  position: string;
  level: string;
  model: string;
  jdSnippet: string;   // first 300 chars
  cvFilename: string;
  cvDriveUrl: string;
  score: number;
  grade: string;
  recommendation: string;
  confidence: number;
  summary: string;
}

export async function appendSubmitTrace(row: SubmitTraceRow) {
  const sheets = google.sheets({ version: "v4", auth: getAuth() });
  await sheets.spreadsheets.values.append({
    spreadsheetId: sheetId(),
    range: "Submit Trace!A:O",
    valueInputOption: "RAW",
    insertDataOption: "INSERT_ROWS",
    requestBody: {
      values: [[
        new Date().toISOString(),
        row.email,
        row.name,
        row.ip,
        row.position,
        row.level,
        row.model,
        row.jdSnippet,
        row.cvFilename,
        row.cvDriveUrl,
        row.score,
        row.grade,
        row.recommendation,
        row.confidence,
        row.summary,
      ]],
    },
  });
}
