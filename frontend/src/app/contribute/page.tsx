"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

const backendConfigured = Boolean(process.env.NEXT_PUBLIC_API_URL);

type TextResponse = { id: string; review_status?: string; message?: string };
type AudioResponse = { id: string; review_status?: string; message?: string };

export default function ContributePage() {
  const [kind, setKind] = useState<"text" | "audio">("text");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState("");
  const [dialect, setDialect] = useState("");
  const [genre, setGenre] = useState("proverb");
  const [license, setLicense] = useState("CC-BY");
  const [file, setFile] = useState<File | null>(null);
  const [speaker, setSpeaker] = useState("");
  const [speakerConsent, setSpeakerConsent] = useState(false);
  const [languageConfirmed, setLanguageConfirmed] = useState(false);
  const [textLanguageConfirmed, setTextLanguageConfirmed] = useState(false);
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [archiveConsent, setArchiveConsent] = useState(false);
  const [publishConsent, setPublishConsent] = useState(false);
  const [researchConsent, setResearchConsent] = useState(false);
  const [aiConsent, setAiConsent] = useState(false);
  const [commercialConsent, setCommercialConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function resetMessages() {
    setError("");
    setSuccess("");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    resetMessages();
    if (!backendConfigured) {
      setError("The production archive API is not connected yet. Nothing has been submitted or stored.");
      return;
    }
    if (!archiveConsent || !rightsConfirmed) {
      setError("Confirm your right to contribute this material and consent to its storage for review.");
      return;
    }
    if (kind === "audio" && !file) {
      setError("Choose an audio recording first.");
      return;
    }
    if (kind === "audio" && file && file.size > 500 * 1024 * 1024) {
      setError("The recording must be 500 MB or smaller.");
      return;
    }

    setBusy(true);
    try {
      const meta = {
        title: title.trim(),
        dialect: dialect.trim() || null,
        genre,
        license,
        consent_to_archive: archiveConsent,
        confirm_rights: rightsConfirmed,
        speaker_consent_confirmed: kind === "audio" ? speakerConsent : false,
        language_confirmed: kind === "audio" ? languageConfirmed : textLanguageConfirmed,
        consent_to_publish: publishConsent,
        allow_research_use: researchConsent,
        allow_ai_training: aiConsent,
        allow_commercial_use: commercialConsent,
        notes: "Gĩkũyũ contribution submitted through the public archive form.",
      };
      if (kind === "text") {
        const result = await api.post<TextResponse>("/api/v1/text-records", {
          ...meta,
          body: body.trim(),
          author: author.trim() || null,
          language_code: "ki",
        });
        setSuccess(result.message ?? "Your text was received for review. It is not public until approved.");
        setTitle("");
        setBody("");
        setAuthor("");
      } else if (file) {
        const result = await api.upload<AudioResponse>("/api/v1/media", file, {
          ...meta,
          speaker: speaker.trim() || null,
          county: null,
        });
        setSuccess(result.message ?? "Your recording was received for review. It is not public until approved.");
        setTitle("");
        setSpeaker("");
        setFile(null);
      }
    } catch (cause) {
      const message = cause instanceof ApiError ? cause.message : cause instanceof Error ? cause.message : "The contribution could not be submitted.";
      setError(message.includes("401") || (cause instanceof ApiError && cause.status === 401)
        ? "Sign in before submitting a contribution."
        : message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Community archive</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Contribute to the Gĩkũyũ corpus</h1>
        <p className="leading-7 text-gray-600">Add a proverb, riddle, story, original text or recording. Submissions enter review first; they are not automatically published or included in AI-training datasets.</p>
      </header>

      {!backendConfigured && <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><h2 className="font-semibold">Production storage is not connected</h2><p className="mt-2 text-sm leading-6">The form is implemented, but this deployment has no configured archive API. Submitting is disabled so your material is not lost or falsely reported as saved. No contribution has been sent.</p></div>}

      <div className="flex flex-wrap gap-2" role="group" aria-label="Contribution type">
        <button type="button" onClick={() => { setKind("text"); resetMessages(); }} aria-pressed={kind === "text"} className={`rounded-lg px-4 py-2 font-semibold ${kind === "text" ? "bg-earth-900 text-white" : "border border-gray-300 text-gray-700"}`}>Text contribution</button>
        <button type="button" onClick={() => { setKind("audio"); resetMessages(); }} aria-pressed={kind === "audio"} className={`rounded-lg px-4 py-2 font-semibold ${kind === "audio" ? "bg-earth-900 text-white" : "border border-gray-300 text-gray-700"}`}>Audio recording</button>
      </div>

      <form onSubmit={submit} className="space-y-6 rounded-2xl border border-gray-200 bg-white p-5 sm:p-7">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <label htmlFor="contribution-title" className="block text-sm font-semibold text-gray-800">{kind === "text" ? "Title or short description" : "Recording title"}</label>
            <input id="contribution-title" required maxLength={500} value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder={kind === "text" ? "e.g. A proverb about home" : "e.g. A family story told in Gĩkũyũ"} />
          </div>
          {kind === "text" ? <>
            <div className="space-y-2 sm:col-span-2"><label htmlFor="text-body" className="block text-sm font-semibold text-gray-800">Gĩkũyũ text</label><textarea id="text-body" required minLength={1} maxLength={2000000} rows={9} value={body} onChange={(e) => setBody(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3 leading-7" placeholder="Write or paste the Gĩkũyũ text here…" /></div>
            <div className="space-y-2"><label htmlFor="author" className="block text-sm font-semibold text-gray-800">Author or source speaker (optional)</label><input id="author" maxLength={200} value={author} onChange={(e) => setAuthor(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" /></div>
          </> : <>
            <div className="space-y-2"><label htmlFor="speaker" className="block text-sm font-semibold text-gray-800">Speaker name or label (optional)</label><input id="speaker" maxLength={200} value={speaker} onChange={(e) => setSpeaker(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder="Use a label if anonymity is preferred" /></div>
            <div className="space-y-2 sm:col-span-2"><label htmlFor="audio-file" className="block text-sm font-semibold text-gray-800">Audio file</label><input id="audio-file" required type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="w-full rounded-lg border border-gray-300 p-3" /><p className="text-xs text-gray-500">Maximum 500 MB. Keep a backup of your original recording.</p></div>
          </>}
          <div className="space-y-2"><label htmlFor="dialect" className="block text-sm font-semibold text-gray-800">Dialect or locality (optional)</label><input id="dialect" maxLength={100} value={dialect} onChange={(e) => setDialect(e.target.value)} className="w-full rounded-lg border border-gray-300 p-3" placeholder="e.g. Ndia, Mathira, Murang'a" /></div>
          <div className="space-y-2"><label htmlFor="genre" className="block text-sm font-semibold text-gray-800">Material type</label><select id="genre" value={genre} onChange={(e) => setGenre(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white p-3"><option value="proverb">Proverb</option><option value="riddle">Riddle</option><option value="folklore">Folklore or story</option><option value="conversation">Conversation</option><option value="translation">Translation</option><option value="original-writing">Original writing</option><option value="oral-history">Oral history</option><option value="literature">Literature</option><option value="other">Other</option></select></div>
          <div className="space-y-2 sm:col-span-2"><label htmlFor="license" className="block text-sm font-semibold text-gray-800">Licence for this contribution</label><select id="license" value={license} onChange={(e) => setLicense(e.target.value)} className="w-full rounded-lg border border-gray-300 bg-white p-3"><option value="CC-BY">Creative Commons Attribution (CC BY)</option><option value="CC0">CC0 public-domain dedication</option><option value="PUBLIC-DOMAIN">Public domain</option><option value="PERMISSION-GRANTED">Permission granted — documented separately</option></select><p className="text-xs leading-5 text-gray-500">Choose only a licence you have the authority to grant. Permission to archive, publish, research, train AI and commercialise are separate choices below.</p></div>
        </div>

        <fieldset className="space-y-4 rounded-xl bg-gray-50 p-4">
          <legend className="px-1 font-semibold text-earth-900">Rights and consent</legend>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={rightsConfirmed} onChange={(e) => setRightsConfirmed(e.target.checked)} required className="mt-1" /><span>I have the right to contribute this material and have not knowingly included material I am not authorised to submit.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={archiveConsent} onChange={(e) => setArchiveConsent(e.target.checked)} required className="mt-1" /><span>I consent to the archive storing this contribution for review.</span></label>
          {kind === "text" && <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={textLanguageConfirmed} onChange={(e) => setTextLanguageConfirmed(e.target.checked)} required className="mt-1" /><span>I confirm this contribution is Gĩkũyũ (Kikuyu) language material.</span></label>}
          {kind === "audio" && <p className="rounded-lg border border-earth-500/20 bg-white p-3 text-sm leading-6 text-earth-900">For audio: submit only a recording you own or have permission to share, and confirm that the speaker(s) have consented to being recorded and to the intended use.</p>}
          {kind === "audio" && <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={languageConfirmed} onChange={(e) => setLanguageConfirmed(e.target.checked)} required className="mt-1" /><span>I confirm this recording contains Gĩkũyũ language material.</span></label>}
          {kind === "audio" && <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={speakerConsent} onChange={(e) => setSpeakerConsent(e.target.checked)} required className="mt-1" /><span>I have permission from the speaker(s), and I own this recording or have the right to submit it.</span></label>}
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={publishConsent} onChange={(e) => setPublishConsent(e.target.checked)} className="mt-1" /><span>I permit public display after review.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={researchConsent} onChange={(e) => setResearchConsent(e.target.checked)} className="mt-1" /><span>I permit research use, subject to the selected licence and archive review.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={aiConsent} onChange={(e) => setAiConsent(e.target.checked)} className="mt-1" /><span>I permit AI-training use, subject to the selected licence and archive review.</span></label>
          <label className="flex items-start gap-3 text-sm leading-6 text-gray-700"><input type="checkbox" checked={commercialConsent} onChange={(e) => setCommercialConsent(e.target.checked)} className="mt-1" /><span>I permit commercial reuse where the selected licence allows it.</span></label>
        </fieldset>

        {error && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm leading-6 text-red-900">{error}</p>}
        {success && <p role="status" className="rounded-lg border border-green-300 bg-green-50 p-3 text-sm leading-6 text-green-900">{success}</p>}
        {!backendConfigured && <p className="text-sm text-gray-500">You can still prepare your text locally, but do not close this page expecting it to be stored. The archive backend must be connected before submission is enabled.</p>}
        <div className="flex flex-wrap items-center gap-4"><button type="submit" disabled={!backendConfigured || busy} className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{busy ? "Submitting…" : "Submit for review"}</button><Link href="/login" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Sign in</Link><Link href="/register" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Create contributor account</Link></div>
      </form>
    </section>
  );
}
