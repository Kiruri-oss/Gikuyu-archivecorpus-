"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";

type ContributionKind = "text" | "audio";
type Receipt = { id?: string; review_status?: string; message?: string; detail?: string };

export default function ContributePage() {
  const [kind, setKind] = useState<ContributionKind>("text");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [author, setAuthor] = useState("");
  const [year, setYear] = useState("");
  const [dialect, setDialect] = useState("");
  const [genre, setGenre] = useState("proverb");
  const [speaker, setSpeaker] = useState("");
  const [license, setLicense] = useState("CC BY 4.0");
  const [file, setFile] = useState<File | null>(null);
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [archiveConsent, setArchiveConsent] = useState(false);
  const [speakerConsent, setSpeakerConsent] = useState(false);
  const [publicConsent, setPublicConsent] = useState(false);
  const [researchUse, setResearchUse] = useState(false);
  const [aiUse, setAiUse] = useState(false);
  const [commercialUse, setCommercialUse] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setReceipt(null);
    try {
      let result: Receipt;
      if (kind === "text") {
        result = await api.post<Receipt>("/api/v1/text-records", {
          title: title.trim(),
          body: text.trim(),
          language_code: "ki",
          author: author.trim() || null,
          year: year ? Number(year) : null,
          dialect: dialect.trim() || null,
          genre,
          license,
          consent_to_publish: publicConsent,
          allow_research_use: researchUse,
          allow_ai_training: aiUse,
          allow_commercial_use: commercialUse,
          consent_to_archive: archiveConsent,
          confirm_rights: rightsConfirmed,
        });
      } else {
        if (!file) throw new Error("Choose an audio file first.");
        result = await api.upload<Receipt>("/api/v1/media", file, {
          title: title.trim(),
          speaker: speaker.trim() || null,
          dialect: dialect.trim() || null,
          genre,
          license,
          consent_to_archive: archiveConsent,
          confirm_rights: rightsConfirmed,
          speaker_consent_confirmed: speakerConsent,
          consent_to_publish: publicConsent,
          allow_research_use: researchUse,
          allow_ai_training: aiUse,
          allow_commercial_use: commercialUse,
        });
      }
      setReceipt(result);
      setTitle("");
      setText("");
      setAuthor("");
      setYear("");
      setSpeaker("");
      setFile(null);
      setRightsConfirmed(false);
      setArchiveConsent(false);
      setSpeakerConsent(false);
      setPublicConsent(false);
      setResearchUse(false);
      setAiUse(false);
      setCommercialUse(false);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : cause instanceof Error ? cause.message : "Contribution failed. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Community-built corpus</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Contribute Gĩkũyũ</h1><p className="leading-7 text-gray-600">Add a proverb, riddle, story, translation, original writing or audio recording to the growing Gĩkũyũ archive. Submissions go to the persistent backend when it is configured and require review before publication.</p></header>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Contribution type"><button type="button" onClick={() => setKind("text")} className={`rounded-lg px-4 py-2 font-semibold ${kind === "text" ? "bg-earth-900 text-white" : "border border-gray-300 text-gray-700"}`}>Text contribution</button><button type="button" onClick={() => setKind("audio")} className={`rounded-lg px-4 py-2 font-semibold ${kind === "audio" ? "bg-earth-900 text-white" : "border border-gray-300 text-gray-700"}`}>Audio recording</button></div>
      {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900"><p className="font-semibold">Contribution not confirmed</p><p className="mt-1">{error}</p><p className="mt-2"><Link href="/auth/login" className="font-semibold underline underline-offset-4">Sign in or create an account</Link> if you have not signed in.</p></div>}
      {receipt && <div role="status" className="rounded-xl border border-green-300 bg-green-50 p-5 text-green-950"><h2 className="font-semibold">Contribution received</h2><p className="mt-1 text-sm leading-6">{receipt.message ?? "The archive service recorded your contribution for review."}</p><p className="mt-1 text-sm">Status: {receipt.review_status ?? "pending review"}</p></div>}
      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="space-y-2"><label htmlFor="kind-title" className="block text-sm font-semibold text-gray-800">Title</label><input id="kind-title" required minLength={1} maxLength={500} value={title} onChange={(event) => setTitle(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        {kind === "text" ? <div className="space-y-2"><label htmlFor="contribution-text" className="block text-sm font-semibold text-gray-800">Gĩkũyũ text</label><textarea id="contribution-text" required minLength={1} maxLength={2000000} rows={8} value={text} onChange={(event) => setText(event.target.value)} placeholder="Enter the proverb, story, riddle, translation or original writing…" className="w-full rounded-xl border border-gray-300 p-3 leading-7 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /><p className="text-xs text-gray-500">{text.length.toLocaleString()} characters · ĩ and ũ are supported.</p></div> : <div className="space-y-2"><label htmlFor="audio-file" className="block text-sm font-semibold text-gray-800">Audio file</label><input id="audio-file" type="file" required accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="block w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-700 file:mr-3 file:rounded-lg file:border-0 file:bg-earth-50 file:px-3 file:py-2 file:font-semibold file:text-earth-900" /><p className="text-xs leading-5 text-gray-500">Upload limits depend on the configured archive API and storage service.</p><div className="space-y-2"><label htmlFor="speaker" className="block text-sm font-semibold text-gray-800">Speaker name or label (optional)</label><input id="speaker" maxLength={200} value={speaker} onChange={(event) => setSpeaker(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div></div>}
        {kind === "text" && <div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="author" className="block text-sm font-semibold text-gray-800">Author / source speaker (optional)</label><input id="author" maxLength={200} value={author} onChange={(event) => setAuthor(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div><div className="space-y-2"><label htmlFor="year" className="block text-sm font-semibold text-gray-800">Year (optional)</label><input id="year" type="number" min={1000} max={2100} value={year} onChange={(event) => setYear(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div></div>}
        <div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="dialect" className="block text-sm font-semibold text-gray-800">Gĩkũyũ dialect (optional)</label><input id="dialect" maxLength={100} value={dialect} onChange={(event) => setDialect(event.target.value)} placeholder="e.g. Ki-Murang'a" className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div><div className="space-y-2"><label htmlFor="genre" className="block text-sm font-semibold text-gray-800">Type</label><select id="genre" value={genre} onChange={(event) => setGenre(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-gray-900"><option value="proverb">Proverb</option><option value="riddle">Riddle</option><option value="folklore">Folklore / story</option><option value="conversation">Conversation</option><option value="translation">Translation</option><option value="original-writing">Original writing</option><option value="oral-history">Oral history</option><option value="literature">Literature</option><option value="other">Other</option></select></div></div>
        <div className="space-y-2"><label htmlFor="license" className="block text-sm font-semibold text-gray-800">Licence / permission basis</label><select id="license" value={license} onChange={(event) => setLicense(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-gray-900"><option value="CC BY 4.0">CC BY 4.0 — attribution</option><option value="CC0">CC0 — public domain dedication</option><option value="PUBLIC-DOMAIN">Public domain</option><option value="PERMISSION GRANTED">Permission granted (documented)</option><option value="ALL RIGHTS RESERVED">All rights reserved</option></select><p className="text-xs leading-5 text-gray-500">Do not select a licence you do not have authority to grant. The selected value is stored with the submission.</p></div>
        <div className="space-y-3 rounded-xl bg-earth-50 p-4">
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" required checked={rightsConfirmed} onChange={(event) => setRightsConfirmed(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>I have the right to submit this material and confirm that the information I provided is accurate.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" required checked={archiveConsent} onChange={(event) => setArchiveConsent(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>I consent to the archive storing this contribution for processing and review.</span></label>
          {kind === "audio" && <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" required checked={speakerConsent} onChange={(event) => setSpeakerConsent(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>I have permission from the speaker and I own this recording, or I have authority to submit it.</span></label>}
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" checked={publicConsent} onChange={(event) => setPublicConsent(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>I consent to public display after review.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" checked={researchUse} onChange={(event) => setResearchUse(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>Permit research use.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" checked={aiUse} onChange={(event) => setAiUse(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>Permit AI training use.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-800"><input type="checkbox" checked={commercialUse} onChange={(event) => setCommercialUse(event.target.checked)} className="mt-1 h-4 w-4 accent-earth-900" /><span>Permit commercial use.</span></label>
        </div>
        <button type="submit" disabled={submitting} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white hover:bg-earth-800 disabled:cursor-not-allowed disabled:opacity-50">{submitting ? "Submitting…" : "Submit contribution"}</button>
      </form>
      <p className="text-sm leading-6 text-gray-500">Need an account? <Link href="/auth/register" className="font-semibold text-earth-700 underline underline-offset-4">Register</Link>. Already registered? <Link href="/auth/login" className="font-semibold text-earth-700 underline underline-offset-4">Sign in</Link>.</p>
    </div>
  );
}
