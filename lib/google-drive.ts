// lib/google-drive.ts  — server-side only
import { google } from "googleapis";
import { Readable } from "stream";

function getAuth() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!raw) throw new Error("GOOGLE_SERVICE_ACCOUNT_KEY is not set");
  return new google.auth.GoogleAuth({
    credentials: JSON.parse(raw),
    scopes: ["https://www.googleapis.com/auth/drive"],
  });
}

function folderId() {
  const id = process.env.GOOGLE_DRIVE_FOLDER_ID;
  if (!id) throw new Error("GOOGLE_DRIVE_FOLDER_ID is not set");
  return id;
}

function mimeType(filename: string): string {
  const n = filename.toLowerCase();
  if (n.endsWith(".pdf"))  return "application/pdf";
  if (n.endsWith(".docx")) return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  return "text/plain";
}

export interface DriveUploadResult {
  id: string;
  webViewLink: string;
}

export async function uploadCVToDrive(
  buffer: Buffer,
  originalFilename: string,
  uploaderEmail: string
): Promise<DriveUploadResult> {
  const drive = google.drive({ version: "v3", auth: getAuth() });

  const safeName = `${Date.now()}_${uploaderEmail.replace(/[^a-z0-9]/gi, "_")}_${originalFilename}`;

  const res = await drive.files.create({
    requestBody: {
      name: safeName,
      parents: [folderId()],
      description: `Uploaded by ${uploaderEmail}`,
    },
    media: {
      mimeType: mimeType(originalFilename),
      body: Readable.from(buffer),
    },
    fields: "id,webViewLink",
  });

  return {
    id: res.data.id ?? "",
    webViewLink: res.data.webViewLink ?? "",
  };
}
