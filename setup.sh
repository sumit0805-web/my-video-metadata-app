#!/bin/bash

mkdir -p videometa-frontend/app/components
mkdir -p videometa-frontend/app/hooks

cd videometa-frontend

# ── package.json ──────────────────────────────────────────────────────────────
cat > package.json << 'EOF'
{
  "name": "videometa-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@ffmpeg/ffmpeg": "^0.12.10",
    "@ffmpeg/util": "^0.12.1",
    "next": "14.2.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/node": "^20.12.7",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5"
  }
}
EOF

# ── next.config.js ────────────────────────────────────────────────────────────
cat > next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
          { key: "Cross-Origin-Embedder-Policy", value: "require-corp" },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
EOF

# ── tailwind.config.ts ────────────────────────────────────────────────────────
cat > tailwind.config.ts << 'EOF'
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#8b5cf6",
        surface: "#1a1a1a",
        bg: "#0f0f0f",
      },
    },
  },
  plugins: [],
};

export default config;
EOF

# ── postcss.config.js ─────────────────────────────────────────────────────────
cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF

# ── tsconfig.json ─────────────────────────────────────────────────────────────
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

# ── vercel.json ───────────────────────────────────────────────────────────────
cat > vercel.json << 'EOF'
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cross-Origin-Opener-Policy",  "value": "same-origin"  },
        { "key": "Cross-Origin-Embedder-Policy", "value": "require-corp" }
      ]
    }
  ]
}
EOF

# ── .env.local ────────────────────────────────────────────────────────────────
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=https://maxsteel0-video-metadata-generator.hf.space
EOF

# ── app/globals.css ───────────────────────────────────────────────────────────
cat > app/globals.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body {
  background-color: #0f0f0f;
  color: #e5e7eb;
  min-height: 100vh;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f0f0f; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #5a5a5a; }
* { scrollbar-width: thin; scrollbar-color: #3a3a3a #0f0f0f; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fadeInUp 0.5s ease forwards; }

@keyframes stepPulse {
  0%, 100% { opacity: 0.6; }
  50%       { opacity: 1; }
}
.step-pulse { animation: stepPulse 1.5s ease-in-out infinite; }

.toggle-track {
  width: 44px; height: 24px;
  background: #3a3a3a;
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}
.toggle-track.on { background: #8b5cf6; }
.toggle-thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 18px; height: 18px;
  background: #e5e7eb;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-track.on .toggle-thumb { transform: translateX(20px); }
EOF

# ── app/layout.tsx ────────────────────────────────────────────────────────────
cat > app/layout.tsx << 'EOF'
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
EOF

# ── app/components/CopyButton.tsx ─────────────────────────────────────────────
cat > app/components/CopyButton.tsx << 'EOF'
"use client";
import { useState } from "react";

interface Props {
  text: string;
  label?: string;
  className?: string;
}

export default function CopyButton({ text, label = "Copy", className = "" }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
        ${copied
          ? "bg-green-500/20 text-green-400 border border-green-500/30"
          : "bg-[#2a2a2a] text-gray-400 border border-gray-700 hover:bg-[#333] hover:text-gray-200"
        } ${className}`}
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}
EOF

# ── app/hooks/useVideoCompression.ts ─────────────────────────────────────────
cat > app/hooks/useVideoCompression.ts << 'EOF'
"use client";
import { useRef } from "react";

export function useVideoCompression() {
  const ffmpegRef = useRef<any>(null);

  const compress = async (
    file: File,
    onProgress: (pct: number) => void
  ): Promise<File> => {
    console.log("[FFmpeg] Compressing:", file.name, `${(file.size / 1024 / 1024).toFixed(1)} MB`);

    try {
      const { FFmpeg } = await import("@ffmpeg/ffmpeg");
      const { fetchFile, toBlobURL } = await import("@ffmpeg/util");

      if (!ffmpegRef.current) {
        ffmpegRef.current = new FFmpeg();

        ffmpegRef.current.on("progress", ({ progress }: { progress: number }) => {
          onProgress(Math.round(Math.min(progress * 100, 100)));
        });

        const base = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd";
        await ffmpegRef.current.load({
          coreURL: await toBlobURL(`${base}/ffmpeg-core.js`, "text/javascript"),
          wasmURL: await toBlobURL(`${base}/ffmpeg-core.wasm`, "application/wasm"),
        });

        console.log("[FFmpeg] Core loaded");
      }

      const ff = ffmpegRef.current;

      await ff.writeFile("input_video", await fetchFile(file));
      await ff.exec([
        "-i", "input_video",
        "-vcodec", "libx264",
        "-crf", "28",
        "-preset", "fast",
        "-vf", "scale=-2:720",
        "-acodec", "aac",
        "output.mp4",
      ]);

      const data = await ff.readFile("output.mp4");
      const blob = new Blob([data], { type: "video/mp4" });
      const baseName = file.name.replace(/\.[^.]+$/, "");
      const compressed = new File([blob], `${baseName}_compressed.mp4`, { type: "video/mp4" });

      console.log(`[FFmpeg] Done. ${(file.size / 1024 / 1024).toFixed(1)} MB → ${(compressed.size / 1024 / 1024).toFixed(1)} MB`);

      try { await ff.deleteFile("input_video"); await ff.deleteFile("output.mp4"); } catch {}

      onProgress(100);
      return compressed;

    } catch (err) {
      console.warn("[FFmpeg] Failed, using original file:", err);
      onProgress(0);
      return file;
    }
  };

  return { compress };
}
EOF

# ── app/page.tsx ──────────────────────────────────────────────────────────────
cat > app/page.tsx << 'EOF'
"use client";

import { useState, useEffect, useRef, useCallback, DragEvent, ChangeEvent } from "react";
import CopyButton from "./components/CopyButton";
import { useVideoCompression } from "./hooks/useVideoCompression";

interface MetadataResult {
  titles: string[];
  description: string;
  tags: string[];
  hashtags: string[];
}

type ServerStatus = "checking" | "ok" | "slow" | "down";
type ActiveTab = "file" | "youtube";
type Tone = "Viral" | "Educational" | "Funny" | "Dramatic";
type Platform = "YouTube Shorts" | "TikTok" | "Instagram Reels";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://maxsteel0-video-metadata-generator.hf.space";

const TONES: { label: Tone; emoji: string }[] = [
  { label: "Viral", emoji: "🔥" },
  { label: "Educational", emoji: "📚" },
  { label: "Funny", emoji: "😂" },
  { label: "Dramatic", emoji: "🎬" },
];

const PLATFORMS: { label: Platform; emoji: string }[] = [
  { label: "YouTube Shorts", emoji: "▶" },
  { label: "TikTok", emoji: "🎵" },
  { label: "Instagram Reels", emoji: "📸" },
];

const STEPS = [
  "🎵 Extracting audio and frames...",
  "👁 Analyzing visual content...",
  "✨ Generating metadata with AI...",
];

export default function Home() {
  const [serverStatus, setServerStatus] = useState<ServerStatus>("checking");
  const [activeTab, setActiveTab] = useState<ActiveTab>("file");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [compressionEnabled, setCompressionEnabled] = useState(true);
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionPct, setCompressionPct] = useState(0);
  const { compress } = useVideoCompression();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [youtubeUrlError, setYoutubeUrlError] = useState(false);
  const [tone, setTone] = useState<Tone>("Viral");
  const [platform, setPlatform] = useState<Platform>("YouTube Shorts");
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<MetadataResult | null>(null);
  const topRef = useRef<HTMLDivElement>(null);

  // Cold-start health check
  useEffect(() => {
    let slowTimer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    slowTimer = setTimeout(() => setServerStatus("slow"), 3000);

    fetch(`${API_BASE}/health`, { signal: controller.signal })
      .then((r) => r.json())
      .then(() => { clearTimeout(slowTimer); setServerStatus("ok"); })
      .catch(() => { clearTimeout(slowTimer); if (!controller.signal.aborted) setServerStatus("down"); });

    const hardTimeout = setTimeout(() => {
      controller.abort();
      setServerStatus((prev) => (prev === "slow" ? "down" : prev));
    }, 10000);

    return () => { clearTimeout(slowTimer); clearTimeout(hardTimeout); controller.abort(); };
  }, []);

  // Step cycling
  useEffect(() => {
    if (isLoading) {
      setCurrentStep(0);
      const timers = [
        setTimeout(() => setCurrentStep(1), 6000),
        setTimeout(() => setCurrentStep(2), 12000),
      ];
      return () => timers.forEach(clearTimeout);
    }
  }, [isLoading]);

  const handleFileDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) setVideoFile(file);
  }, []);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setVideoFile(file);
  };

  const validateYouTube = (url: string) =>
    url.includes("youtube.com") || url.includes("youtu.be");

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const handleSubmit = async () => {
    setApiError(null);
    setResult(null);
    setIsLoading(true);

    try {
      let fileToUpload = videoFile;

      if (activeTab === "file" && fileToUpload && compressionEnabled && fileToUpload.size > 50 * 1024 * 1024) {
        setIsCompressing(true);
        setCompressionPct(0);
        fileToUpload = await compress(fileToUpload, (pct) => setCompressionPct(pct));
        setIsCompressing(false);
      }

      let response: Response;

      if (activeTab === "youtube") {
        if (!validateYouTube(youtubeUrl)) { setYoutubeUrlError(true); setIsLoading(false); return; }
        response = await fetch(`${API_BASE}/process-video?youtube_url=${encodeURIComponent(youtubeUrl)}`, { method: "POST" });
      } else {
        if (!fileToUpload) { setApiError("Please select a video file."); setIsLoading(false); return; }
        const formData = new FormData();
        formData.append("file", fileToUpload);
        response = await fetch(`${API_BASE}/process-video`, { method: "POST", body: formData });
      }

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error ${response.status}: ${text}`);
      }

      const data: MetadataResult = await response.json();
      setResult(data);
    } catch (err: any) {
      setApiError(err.message ?? "Unknown error. Please try again.");
    } finally {
      setIsLoading(false);
      setIsCompressing(false);
    }
  };

  const buildCopyAll = () => {
    if (!result) return "";
    return [
      "=== TITLES ===",
      result.titles.map((t, i) => `${i + 1}. ${t}`).join("\n"),
      "",
      "=== DESCRIPTION ===",
      result.description,
      "",
      "=== TAGS ===",
      result.tags.join(", "),
      "",
      "=== HASHTAGS ===",
      result.hashtags.join(" "),
    ].join("\n");
  };

  const handleReset = () => {
    setResult(null);
    setVideoFile(null);
    setYoutubeUrl("");
    setApiError(null);
    setCompressionPct(0);
    topRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const canSubmit = !isLoading && (activeTab === "file" ? !!videoFile : youtubeUrl.trim().length > 0);

  return (
    <main className="min-h-screen bg-[#0f0f0f] pb-16" ref={topRef}>
      <div className="max-w-3xl mx-auto px-4 pt-10">

        {serverStatus === "slow" && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-300">
            <span className="flex-1">🔄 Server is waking up from sleep — this may take 30–60 seconds on first load.</span>
            <button onClick={() => setServerStatus("ok")} className="text-yellow-400 hover:text-yellow-200 text-lg leading-none">×</button>
          </div>
        )}
        {serverStatus === "down" && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            <span className="flex-1">❌ Server unavailable. Please try again in a minute.</span>
            <button onClick={() => setServerStatus("ok")} className="text-red-400 hover:text-red-200 text-lg leading-none">×</button>
          </div>
        )}

        {/* Hero */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3 bg-gradient-to-r from-[#8b5cf6] to-[#3b82f6] bg-clip-text text-transparent">
            VideoMeta AI
          </h1>
          <p className="text-gray-400 text-lg mb-5">Drop a video. Get viral metadata in seconds.</p>
          <div className="flex flex-wrap justify-center gap-2 text-xs">
            {["⚡ Whisper", "👁 CLIP + YOLO", "✨ Gemini AI"].map((badge) => (
              <span key={badge} className="px-3 py-1 rounded-full bg-[#1a1a1a] border border-gray-700 text-gray-400">{badge}</span>
            ))}
          </div>
        </div>

        {/* Upload */}
        <div className="bg-[#1a1a1a] rounded-2xl p-6 mb-4 border border-gray-800">
          <div className="flex gap-1 mb-6 border-b border-gray-800">
            {(["file", "youtube"] as ActiveTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium transition-colors relative pb-3
                  ${activeTab === tab ? "text-purple-400" : "text-gray-500 hover:text-gray-300"}`}
              >
                {tab === "file" ? "📁 Upload File" : "🔗 YouTube URL"}
                {activeTab === tab && <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500 rounded-t-sm" />}
              </button>
            ))}
          </div>

          {activeTab === "file" ? (
            <>
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
                  ${isDragging ? "border-purple-500 bg-purple-500/5" : videoFile ? "border-purple-500/50 bg-purple-500/5" : "border-gray-700 hover:border-purple-500/60 bg-[#111]"}`}
              >
                <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
                {videoFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="text-3xl">🎬</div>
                    <p className="font-medium text-gray-200 text-sm truncate max-w-xs">{videoFile.name}</p>
                    <p className="text-xs text-gray-500">{formatBytes(videoFile.size)}</p>
                    <button
                      onClick={(e) => { e.stopPropagation(); setVideoFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
                      className="mt-1 text-xs text-red-400 hover:text-red-300 border border-red-500/30 px-3 py-1 rounded-full"
                    >× Remove</button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <svg className="w-10 h-10 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 16v-8m0 0l-3 3m3-3l3 3M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
                    </svg>
                    <p className="text-gray-400 text-sm">Drag & drop a video, or <span className="text-purple-400">browse</span></p>
                    <p className="text-xs text-gray-600">MP4, MOV, AVI, WebM · up to 500 MB</p>
                  </div>
                )}
              </div>

              <div className="mt-4 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">⚡ Auto-compress videos over 50MB</span>
                  <div
                    role="switch"
                    aria-checked={compressionEnabled}
                    onClick={() => setCompressionEnabled((v) => !v)}
                    className={`toggle-track ${compressionEnabled ? "on" : ""}`}
                  >
                    <div className="toggle-thumb" />
                  </div>
                </div>
                {compressionEnabled && videoFile && videoFile.size > 50 * 1024 * 1024 && (
                  <p className="text-xs text-purple-400">This video will be compressed before upload</p>
                )}
              </div>

              {isCompressing && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Compressing video...</span>
                    <span>{compressionPct}%</span>
                  </div>
                  <div className="h-2 bg-[#2a2a2a] rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full transition-all duration-300" style={{ width: `${compressionPct}%` }} />
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="relative">
                <input
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => { setYoutubeUrl(e.target.value); setYoutubeUrlError(false); }}
                  onBlur={() => { if (youtubeUrl && !validateYouTube(youtubeUrl)) setYoutubeUrlError(true); }}
                  placeholder="https://youtube.com/shorts/..."
                  className={`w-full bg-[#111] border rounded-xl px-4 py-3 pr-10 text-sm text-gray-200 placeholder-gray-600 outline-none transition-colors
                    ${youtubeUrlError ? "border-red-500" : "border-gray-700 focus:border-purple-500"}`}
                />
                {youtubeUrl && (
                  <button onClick={() => { setYoutubeUrl(""); setYoutubeUrlError(false); }} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 text-lg">×</button>
                )}
              </div>
              {youtubeUrlError && <p className="mt-1.5 text-xs text-red-400">Invalid YouTube URL</p>}
            </>
          )}
        </div>

        {/* Tone + Platform */}
        <div className="bg-[#1a1a1a] rounded-2xl p-6 mb-4 border border-gray-800 flex flex-col gap-5">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Content Tone</p>
            <div className="flex flex-wrap gap-2">
              {TONES.map(({ label, emoji }) => (
                <button key={label} onClick={() => setTone(label)}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-all
                    ${tone === label ? "bg-purple-600 text-white border-purple-600" : "bg-[#1a1a1a] text-gray-400 border-gray-700 hover:border-gray-500"}`}>
                  {emoji} {label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Target Platform</p>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map(({ label, emoji }) => (
                <button key={label} onClick={() => setPlatform(label)}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-all
                    ${platform === label ? "bg-purple-600 text-white border-purple-600" : "bg-[#1a1a1a] text-gray-400 border-gray-700 hover:border-gray-500"}`}>
                  {emoji} {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={`w-full py-4 rounded-xl font-semibold text-white text-base transition-all bg-gradient-to-r from-purple-600 to-blue-500
            ${!canSubmit ? "opacity-50 cursor-not-allowed" : "hover:opacity-90 active:scale-[0.99]"}`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
              Processing...
            </span>
          ) : "✨ Generate Metadata"}
        </button>

        {isLoading && (
          <div className="mt-4 space-y-2">
            {STEPS.map((step, i) => (
              <div key={step}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border-l-2 bg-[#1a1a1a] text-sm transition-opacity duration-500
                  ${i === currentStep ? "border-purple-500 text-gray-200 step-pulse" : i < currentStep ? "border-green-600 text-gray-500 opacity-60" : "border-gray-700 text-gray-600 opacity-30"}`}>
                {step}
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {apiError && (
          <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            <span className="flex-1">❌ {apiError}</span>
            <button onClick={() => setApiError(null)} className="text-red-400 hover:text-red-200 text-lg leading-none">×</button>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 animate-fade-in-up">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

              <div className="bg-[#1a1a1a] rounded-2xl p-6 border border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-200">📝 Titles</h2>
                  <CopyButton text={result.titles.join("\n")} label="All" />
                </div>
                <ol className="space-y-2">
                  {result.titles.map((title, i) => (
                    <li key={i} className="flex items-start gap-2 group">
                      <span className="text-purple-500 font-bold text-sm mt-0.5 w-4 shrink-0">{i + 1}.</span>
                      <span className="text-gray-300 text-sm flex-1 select-text">{title}</span>
                      <CopyButton text={title} className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    </li>
                  ))}
                </ol>
              </div>

              <div className="bg-[#1a1a1a] rounded-2xl p-6 border border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-200">🏷️ Tags</h2>
                  <CopyButton text={result.tags.join(", ")} label="All Tags" />
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.tags.map((tag, i) => (
                    <span key={i} className="px-3 py-1 rounded-full bg-[#2a2a2a] text-gray-300 text-xs border border-gray-700">{tag}</span>
                  ))}
                </div>
              </div>

              <div className="bg-[#1a1a1a] rounded-2xl p-6 border border-gray-800 lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-200">📄 Description</h2>
                  <CopyButton text={result.description} />
                </div>
                <p className="text-gray-300 text-sm leading-relaxed select-text whitespace-pre-wrap">{result.description}</p>
              </div>

              <div className="bg-[#1a1a1a] rounded-2xl p-6 border border-gray-800 lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-200"># Hashtags</h2>
                  <CopyButton text={result.hashtags.join(" ")} label="All Hashtags" />
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.hashtags.map((tag, i) => (
                    <span key={i} className="px-3 py-1 rounded-full bg-purple-500/15 text-purple-300 text-xs border border-purple-500/30">{tag}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <CopyButton text={buildCopyAll()} label="📋 Copy Everything" className="flex-1 justify-center py-3 text-sm" />
              <button onClick={handleReset} className="flex-1 py-3 rounded-xl text-sm font-medium border border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200 transition-colors">
                🔄 Generate Again
              </button>
            </div>
          </div>
        )}

        <footer className="mt-16 text-center text-xs text-gray-700">
          Built with FastAPI · Gemini 1.5 Flash · CLIP · YOLOv8 · Whisper
        </footer>
      </div>
    </main>
  );
}
EOF

echo ""
echo "✅ All files created! Now run:"
echo ""
echo "   cd videometa-frontend"
echo "   npm install"
echo "   npm run dev"
echo ""
