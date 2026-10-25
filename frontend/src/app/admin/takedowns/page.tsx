"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
type Takedown = {
  id: string;
  url: string;
  requester_name: string;
  requester_email: string;
  reason: string;
  status: string;
  created_at: string;
  actioned_at?: string | null;
};

export default function AdminTakedownsPage() {
  const [items, setItems] = useState<Takedown[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!API_URL) return;
    setLoading(true);
    setError("");
    try {
      setItems(await api.get<Takedown[]>("/api/v1/takedowns"));
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 403
        ? "This queue requires an administrator account."
        : cause instanceof Error ? cause.message : "Takedown requests could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function action(item: Takedown) {
    setBusyId(item.id);
    setError("");
    setMessage("");
    try {
      const updated = await api.post<Takedown>(`/api/v1/takedowns/${encodeURIComponent(item.id)}/action`);
      setItems((rows) => rows.map((row) => row.id === item.id ? updated : row));
      setMessage(`Request ${item.id} actioned. Matching archive records were removed from public search and associated stored media/text were deleted where applicable.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The removal action failed.");
    } finally {
      setBusyId("");
    }
  }


  async function reject(item: Takedown) {
    setBusyId(item.id);
    setError("");
    setMessage("");
    try {
      const updated = await api.post<Takedown>(`/api/v1/takedowns/${encodeURIComponent(item.id)}/reject`);
      setItems((rows) => rows.map((row) => row.id === item.id ? updated : row));
      setMessage("Request rejected after review. A source hidden only for this request was restored if no other open request remains.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The request could not be rejected.");
    } finally {
      setBusyId("");
    }
  }

  return (
    <section className="mx-auto max-w-5xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Administrator tools</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Takedown and removal queue</h1><p className="leading-7 text-gray-600">Review rights-holder requests. The submission endpoint temporarily hides matching approved source records; actioning a request removes matching indexed records and associated stored media/text.</p></header>
      {!API_URL && <p role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm leading-6 text-amber-950">The production archive API is not connected. Removal requests cannot be reviewed from the public deployment yet.</p>}
      {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      {message && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm leading-6 text-green-900">{message}</p>}
      <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-sm text-gray-500">{loading ? "Loading requests…" : `${items.length} request(s)`}</p><button type="button" onClick={() => void load()} disabled={!API_URL || loading} className="rounded-lg border border-earth-500 px-4 py-2 text-sm font-semibold text-earth-900 disabled:opacity-50">Refresh queue</button></div>
      {!loading && API_URL && items.length === 0 && !error && <p className="rounded-xl border border-dashed p-8 text-center text-gray-600">No removal requests have been submitted.</p>}
      <div className="space-y-4">{items.map((item) => <article key={item.id} className="space-y-4 rounded-2xl border border-gray-200 p-5 sm:p-6"><div className="flex flex-wrap items-center justify-between gap-3"><span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold uppercase text-gray-700">{item.status}</span><span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</span></div><h2 className="text-lg font-semibold text-earth-900">{item.requester_name}</h2><p className="text-sm text-gray-600">{item.requester_email}</p><a href={item.url} target="_blank" rel="noopener noreferrer" className="break-all text-sm text-earth-700 underline underline-offset-4">{item.url} ↗</a><div className="rounded-lg bg-gray-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Reason</p><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-gray-800">{item.reason}</p></div><div className="flex flex-wrap gap-2">{item.status !== "actioned" && item.status !== "rejected" && <><button type="button" disabled={busyId === item.id} onClick={() => void action(item)} className="rounded-lg bg-earth-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busyId === item.id ? "Processing…" : "Action request and remove archive copy"}</button><button type="button" disabled={busyId === item.id} onClick={() => void reject(item)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-800 disabled:opacity-50">Reject request and restore source if appropriate</button></>}</div></article>)}</div>
    </section>
  );
}
