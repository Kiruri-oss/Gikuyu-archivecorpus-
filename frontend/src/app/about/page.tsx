import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About the project",
  description: "The mission, current limits and community-first principles behind Gĩkũyũ Archive and the African language library.",
};

export default function AboutPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-8 py-10 sm:py-14">
      <header className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Why this exists</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-5xl">African languages deserve a lasting digital home.</h1>
        <p className="text-lg leading-8 text-gray-600">Gĩkũyũ Archive begins with Gĩkũyũ and is designed to grow into an African language library: searchable language profiles, community texts, recordings, transcripts, translations and carefully annotated datasets.</p>
      </header>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">What works today</h2><p className="leading-7 text-gray-700">The live application searches selected public Wikimedia reference sites and links readers back to original pages. The language directory is an initial discovery layer, not a claim that a persistent corpus is already hosted here.</p><div className="flex flex-wrap gap-3"><Link href="/languages" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white">Explore language profiles</Link><Link href="/search" className="inline-flex rounded-lg border px-4 py-3 font-semibold text-earth-900">Search public sources</Link></div></section>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">What is not live yet</h2><p className="leading-7 text-gray-700">Accounts, community audio uploads, transcription and review, persistent records, takedown processing and dataset exports are not enabled. The site will not pretend that a contribution has been received or that a dataset is cleared for reuse.</p></section>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">Principles for the archive we want to build</h2><ul className="list-disc space-y-2 pl-6 leading-7 text-gray-700"><li><strong>Consent:</strong> contributors should understand what they are sharing and how it may be used.</li><li><strong>Attribution:</strong> source and contributor context should travel with material where appropriate.</li><li><strong>Community care:</strong> sacred, sensitive or restricted knowledge should not be treated as automatically public just because it is digital.</li><li><strong>Accountability:</strong> licensing, correction, removal and access decisions need transparent processes.</li><li><strong>Open language infrastructure:</strong> schemas and export formats should make it possible for researchers and other tools to build on permitted records.</li></ul></section>
      <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6"><h2 className="font-semibold text-earth-900">Ambitious scope, honest release status</h2><p className="mt-2 leading-7 text-gray-700">The goal is a durable, multilingual African language library. Achieving it requires persistent storage, people contributing and reviewing material, rights-aware ingestion, and reliable operations—not just an attractive interface.</p></section>
    </article>
  );
}
