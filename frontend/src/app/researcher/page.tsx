"use client";

import Link from "next/link";
import { useState } from "react";

type ExportFormat = "csv" | "jsonl";
type ExportPurpose = "research" | "ai_training" | "commercial";

export default function ResearcherPage() {
  const [format, setFormat] = useState<ExportFormat>("csv");
  const [purpose, setPurpose] = useState<ExportPurpose>("research");
  const [license, setLicense] = useState("all_verified");
  const [dialect, setDialect] = useState("");
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  async function download() {
    setError("");
    setDownloading(true);
    try {
      const query = new URLSearchParams({ purpose, license_filter: license });
      if (dialect.trim()) query.set("dialect", dialect.trim());
      const base = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${base}/api/v1/exports/${format}?${query.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        cache: "no-store",
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? (response.status === 403
          ? "This account does not have researcher export permission."
          : "The archive export service is not available."));
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `gikuyu-corpus-${purpose}-${license}-${Date.now()}.${format}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Export failed. Try again.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Researcher workspace</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Export the Gĩkũyũ corpus</h1><p className="leading-7 text-gray-600">Download source-traceable archive records in CSV or JSONL. Each export is filtered by both your intended use and the stored permissions on each record. Records with unknown rights are excluded from reuse datasets.</p></header>
      {error && <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950">{error}<p className="mt-2"><Link href="/auth/login" className="font-semibold underline underline-offset-4">Sign in</Link> with a researcher account if needed.</p></div>}
      <section className="space-y-5 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="space-y-2"><label htmlFor="format" className="block text-sm font-semibold text-gray-800">File format</label><select id="format" value={format} onChange={(event) => setFormat(event.target.value as ExportFormat)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-gray-900"><option value="csv">CSV — spreadsheets and analysis</option><option value="jsonl">JSONL — corpus pipelines</option></select></div>
        <div className="space-y-2"><label htmlFor="purpose" className="block text-sm font-semibold text-gray-800">Intended use</label><select id="purpose" value={purpose} onChange={(event) => setPurpose(event.target.value as ExportPurpose)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-gray-900"><option value="research">Research</option><option value="ai_training">AI training</option><option value="commercial">Commercial use</option></select></div>
        <div className="space-y-2"><label htmlFor="license-filter" className="block text-sm font-semibold text-gray-800">Licence filter</label><select id="license-filter" value={license} onChange={(event) => setLicense(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-gray-900"><option value="all_verified">All records permitted for selected use</option><option value="cc0">CC0 only</option></select></div>
        <div className="space-y-2"><label htmlFor="dialect" className="block text-sm font-semibold text-gray-800">Dialect (optional)</label><input id="dialect" maxLength={100} value={dialect} onChange={(event) => setDialect(event.target.value)} placeholder="e.g. Ki-Murang'a" className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <button type="button" onClick={download} disabled={downloading} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white hover:bg-earth-800 disabled:opacity-50">{downloading ? "Preparing export…" : `Download corpus as ${format.toUpperCase()}`}</button>
      </section>
      <p className="text-sm leading-6 text-gray-500">WAV/audio files remain in archive storage and are not bundled into these text exports yet. Access requires a researcher account and is limited by each record&apos;s permissions. <Link href="/about" className="font-semibold text-earth-700 underline underline-offset-4">About the archive</Link>.</p>
    </div>
  );
}
