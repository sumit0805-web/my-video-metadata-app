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
