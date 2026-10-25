"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

type HunterStatus = {
  status: string;
  scheduled?: boolean;
  seed_count?: number;
  default_page_budget?: number;
  max_pages_per_run?: number;
  max_discovery_hosts?: number;
  max_pages_per_host?: number;
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  pages_discovered?: number;
  records_saved?: number;
  page_budget?: number;
  error?: string;
};

export default function AdminHunterPage() {
  const [status, setStatus] = useState<HunterStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await api.get<HunterStatus>("/api/v1/hunter/status"));
      setError("");
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 403
        ? "This control panel requires an administrator account."
        : cause instanceof Error ? cause.message : "Hunter status could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadStatus(); }, [loadStatus]);
  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => { void loadStatus(); }, 5000);
    return () => window.clearInterval(timer);
  }, [running, loadStatus]);

  useEffect(() => {
    if (status?.status === "completed" || status?.status === "failed") setRunning(false);
    if (status?.status === "running" || status?.status === "queued") setRunning(true);
  }, [status]);

  async function runNow() {
    setError("");
    setMessage("");
    setRunning(true);
    try {
      await api.post<{ status: string; page_budget: number }>("/api/v1/hunter/run?max_pages=1000");
      setMessage("Hunter run queued. This page will refresh status while the crawl runs.");
      await loadStatus();
    } catch (cause) {
      setRunning(false);
      setError(cause instanceof ApiError && cause.status === 409
        ? "A Hunter run is already in progress."
        : cause instanceof Error ? cause.message : "The Hunter could not be started.");
    }
  }

  return (
    <section className="mx-auto max-w-4xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Administrator tools</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Gĩkũyũ Hunter control</h1><p className="leading-7 text-gray-600">Run the bounded source hunter, inspect its latest result and send collected records to the source review queue. The Hunter is configured to discover Gĩkũyũ pages across relevant public sources, obey robots.txt, record provenance and keep unknown-rights material out of AI-training and commercial exports.</p></header>
      
      {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      {message && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-4 text-sm leading-6 text-green-900">{message}</p>}
      <div className="rounded-2xl border border-gray-200 p-5 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-sm text-gray-500">Latest run</p><h2 className="mt-1 text-2xl font-bold capitalize text-earth-900">{status?.status?.replaceAll("_", " ") ?? "Unknown"}</h2></div><button type="button" onClick={() => void runNow()} disabled={running} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{running ? "Hunter running…" : "Run Hunter now"}</button></div>
        {status?.error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-900">{status.error}</p>}
        <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[
          ["Scheduled", status?.scheduled ? "Active" : "Not running"],
          ["Discovery seeds", status?.seed_count ?? "—"],
          ["Page budget", status?.page_budget ?? status?.default_page_budget ?? "—"],
          ["Pages detected", status?.pages_discovered ?? "—"],
          ["Records saved", status?.records_saved ?? "—"],
          ["Host limits", status ? `${status.max_discovery_hosts ?? "—"} hosts · ${status.max_pages_per_host ?? "—"} pages/host` : "—"],
        ].map(([label, value]) => <div key={String(label)} className="rounded-lg bg-gray-50 p-4"><dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt><dd className="mt-2 font-semibold text-earth-900">{value}</dd></div>)}</dl>
        <div className="mt-5 space-y-1 text-sm text-gray-500">{status?.queued_at && <p>Queued: {new Date(status.queued_at).toLocaleString()}</p>}{status?.started_at && <p>Started: {new Date(status.started_at).toLocaleString()}</p>}{status?.completed_at && <p>Completed: {new Date(status.completed_at).toLocaleString()}</p>}{status?.failed_at && <p>Failed: {new Date(status.failed_at).toLocaleString()}</p>}</div>
        <button type="button" onClick={() => void loadStatus()} disabled={loading} className="mt-5 rounded-lg border border-earth-500 px-4 py-2 text-sm font-semibold text-earth-900 disabled:opacity-50">{loading ? "Refreshing…" : "Refresh status"}</button>
      </div>
      <div className="flex flex-wrap gap-4 text-sm"><Link href="/admin/sources" className="font-semibold text-earth-700 underline underline-offset-4">Review collected sources</Link><Link href="/admin/takedowns" className="font-semibold text-earth-700 underline underline-offset-4">Open takedown queue</Link></div>
      <p className="text-sm leading-6 text-gray-500">A crawl is capped at 500 pages by default, 30 pages per host and 40 discovered hosts per run. A one-second minimum delay is applied between requests to the same host. The scheduler also runs every six hours when the production backend is configured and running.</p>
    </section>
  );
}
