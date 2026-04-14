// lib/cloudinary.ts — server-side only
import { v2 as cloudinary } from "cloudinary";

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key:    process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

export interface CloudinaryUploadResult {
  public_id: string;
  secure_url: string;
}

export async function uploadCVToCloudinary(
  buffer: Buffer,
  originalFilename: string,
  uploaderEmail: string
): Promise<CloudinaryUploadResult> {
  return new Promise((resolve, reject) => {
    const uploadStream = cloudinary.uploader.upload_stream(
      {
        folder: "cv-scoring",
        resource_type: "auto",
        public_id: `${Date.now()}_${uploaderEmail.replace(/[^a-z0-9]/gi, "_")}`,
        display_name: originalFilename,
      },
      (error, result) => {
        if (error) return reject(error);
        if (!result) return reject(new Error("Upload failed: No result from Cloudinary"));
        resolve({
          public_id: result.public_id,
          secure_url: result.secure_url,
        });
      }
    );

    uploadStream.end(buffer);
  });
}
