import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "VideoMeta AI | Viral Metadata Generator",
  description:
    "Drop any video or YouTube URL and get AI-generated titles, descriptions, tags, and hashtags optimized for YouTube Shorts, TikTok, and Instagram Reels.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#0f0f0f] min-h-screen text-gray-200 antialiased`}>
        {children}
      </body>
    </html>
  );
}
