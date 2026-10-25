import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About the project",
  description: "The mission, current limits and community-first principles behind Gĩkũyũ Archive.",
};

export default function AboutPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-8 py-10 sm:py-14">
      <header className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Why this exists</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-5xl">Language is more than data.</h1>
        <p className="text-lg leading-8 text-gray-600">Gĩkũyũ Archive is an independent project exploring how digital tools can make Gĩkũyũ-language knowledge easier to discover while keeping rights, consent and community interests in view.</p>
      </header>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">What works today</h2><p className="leading-7 text-gray-700">The live application searches selected public Wikimedia reference sites and links readers back to the original pages. It does not copy those pages into a permanent archive, and it does not claim ownership over them.</p><Link href="/search" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white">Explore public sources</Link></section>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">What is not live yet</h2><p className="leading-7 text-gray-700">Accounts, community audio uploads, transcription and review, persistent records, takedown processing and dataset exports are not enabled. The site will not pretend that a contribution has been received or that a dataset is cleared for reuse.</p></section>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">Principles for the archive we want to build</h2><ul className="list-disc space-y-2 pl-6 leading-7 text-gray-700"><li><strong>Consent:</strong> contributors should understand what they are sharing and how it may be used.</li><li><strong>Attribution:</strong> source and contributor context should travel with material where appropriate.</li><li><strong>Community care:</strong> sacred, sensitive or restricted knowledge should not be treated as automatically public just because it is digital.</li><li><strong>Accountability:</strong> licensing, correction, removal and access decisions need transparent processes.</li><li><strong>Honesty:</strong> the interface must distinguish a public link from content the project actually stores or verifies.</li></ul></section>
      <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6"><h2 className="font-semibold text-earth-900">A work in progress, stated plainly</h2><p className="mt-2 leading-7 text-gray-700">This project is not yet a complete or community-governed corpus. Establishing governance, durable infrastructure and review processes is part of the work, not a claim we can make in advance.</p></section>
    </article>
  );
}
