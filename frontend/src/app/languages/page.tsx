import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gĩkũyũ Archive Corpus",
  description: "A growing Gĩkũyũ corpus of texts, oral history, recordings, transcripts, orthography and research datasets.",
};

const pillars = [
  ["Words and writing", "Vocabulary, proverbs, riddles, folklore, translations, original writing and eligible literature."],
  ["Voices and oral memory", "Recordings of stories and conversations, with speaker permission and provenance recorded."],
  ["Transcription and annotation", "Time-aligned transcripts, translations, dialect labels, reviewer corrections and Gĩkũyũ orthography including ĩ and ũ."],
  ["Research datasets", "Curated text and audio data with source provenance and purpose-specific reuse permissions."],
];

export default function LanguagesPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-10 py-8 sm:py-12">
      <header className="max-w-3xl space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">One language. A whole digital record.</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-5xl">The Gĩkũyũ Archive Corpus.</h1>
        <p className="text-lg leading-8 text-gray-600">A dedicated collection engine and digital library for Gĩkũyũ: discover material, preserve its source, build a reliable text and audio archive, and prepare carefully curated datasets for language research and AI.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2">
        {pillars.map(([title, description]) => <article key={title} className="rounded-2xl border border-gray-200 p-6"><h2 className="text-xl font-semibold text-earth-900">{title}</h2><p className="mt-3 leading-7 text-gray-600">{description}</p></article>)}
      </div>
      <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-earth-900">Current release status</h2>
        <p className="mt-3 leading-7 text-gray-700">This archive brings source discovery, persistent text and audio contributions, review workflows, Gĩkũyũ transcription and annotation, orthography tools, and purpose-filtered research exports into one language-focused workspace. Public records must pass review and carry provenance and permissions; member submissions remain private until approved. The amount of material currently published depends on what has actually been collected and approved, so empty collections are shown honestly rather than filled with sample records.</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/search" className="inline-flex rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Explore available material</Link>
          <Link href="/contribute" className="inline-flex rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Contribute text or audio</Link>
          <Link href="/orthography" className="inline-flex rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Check orthography</Link>
          <Link href="/transcribe" className="inline-flex rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Transcribe audio</Link>
          <Link href="/researcher" className="inline-flex rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Research datasets</Link>
          <Link href="/takedown" className="inline-flex rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Request correction or removal</Link>
        </div>
      </section>
      <p className="text-sm leading-6 text-gray-500">Gĩkũyũ is the only corpus language in this project. The objective is depth: more Gĩkũyũ source material, better records, richer transcription and annotation, and a useful corpus that can grow over time.</p>
    </div>
  );
}
