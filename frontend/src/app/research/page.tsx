"use client";

import Link from "next/link";
import { useState } from "react";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
type Format = "csv" | "jsonl";
type Purpose = "research" | "ai_training" | "commercial";
type Licence = "cc0" | "all_verified";

export default function ResearchPage() {
  const [purpose, setPurpose] = useState<Purpose>("ai_training");
  const [licence, setLicence] = useState<Licence>("cc0");
  const [format, setFormat] = useState<Format>("jsonl");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function download() {
    setBusy(true);
    setError("");
    setMessage("");
    if (!API_URL) {
      setError("The production archive API is not connected. No dataset can be exported from this deployment yet.");
      setBusy(false);
      return;
    }
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Sign in with a researcher, reviewer or admin account to export curated data.");
      setBusy(false);
      return;
    }
    try {
      const params = new URLSearchParams({ purpose, license_filter: licence });
      const response = await fetch(`${API_URL}/api/v1/exports/${format}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(payload.detail ?? "The dataset could not be exported.");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `gikuyu-archive-${purpose}-${licence}.${format === "jsonl" ? "jsonl" : "csv"}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setMessage("The API returned the dataset. The file download should now be available on your device.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The dataset could not be exported.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Researcher portal</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Download curated Gĩkũyũ datasets</h1>
        <p className="leading-7 text-gray-600">Exports include approved records only and preserve source provenance. Select a use purpose and licence scope; the server filters records by the permissions stored with each contribution.</p>
      </header>
      {!API_URL && <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><h2 className="font-semibold">Research exports are not connected in production</h2><p className="mt-2 text-sm leading-6">The export endpoints are implemented in the backend, but the live website has no configured backend URL or persistent corpus. No export will be fabricated or simulated.</p></div>}
      <div className="space-y-6 rounded-2xl border border-gray-200 p-5 sm:p-7">
        <fieldset className="space-y-3"><legend className="font-semibold text-earth-900">Permitted use</legend>
          <label className="flex items-start gap-3 rounded-lg border p-3"><input type="radio" name="purpose" value="research" checked={purpose === "research"} onChange={() => setPurpose("research")} className="mt-1" /><span><strong className="block text-sm">Research</strong><span className="text-sm text-gray-600">Records whose stored permissions allow research use.</span></span></label>
          <label className="flex items-start gap-3 rounded-lg border p-3"><input type="radio" name="purpose" value="ai_training" checked={purpose === "ai_training"} onChange={() => setPurpose("ai_training")} className="mt-1" /><span><strong className="block text-sm">AI training</strong><span className="text-sm text-gray-600">Records explicitly marked as permitted for AI training.</span></span></label>
          <label className="flex items-start gap-3 rounded-lg border p-3"><input type="radio" name="purpose" value="commercial" checked={purpose === "commercial"} onChange={() => setPurpose("commercial")} className="mt-1" /><span><strong className="block text-sm">Commercial use</strong><span className="text-sm text-gray-600">Records whose stored permissions allow commercial reuse.</span></span></label>
        </fieldset>
        <fieldset className="space-y-3"><legend className="font-semibold text-earth-900">Licence filter</legend>
          <label className="flex items-start gap-3 rounded-lg border p-3"><input type="radio" name="licence" value="cc0" checked={licence === "cc0"} onChange={() => setLicence("cc0")} className="mt-1" /><span><strong className="block text-sm">CC0 only</strong><span className="text-sm text-gray-600">Only records whose licence field starts with CC0.</span></span></label>
          <label className="flex items-start gap-3 rounded-lg border p-3"><input type="radio" name="licence" value="all_verified" checked={licence === "all_verified"} onChange={() => setLicence("all_verified")} className="mt-1" /><span><strong className="block text-sm">All approved, permission-matched records</strong><span className="text-sm text-gray-600">Includes records approved for the selected purpose, regardless of the specific supported licence.</span></span></label>
        </fieldset>
        <div className="space-y-2"><label htmlFor="format" className="block text-sm font-semibold text-earth-900">File format</label><select id="format" value={format} onChange={(e) => setFormat(e.target.value as Format)} className="w-full rounded-lg border border-gray-300 bg-white p-3"><option value="jsonl">JSONL — one record per line</option><option value="csv">CSV — spreadsheet compatible</option></select></div>
        {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm leading-6 text-red-900">{error}</p>}
        {message && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-3 text-sm leading-6 text-green-900">{message}</p>}
        <div className="flex flex-wrap items-center gap-4"><button type="button" onClick={download} disabled={busy || !API_URL} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{busy ? "Preparing dataset…" : `Download corpus as ${format.toUpperCase()}`}</button><Link href="/login" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Researcher sign in</Link></div>
      </div>
      <p className="text-sm leading-6 text-gray-500">WAV package export is not implemented yet. Audio downloads need a secure archive bundle, permission checks per recording, and conversion/packaging verification; this portal currently offers CSV and JSONL only.</p>
    </section>
  );
}
