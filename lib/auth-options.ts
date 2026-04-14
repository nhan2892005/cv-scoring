// lib/auth-options.ts
import GoogleProvider from "next-auth/providers/google";
import type { NextAuthOptions } from "next-auth";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  pages: {
    signIn: "/",
  },
  callbacks: {
    async session({ session }) {
      return session;
    },
  },
  events: {
    async signIn({ user }) {
      // Logic moves to server-side event for 100% reliability
      try {
        const { headers } = await import("next/headers");
        const { appendLoginTrace } = await import("./google-sheets");
        
        const headerList = headers();
        const ip = headerList.get("x-forwarded-for")?.split(",")[0] || "unknown";
        const ua = headerList.get("user-agent") || "unknown";

        await appendLoginTrace({
          email: user.email || "unknown",
          name: user.name || "",
          image: user.image || "",
          ip,
          userAgent: ua,
        });
      } catch (err) {
        console.error("[auth-event] signIn tracking error:", err);
      }
    },
  },
};
