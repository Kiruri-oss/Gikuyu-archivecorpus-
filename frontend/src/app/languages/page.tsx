import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gĩkũyũ Archive Corpus",
  description: "The Gĩkũyũ language archive: texts, oral history, recordings, transcripts, orthography and research datasets.",
};

export default function LanguagesPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-10 py-8 sm:py-12">
      <header className="max-w-3xl space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">One language. A whole digital record.</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-5xl">A growing online home for Gĩkũyũ.</h1>
        <p className="text-lg leading-8 text-gray-600">The mission is to make Gĩkũyũ searchable, documentable and useful for its speakers and future language technology—not merely to wrap a search engine around somebody else’s websites.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2">
        {[
          ["Words and writing", "Vocabulary, proverbs, riddles, folklore, translations, original writing and eligible public-domain literature."],
          ["Voices and oral memory", "Consent-based recordings of stories, conversations and knowledge shared by Gĩkũyũ speakers."],
          ["Transcription and annotation", "Time-aligned transcripts, translations, dialect labels, reviewer corrections and standard orthography including ĩ and ũ."],
          ["A research corpus", "Provenance-rich, licence-filtered text and audio datasets for permitted language research and AI training."],
        ].map(([title, description]) => <article key={title} className="rounded-2xl border border-gray-200 p-6"><h2 className="text-xl font-semibold text-earth-900">{title}</h2><p className="mt-3 leading-7 text-gray-600">{description}</p></article>)}
      </div>
      <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-earth-900">Current release status</h2>
        <p className="mt-3 leading-7 text-gray-700">The deployed version currently discovers selected public reference pages and can save links locally in a visitor’s browser. Persistent corpus storage, the autonomous rights-aware hunter, audio contribution, transcription review and curated corpus export still need implementation and verification.</p>
        <Link href="/search" className="mt-5 inline-flex rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Explore current Gĩkũyũ references</Link>
      </section>
    </div>
  );
}
