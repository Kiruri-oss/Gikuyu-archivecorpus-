import Link from "next/link";
import type { Metadata } from "next";
import { AFRICAN_LANGUAGES } from "@/lib/languages";

export const metadata: Metadata = {
  title: "African language profiles",
  description: "An expanding directory of African language profiles and public reference discovery.",
};

export default function LanguagesPage() {
  return (
    <div className="space-y-8 py-8 sm:py-12">
      <header className="max-w-3xl space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">An expanding directory</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-5xl">African languages deserve a digital home.</h1>
        <p className="text-lg leading-8 text-gray-600">The long-term goal is a growing library of language profiles, words, stories, recordings, transcripts, translations and annotations—with source, rights and contributor context preserved.</p>
        <p className="leading-7 text-gray-600">These initial profiles open public reference discovery. They do not yet represent a locally curated corpus or guarantee that every language has an active Wikimedia source.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {AFRICAN_LANGUAGES.map((language) => (
          <article key={language.code} className="flex flex-col rounded-2xl border border-gray-200 p-5 transition hover:border-earth-500/60 hover:shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{language.region}</p>
            <h2 className="mt-2 text-xl font-semibold text-earth-900">{language.name}</h2>
            <p className="mt-1 text-sm text-gray-500">{language.nativeName} · {language.family}</p>
            <p className="mt-3 flex-1 leading-7 text-gray-600">{language.description}</p>
            <Link href={`/search?lang=${language.code}`} className="mt-5 inline-flex font-semibold text-earth-700 underline underline-offset-4">Explore public references ↗</Link>
          </article>
        ))}
      </div>
      <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-earth-900">From discovery to a real library</h2>
        <p className="mt-3 leading-7 text-gray-700">The next phases are persistent text records, a source and licence registry, consent-based audio contributions, time-aligned transcription and translation, reviewer annotations, and exports for permitted research uses. That foundation must work for Gĩkũyũ first and then extend across languages without flattening their differences.</p>
      </section>
    </div>
  );
}
