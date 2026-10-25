"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

const backendConfigured = Boolean(process.env.NEXT_PUBLIC_API_URL);

type TakedownResponse = {
  id: string;
  status: string;
  created_at: string;
};

export default function TakedownPage() {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<TakedownResponse | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setReceipt(null);
    if (!backendConfigured) {
      setError("The production archive API is not connected yet. Your request has not been sent or recorded.");
      return;
    }
    setBusy(true);
    try {
      const result = await api.post<TakedownResponse>("/api/v1/takedowns", {
        url: url.trim(),
        requester_name: name.trim(),
        requester_email: email.trim(),
        reason: reason.trim(),
      });
      setReceipt(result);
      setUrl("");
      setName("");
      setEmail("");
      setReason("");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The request could not be submitted. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="mx-auto max-w-3xl space-y-7 py-10 sm:py-14">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Rights and corrections</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Request review or removal</h1>
        <p className="leading-7 text-gray-600">Use this form to identify Gĩkũyũ material in the archive that you own or are authorised to represent, report a rights concern, or request correction. Include the exact source URL and enough detail for the archive team to locate the record.</p>
      </header>

      {!backendConfigured && <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><h2 className="font-semibold">Request intake is not connected on this deployment</h2><p className="mt-2 text-sm leading-6">The form is implemented, but the production backend is not configured. Do not treat a click here as a submitted request; nothing will be sent until the archive API is connected.</p></div>}

      {receipt && <div role="status" className="rounded-xl border border-green-300 bg-green-50 p-5 text-green-950"><h2 className="font-semibold">Request received by the archive API</h2><p className="mt-2 text-sm leading-6">Reference: <strong>{receipt.id}</strong></p><p className="text-sm leading-6">Status: {receipt.status}. Keep the reference for follow-up. Submission records a request; it does not itself confirm that a decision or removal has occurred.</p></div>}

      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-gray-200 p-5 sm:p-7">
        <div className="space-y-2"><label htmlFor="source-url" className="block text-sm font-semibold text-gray-800">Exact source or archive URL</label><input id="source-url" type="url" required maxLength={2000} value={url} onChange={(e) => setUrl(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder="https://…" /></div>
        <div className="grid gap-5 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="requester-name" className="block text-sm font-semibold text-gray-800">Your name</label><input id="requester-name" required minLength={2} maxLength={200} value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" /></div><div className="space-y-2"><label htmlFor="requester-email" className="block text-sm font-semibold text-gray-800">Contact email</label><input id="requester-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" /></div></div>
        <div className="space-y-2"><label htmlFor="reason" className="block text-sm font-semibold text-gray-800">Reason and details</label><textarea id="reason" required minLength={10} maxLength={5000} rows={6} value={reason} onChange={(e) => setReason(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3 leading-7" placeholder="Describe the material, your relationship to it, and the correction or action you are requesting." /></div>
        {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm leading-6 text-red-900">{error}</p>}
        <button type="submit" disabled={busy || !backendConfigured} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{busy ? "Submitting…" : "Submit review request"}</button>
      </form>

      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">What happens next?</h2><p className="leading-7 text-gray-700">When the API is connected, requests are recorded in the archive&apos;s review queue. The team can locate the source and record, review the evidence, and record the action taken. Do not send passwords, identity documents or unrelated sensitive information.</p><p className="leading-7 text-gray-700">For material hosted by another publisher, you may also need to contact that publisher directly. A request to this archive cannot remove material from a third-party website.</p></section>
      <Link href="/about" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Read about the current archive scope</Link>
    </article>
  );
}
