"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type TakedownReceipt = {
  id?: string;
  status?: string;
  detail?: string;
};

export default function TakedownPage() {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<TakedownReceipt | null>(null);

  async function submitRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setReceipt(null);
    try {
      const response = await fetch("/api/v1/takedowns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          requester_name: name.trim(),
          requester_email: email.trim(),
          reason: reason.trim(),
        }),
      });
      const payload = await response.json().catch(() => ({})) as TakedownReceipt;
      if (!response.ok) {
        throw new Error(payload.detail ?? (response.status === 503
          ? "The takedown service is not connected to a persistent archive yet. Your request has not been submitted."
          : "The request could not be submitted. Check the details and try again."));
      }
      setReceipt(payload);
      setUrl("");
      setName("");
      setEmail("");
      setReason("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The request could not be submitted. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <article className="mx-auto max-w-3xl space-y-7 py-10 sm:py-14">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Archive accountability</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Request removal from Gĩkũyũ Archive Corpus</h1>
        <p className="leading-7 text-gray-600">If you own material held in the archive and believe it should be removed, submit the source URL and a short explanation. Requests should identify the affected material clearly so it can be located and reviewed.</p>
      </header>

      {receipt && (
        <div role="status" className="rounded-xl border border-green-300 bg-green-50 p-5 text-green-950">
          <h2 className="font-semibold">Request received by the archive service</h2>
          <p className="mt-2 text-sm leading-6">Reference: {receipt.id ?? "recorded"} · Status: {receipt.status ?? "received"}. Keep this reference for follow-up.</p>
        </div>
      )}
      {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-950"><p className="font-semibold">Request not confirmed</p><p className="mt-1 text-sm leading-6">{error}</p></div>}

      <form onSubmit={submitRequest} className="space-y-5 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="space-y-2">
          <label htmlFor="takedown-url" className="block text-sm font-semibold text-gray-800">URL of the archived material</label>
          <input id="takedown-url" type="url" required maxLength={2000} value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.org/page-or-recording" className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" />
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <label htmlFor="takedown-name" className="block text-sm font-semibold text-gray-800">Your name</label>
            <input id="takedown-name" autoComplete="name" required minLength={2} maxLength={200} value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" />
          </div>
          <div className="space-y-2">
            <label htmlFor="takedown-email" className="block text-sm font-semibold text-gray-800">Email for follow-up</label>
            <input id="takedown-email" type="email" autoComplete="email" required maxLength={255} value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" />
          </div>
        </div>
        <div className="space-y-2">
          <label htmlFor="takedown-reason" className="block text-sm font-semibold text-gray-800">Why are you requesting removal?</label>
          <textarea id="takedown-reason" required minLength={10} maxLength={5000} rows={5} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Identify the material and explain your concern or rights in it." className="w-full rounded-xl border border-gray-300 p-3 leading-6 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" />
          <p className="text-xs text-gray-500">{reason.length.toLocaleString()} / 5,000 characters</p>
        </div>
        <button type="submit" disabled={submitting} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white hover:bg-earth-800 disabled:cursor-not-allowed disabled:opacity-50">{submitting ? "Submitting…" : "Submit removal request"}</button>
        <p className="text-xs leading-5 text-gray-500">Your name and email are sent to the archive service only when you submit. Do not include identity documents or unnecessary sensitive information. The form will clearly report if the backend is unavailable; it will not claim a request was received when it was not.</p>
      </form>

      <section className="space-y-3 border-t pt-6">
        <h2 className="text-xl font-semibold text-earth-900">What happens next?</h2>
        <p className="leading-7 text-gray-700">A functioning backend records requests with a timestamp and allows an administrator to hide the source, remove stored text/audio records and purge search entries. The original publisher controls the copy on its own site; removing a record here does not remove that external copy.</p>
      </section>
      <Link href="/about" className="text-sm font-semibold text-earth-700 underline underline-offset-4">About the archive</Link>
    </article>
  );
}
