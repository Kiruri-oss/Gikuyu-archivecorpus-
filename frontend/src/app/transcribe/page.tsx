"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Media, Segment } from "@/types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
type MediaDetail = Media & { file_url: string };
type SegmentEdit = { transcript: string; translation: string };

export default function TranscribePage() {
  const [media, setMedia] = useState<Media[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<MediaDetail | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [edits, setEdits] = useState<Record<string, SegmentEdit>>({});
  const [start, setStart] = useState("0");
  const [end, setEnd] = useState("5");
  const [transcript, setTranscript] = useState("");
  const [translation, setTranslation] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const audioItems = useMemo(() => media.filter((item) => item.kind === "audio"), [media]);

  useEffect(() => {
    if (!API_URL) return;
    let cancelled = false;
    setLoading(true);
    api.get<Media[]>("/api/v1/media?limit=100")
      .then((items) => {
        if (cancelled) return;
        const audio = items.filter((item) => item.kind === "audio");
        setMedia(audio);
        if (audio.length > 0) setSelectedId(audio[0].id);
      })
      .catch((cause) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Approved Gĩkũyũ recordings could not be loaded.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!API_URL || !selectedId) {
      setSelected(null);
      setSegments([]);
      return;
    }
    let cancelled = false;
    setError("");
    setNotice("");
    setSelected(null);
    Promise.all([
      api.get<MediaDetail>(`/api/v1/media/${encodeURIComponent(selectedId)}`),
      api.get<Segment[]>(`/api/v1/segments/media/${encodeURIComponent(selectedId)}`),
    ]).then(([detail, rows]) => {
      if (cancelled) return;
      setSelected(detail);
      setSegments(rows);
      setEdits(Object.fromEntries(rows.map((row) => [row.id, {
        transcript: row.transcript ?? "",
        translation: row.translation ?? "",
      }])));
    }).catch((cause) => {
      if (!cancelled) setError(cause instanceof Error ? cause.message : "Recording or transcript could not be loaded.");
    });
    return () => { cancelled = true; };
  }, [selectedId]);

  async function addSegment(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (!selected) return;
    const startValue = Number(start);
    const endValue = Number(end);
    if (!Number.isFinite(startValue) || !Number.isFinite(endValue) || startValue < 0 || endValue <= startValue) {
      setError("End time must be greater than start time, and both times must be valid seconds.");
      return;
    }
    if (!transcript.trim() && !translation.trim()) {
      setError("Enter a Gĩkũyũ transcript, a translation, or both.");
      return;
    }
    setBusy(true);
    try {
      const created = await api.post<Segment>("/api/v1/segments", {
        media_id: selected.id,
        start_seconds: startValue,
        end_seconds: endValue,
        transcript: transcript.trim() || null,
        translation: translation.trim() || null,
      });
      setSegments((rows) => [...rows, created].sort((a, b) => a.start_seconds - b.start_seconds));
      setEdits((rows) => ({ ...rows, [created.id]: { transcript: created.transcript ?? "", translation: created.translation ?? "" } }));
      setStart(String(endValue));
      setEnd(String(endValue + 5));
      setTranscript("");
      setTranslation("");
      setNotice("Transcript segment saved to the archive.");
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 401
        ? "Sign in before adding transcript segments."
        : cause instanceof Error ? cause.message : "The transcript segment could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  async function saveCorrection(segment: Segment) {
    const edit = edits[segment.id];
    if (!edit) return;
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const updated = await api.patch<Segment>(`/api/v1/segments/${encodeURIComponent(segment.id)}`, {
        transcript: edit.transcript,
        translation: edit.translation,
      });
      setSegments((rows) => rows.map((row) => row.id === updated.id ? updated : row));
      setNotice("Correction saved.");
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 403
        ? "Only the recording contributor or an archive reviewer can correct an existing segment. You can still add a new segment below."
        : cause instanceof Error ? cause.message : "The correction could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-4xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Transcription and annotation</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Build the Gĩkũyũ transcript corpus</h1>
        <p className="leading-7 text-gray-600">Listen to an approved recording, add time-aligned Gĩkũyũ text and translation, and improve existing segments where you have permission. Saved segments can later feed reviewed research datasets.</p>
      </header>
      {!API_URL && <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><h2 className="font-semibold">Transcription storage is not connected</h2><p className="mt-2 text-sm leading-6">The transcription interface is implemented, but this deployment has no configured archive API or persistent database. No transcript can be saved until the backend is connected.</p></div>}
      {API_URL && loading && <p role="status" className="text-sm text-gray-500">Loading approved Gĩkũyũ recordings…</p>}
      {API_URL && !loading && audioItems.length === 0 && <div className="rounded-xl border border-dashed p-6"><h2 className="font-semibold text-earth-900">No approved recordings are available yet</h2><p className="mt-2 text-sm leading-6 text-gray-600">Once Gĩkũyũ audio is contributed and approved, it will appear here for transcription.</p><Link href="/contribute" className="mt-4 inline-flex font-semibold text-earth-700 underline">Contribute a recording</Link></div>}

      {API_URL && audioItems.length > 0 && <>
        <div className="space-y-2"><label htmlFor="recording-select" className="block text-sm font-semibold text-gray-800">Choose a recording</label><select id="recording-select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white p-3">{audioItems.map((item) => <option key={item.id} value={item.id}>{item.title}{item.dialect ? ` — ${item.dialect}` : ""}</option>)}</select></div>
        {selected?.file_url && <div className="space-y-3 rounded-2xl border border-gray-200 p-5"><h2 className="font-semibold text-earth-900">{selected.title}</h2><audio controls preload="metadata" src={selected.file_url} className="w-full">Your browser does not support audio playback.</audio><p className="text-xs leading-5 text-gray-500">Use the audio player to identify the start and end time of each spoken segment. Do not publish sensitive or restricted material without permission.</p></div>}

        <section className="space-y-4"><h2 className="text-xl font-semibold text-earth-900">Existing transcript segments</h2>{segments.length === 0 ? <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-600">No transcript segments have been added to this recording yet.</p> : <div className="space-y-4">{segments.map((segment) => <article key={segment.id} className="space-y-3 rounded-xl border border-gray-200 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{segment.start_seconds.toFixed(2)}s – {segment.end_seconds.toFixed(2)}s {segment.is_verified ? "· Reviewed" : "· Unreviewed"}</p><div className="space-y-2"><label htmlFor={`transcript-${segment.id}`} className="block text-sm font-semibold">Gĩkũyũ transcript</label><textarea id={`transcript-${segment.id}`} rows={2} value={edits[segment.id]?.transcript ?? ""} onChange={(e) => setEdits((rows) => ({ ...rows, [segment.id]: { transcript: e.target.value, translation: rows[segment.id]?.translation ?? "" } }))} className="w-full rounded-lg border border-gray-300 p-3" /></div><div className="space-y-2"><label htmlFor={`translation-${segment.id}`} className="block text-sm font-semibold">Translation (optional)</label><textarea id={`translation-${segment.id}`} rows={2} value={edits[segment.id]?.translation ?? ""} onChange={(e) => setEdits((rows) => ({ ...rows, [segment.id]: { transcript: rows[segment.id]?.transcript ?? "", translation: e.target.value } }))} className="w-full rounded-lg border border-gray-300 p-3" /></div><button type="button" disabled={busy} onClick={() => saveCorrection(segment)} className="rounded-lg border border-earth-500 px-4 py-2 text-sm font-semibold text-earth-900 disabled:opacity-50">Save correction</button></article>)}</div>}</section>

        <form onSubmit={addSegment} className="space-y-5 rounded-2xl border border-gray-200 p-5 sm:p-7"><h2 className="text-xl font-semibold text-earth-900">Add a time-aligned segment</h2><div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="start-time" className="block text-sm font-semibold">Start time (seconds)</label><input id="start-time" type="number" min="0" step="0.01" required value={start} onChange={(e) => setStart(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" /></div><div className="space-y-2"><label htmlFor="end-time" className="block text-sm font-semibold">End time (seconds)</label><input id="end-time" type="number" min="0.01" step="0.01" required value={end} onChange={(e) => setEnd(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" /></div></div><div className="space-y-2"><label htmlFor="new-transcript" className="block text-sm font-semibold">Gĩkũyũ transcript</label><textarea id="new-transcript" rows={3} value={transcript} onChange={(e) => setTranscript(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder="Transcribe the spoken Gĩkũyũ as accurately as possible…" /></div><div className="space-y-2"><label htmlFor="new-translation" className="block text-sm font-semibold">Translation (optional)</label><textarea id="new-translation" rows={2} value={translation} onChange={(e) => setTranslation(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder="Add a translation if you can…" /></div><button type="submit" disabled={busy || !selected} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white disabled:opacity-50">{busy ? "Saving…" : "Save transcript segment"}</button></form>
      </>}

      {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      {notice && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm leading-6 text-green-900">{notice}</p>}
      <p className="text-sm leading-6 text-gray-500">Transcript records are not automatically marked verified. A reviewer should confirm spelling, timestamps and translation before a segment is treated as a verified training example.</p>
      <Link href="/login" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Sign in to contribute or correct a transcript</Link>
    </section>
  );
}
