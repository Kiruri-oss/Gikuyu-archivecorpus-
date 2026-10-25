import Link from "next/link";
import { DailyProverb } from "@/components/DailyProverb";
import { ContributorLeaderboard } from "@/components/ContributorLeaderboard";

const archivePillars = [
  {
    number: "01",
    title: "Words & written tradition",
    text: "Proverbs, riddles, vocabulary, folklore, translations, original writing and eligible literature, with source records and provenance.",
  },
  {
    number: "02",
    title: "Voices & oral memory",
    text: "Recordings of stories, conversations and knowledge shared by Gĩkũyũ speakers, with consent and speaker context preserved.",
  },
  {
    number: "03",
    title: "Transcription & annotation",
    text: "Time-aligned transcripts, translations, dialect labels, reviewer corrections and orthography support for ĩ and ũ.",
  },
  {
    number: "04",
    title: "Research-ready corpus",
    text: "Curated Gĩkũyũ datasets for language research and AI, with source provenance and reuse permissions attached to each record.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-14 py-8 sm:py-12">
      <section className="relative overflow-hidden rounded-3xl bg-earth-900 px-6 py-12 text-white sm:px-12 sm:py-16">
        <div aria-hidden="true" className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full border border-white/10 sm:h-[28rem] sm:w-[28rem]" />
        <div aria-hidden="true" className="pointer-events-none absolute -right-5 -top-5 h-48 w-48 rounded-full border border-white/10 sm:h-72 sm:w-72" />
        <div className="relative max-w-3xl space-y-5">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-savanna-500 sm:text-sm">Gĩkũyũ language · Memory · Knowledge</p>
          <h1 className="text-4xl font-bold leading-tight sm:text-6xl">Build the digital home for Gĩkũyũ.</h1>
          <p className="max-w-2xl text-base leading-8 text-white/85 sm:text-lg">Gĩkũyũ Archive Corpus is being built to collect, preserve and make searchable Gĩkũyũ words, proverbs, riddles, stories, literature, oral histories, recordings, transcripts and annotated language data.</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/search" className="rounded-lg bg-savanna-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-savanna-50">Explore available material <span aria-hidden="true">→</span></Link>
            <Link href="/contribute" className="rounded-lg border border-white/30 px-5 py-3 font-semibold text-white transition hover:bg-white/10">Contribute to the corpus</Link>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-white/65">The public website currently exposes source discovery. Persistent community submissions, audio storage and review workflows still need production infrastructure; the site will not claim that an upload was saved when it was not.</p>
        </div>
      </section>

      <DailyProverb />
      <ContributorLeaderboard />

      <section className="space-y-5">
        <div className="max-w-3xl space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">The archive we are building</p>
          <h2 className="text-2xl font-bold text-earth-900 sm:text-3xl">A real corpus, not just search results.</h2>
          <p className="leading-7 text-gray-600">The objective is a growing, searchable body of Gĩkũyũ material. Each archived item should preserve its source, date found, language or dialect, rights information and review history.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {archivePillars.map((pillar) => (
            <article key={pillar.number} className="rounded-2xl border border-gray-200 bg-white p-5 sm:p-6">
              <p className="text-sm font-bold tracking-widest text-earth-500">{pillar.number}</p>
              <h3 className="mt-3 text-xl font-semibold text-earth-900">{pillar.title}</h3>
              <p className="mt-2 leading-7 text-gray-600">{pillar.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:grid-cols-[1fr_auto] sm:items-center sm:p-8">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">The collection engine</p>
          <h2 className="text-xl font-semibold text-earth-900 sm:text-2xl">Find more. Preserve the evidence. Improve the record.</h2>
          <p className="max-w-3xl leading-7 text-gray-700">The Hunter is intended to discover Gĩkũyũ material across configured public sources, record provenance and rights evidence, and send candidates into the archive workflow. Contributions, transcription, annotation and curated exports are core parts of the same product.</p>
        </div>
        <Link href="/languages" className="inline-flex justify-center rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-white">Explore the corpus</Link>
      </section>

      <section className="space-y-2 border-t border-gray-200 pt-6 text-sm leading-6 text-gray-500">
        <p>Gĩkũyũ is the sole focus of this archive. The goal is to build a deep, useful corpus for the language.</p>
        <p>Public access, archive storage, research use and AI-training permission are recorded separately where the source terms require it. The Hunter preserves source evidence so that records can be reviewed and corrected.</p>
      </section>
    </div>
  );
}
