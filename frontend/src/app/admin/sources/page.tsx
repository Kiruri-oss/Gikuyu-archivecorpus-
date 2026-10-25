"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
type Source = {
  id: string;
  url: string;
  domain: string;
  source_type: string;
  status: string;
  license?: string | null;
  language_confidence?: number | null;
  created_at: string;
  reviewer_notes?: string | null;
};

export default function AdminSourcesPage() {
  const [items, setItems] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!API_URL) return;
    setLoading(true);
    setError("");
    try {
      const rows = await api.get<Source[]>("/api/v1/sources?status_filter=pending&limit=100");
      setItems(rows);
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 403
        ? "This page requires a reviewer or administrator account."
        : cause instanceof Error ? cause.message : "Pending sources could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function review(source: Source, status: "approved" | "rejected" | "taken_down") {
    setBusyId(source.id);
    setError("");
    setMessage("");
    try {
      await api.patch<Source>(`/api/v1/sources/${encodeURIComponent(source.id)}/review`, {
        status,
        reviewer_notes: notes[source.id]?.trim() || null,
      });
      setMessage(`Source ${status.replace("_", " ")}: ${source.domain}`);
      setItems((rows) => rows.filter((row) => row.id !== source.id));
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 422
        ? `The source could not be approved: ${cause.message}`
        : cause instanceof Error ? cause.message : "The source review action failed.");
    } finally {
      setBusyId("");
    }
  }

  return (
    <section className="mx-auto max-w-5xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Reviewer tools</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Hunter source review</h1><p className="leading-7 text-gray-600">Review source candidates collected by the Gĩkũyũ Hunter. Confirm the language, provenance and licence evidence before approving a record for public display or research exports.</p></header>
      {!API_URL && <p role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm leading-6 text-amber-950">The production archive API is not connected. Hunter candidates cannot be reviewed from the public deployment yet.</p>}
      {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      {message && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm leading-6 text-green-900">{message}</p>}
      <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-sm text-gray-500">{loading ? "Loading pending sources…" : `${items.length} pending source(s)`}</p><button type="button" onClick={() => void load()} disabled={!API_URL || loading} className="rounded-lg border border-earth-500 px-4 py-2 text-sm font-semibold text-earth-900 disabled:opacity-50">Refresh queue</button></div>
      {!loading && API_URL && items.length === 0 && !error && <p className="rounded-xl border border-dashed p-8 text-center text-gray-600">No pending sources are waiting for review.</p>}
      <div className="space-y-4">{items.map((source) => <article key={source.id} className="space-y-4 rounded-2xl border border-gray-200 p-5 sm:p-6"><div className="space-y-2"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-earth-50 px-3 py-1 text-xs font-semibold uppercase text-earth-800">{source.source_type}</span>{source.license && <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700">{source.license}</span>}</div><h2 className="break-all text-lg font-semibold text-earth-900">{source.domain}</h2><a href={source.url} target="_blank" rel="noopener noreferrer" className="break-all text-sm text-earth-700 underline underline-offset-4">{source.url} ↗</a><p className="text-xs text-gray-500">Discovered {new Date(source.created_at).toLocaleString()} · Language confidence {source.language_confidence == null ? "not recorded" : `${Math.round(source.language_confidence * 100)}%`}</p></div><div className="space-y-2"><label htmlFor={`review-notes-${source.id}`} className="block text-sm font-semibold">Review notes (optional)</label><textarea id={`review-notes-${source.id}`} rows={2} maxLength={5000} value={notes[source.id] ?? ""} onChange={(e) => setNotes((current) => ({ ...current, [source.id]: e.target.value }))} className="w-full rounded-lg border border-gray-300 p-3" placeholder="Language verification, licence evidence, corrections…" /></div><div className="flex flex-wrap gap-2"><button type="button" disabled={busyId === source.id} onClick={() => void review(source, "approved")} className="rounded-lg bg-earth-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Approve source</button><button type="button" disabled={busyId === source.id} onClick={() => void review(source, "rejected")} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-800 disabled:opacity-50">Reject</button><button type="button" disabled={busyId === source.id} onClick={() => void review(source, "taken_down")} className="rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold text-red-800 disabled:opacity-50">Take down</button></div></article>)}</div>
      <p className="text-sm text-gray-500">Only approved, publicly displayable records enter public search and curated exports. <Link href="/admin/takedowns" className="font-semibold text-earth-700 underline">Open takedown queue</Link>.</p>
    </section>
  );
}
