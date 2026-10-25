"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { getAccessToken } from "@/lib/auth";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

export default function ResearcherPage() {
  const [dialect, setDialect] = useState("");
  const [downloading, setDownloading] = useState<"jsonl" | "csv" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const download = async (format: "jsonl" | "csv") => {
    setDownloading(format);
    setError(null);
    try {
      const path = `/api/v1/exports/${format}${dialect ? `?dialect=${encodeURIComponent(dialect)}` : ""}`;
      const token = getAccessToken();
      const res = await fetch(`${API_URL}${path}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(payload?.detail ?? `Export unavailable (HTTP ${res.status}).`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `gikuyu-archive.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-xl mx-auto py-8 space-y-6">
        <h1 className="text-2xl font-bold">Researcher Exports</h1>
        <p className="text-gray-600 text-sm">
          Export datasets for ASR, TTS, MT, or LLM training. Licence metadata
          is preserved per row. Respect NC and Restricted licences.
        </p>
        <label className="block">
          <span className="text-sm font-medium">Dialect filter (optional)</span>
          <input type="text" value={dialect} onChange={(e) => setDialect(e.target.value)} placeholder="Ki-Muranga" className="w-full p-3 border rounded-lg mt-1" />
        </label>
        <div className="flex gap-3">
          <button type="button" onClick={() => download("jsonl")} disabled={downloading !== null} className="flex-1 py-3 bg-earth-500 text-white rounded-lg disabled:opacity-50">
            {downloading === "jsonl" ? "..." : "Download JSONL"}
          </button>
          <button type="button" onClick={() => download("csv")} disabled={downloading !== null} className="flex-1 py-3 border border-earth-500 text-earth-500 rounded-lg disabled:opacity-50">
            {downloading === "csv" ? "..." : "Download CSV"}
          </button>
        </div>
        {error && <p role="alert" className="text-red-600">{error}</p>}
      </div>
    </ProtectedRoute>
  );
}
