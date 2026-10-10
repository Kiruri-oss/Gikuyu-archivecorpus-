"use client";

import { use, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import type { Segment } from "@/types";

export default function TranscribePage({
  params,
}: {
  params: Promise<{ segmentId: string }>;
}) {
  const { segmentId } = use(params);
  const [mediaId, setMediaId] = useState("");
  const [transcript, setTranscript] = useState("");
  const [translation, setTranslation] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = new URLSearchParams(window.location.search).get("media");
    if (stored) setMediaId(stored);
  }, []);

  const handleSave = async () => {
    if (!mediaId) {
      setError("Missing media id in URL");
      return;
    }
    setStatus("saving");
    setError(null);
    try {
      await api.patch<Segment>(`/api/v1/segments/${segmentId}`, {
        transcript: transcript || null,
        translation: translation || null,
      });
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto py-8 space-y-4">
        <h1 className="text-2xl font-bold">Transcribe segment</h1>

        <label className="block">
          <span className="text-sm font-medium">Transcript (Kikuyu)</span>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            rows={4}
            className="w-full p-3 border rounded-lg mt-1"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium">Translation (English)</span>
          <textarea
            value={translation}
            onChange={(e) => setTranslation(e.target.value)}
            rows={4}
            className="w-full p-3 border rounded-lg mt-1"
          />
        </label>

        <button
          type="button"
          onClick={handleSave}
          disabled={status === "saving"}
          className="w-full py-3 bg-earth-500 text-white rounded-lg disabled:opacity-50"
        >
          {status === "saving" ? "Saving..." : "Save"}
        </button>

        {error && <p role="alert" className="text-red-600">{error}</p>}
        {status === "done" && <p className="text-green-600">Saved.</p>}
      </div>
    </ProtectedRoute>
  );
}