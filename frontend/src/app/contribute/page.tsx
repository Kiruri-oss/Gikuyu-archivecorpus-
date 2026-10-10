"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Recorder } from "@/components/Recorder";
import { api } from "@/lib/api";
import type { Media } from "@/types";

export default function ContributePage() {
  const router = useRouter();
  const [blob, setBlob] = useState<Blob | null>(null);
  const [duration, setDuration] = useState(0);
  const [title, setTitle] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [dialect, setDialect] = useState("");
  const [genre, setGenre] = useState("");
  const [status, setStatus] = useState<"idle" | "uploading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!blob || !title.trim()) return;
    setStatus("uploading");
    setError(null);
    try {
      const file = new File([blob], `${Date.now()}.webm`, { type: "audio/webm" });
      await api.upload<Media>("/api/v1/media", file, {
        title: title.trim(),
        speaker: speaker.trim() || null,
        dialect: dialect.trim() || null,
        genre: genre.trim() || null,
        license: "CC-BY-4.0",
        notes: `duration=${duration.toFixed(1)}s`,
      });
      setStatus("done");
      router.push("/search");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  return (
    <div className="max-w-xl mx-auto py-8 space-y-6">
      <h1 className="text-2xl font-bold">Contribute a recording</h1>
      <Recorder onRecordingComplete={(b, d) => { setBlob(b); setDuration(d); }} />

      {blob && (
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Title (e.g. Ngano ya Njũkĩ)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            aria-label="Recording title"
            className="w-full p-3 border rounded-lg"
          />
          <input
            type="text"
            placeholder="Speaker name"
            value={speaker}
            onChange={(e) => setSpeaker(e.target.value)}
            aria-label="Speaker name"
            className="w-full p-3 border rounded-lg"
          />
          <input
            type="text"
            placeholder="Dialect (e.g. Ki-Muranga)"
            value={dialect}
            onChange={(e) => setDialect(e.target.value)}
            aria-label="Dialect"
            className="w-full p-3 border rounded-lg"
          />
          <input
            type="text"
            placeholder="Genre (ngano, thimo, nyĩmbo)"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            aria-label="Genre"
            className="w-full p-3 border rounded-lg"
          />
          <button
            type="button"
            onClick={handleUpload}
            disabled={status === "uploading" || !title.trim()}
            className="w-full py-3 bg-earth-500 text-white rounded-lg disabled:opacity-50"
          >
            {status === "uploading" ? "Uploading..." : "Submit recording"}
          </button>
          {error && <p role="alert" className="text-red-600">{error}</p>}
        </div>
      )}
    </div>
  );
}