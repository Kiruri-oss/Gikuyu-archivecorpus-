import Link from "next/link";
import { DailyProverb } from "@/components/DailyProverb";
import { ContributorLeaderboard } from "@/components/ContributorLeaderboard";
import { HomeMembershipPanel } from "@/components/HomeMembershipPanel";

const archivePillars = [
  {
    number: "01",
    title: "Preserve",
    text: "Discover available Gĩkũyũ material with source provenance and rights information. Only approved records are presented as public archive content.",
    href: "/languages",
    action: "Explore the corpus"
  },
  {
    number: "02",
    title: "Participate",
    text: "Submit Gĩkũyũ text or recordings, transcribe available audio, and add linguistic annotations. Your work is retained with review status.",
    href: "/contribute",
    action: "Contribute material"
  },
  {
    number: "03",
    title: "Belong",
    text: "Your member account gives you a lasting record of contributions, their review status, and your role in the archive community.",
    href: "/account",
    action: "Open My archive"
  },
  {
    number: "04",
    title: "Return",
    text: "Save useful references to your personal collection. Signed-in collections are stored with your account and can be used across devices.",
    href: "/saved",
    action: "View saved references"
  },
  {
    number: "05",
    title: "Discover",
    text: "Explore public material without an account. Search the available corpus before deciding how you want to participate.",
    href: "/search",
    action: "Search Gĩkũyũ"
  }
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
          <p className="max-w-2xl text-base leading-8 text-white/85 sm:text-lg">Explore a growing, rights-aware library for Gĩkũyũ words, proverbs, stories, literature, oral histories, recordings and annotated language data. Public material stays discoverable; members can contribute, organise their reading and build a lasting record of their work.</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/search" className="rounded-lg bg-savanna-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-savanna-50">Explore available material <span aria-hidden="true">→</span></Link>
            <Link href="/contribute" className="rounded-lg border border-white/30 px-5 py-3 font-semibold text-white transition hover:bg-white/10">Contribute to the corpus</Link>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-white/65">Public records retain their source and reuse permissions. Member contributions enter review before publication, so a submission is never presented as approved before it has been checked.</p>
        </div>
      </section>

      <HomeMembershipPanel />

      <DailyProverb />
      <ContributorLeaderboard />

      <section className="space-y-5">
        <div className="max-w-3xl space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">The archive we are building</p>
          <h2 className="text-2xl font-bold text-earth-900 sm:text-3xl">A living archive, built by its community.</h2>
          <p className="leading-7 text-gray-600">Every part of the experience has a job: make available knowledge easy to discover, keep the provenance and permissions attached, and give contributors a useful record of what they add.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {archivePillars.map((pillar) => (
            <article key={pillar.number} className="flex flex-col rounded-2xl border border-gray-200 bg-white p-5 transition hover:border-earth-300 sm:p-6">
              <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-earth-50 text-sm font-bold text-earth-800">{pillar.number}</span><h3 className="text-xl font-semibold text-earth-900">{pillar.title}</h3></div>
              <p className="mt-3 flex-1 leading-7 text-gray-600">{pillar.text}</p>
              <Link href={pillar.href} className="mt-5 inline-flex w-fit items-center gap-2 text-sm font-semibold text-earth-800 underline decoration-earth-300 underline-offset-4 hover:decoration-earth-700">{pillar.action} <span aria-hidden="true">→</span></Link>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:grid-cols-[1fr_auto] sm:items-center sm:p-8">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">The collection engine</p>
          <h2 className="text-xl font-semibold text-earth-900 sm:text-2xl">Find more. Preserve the evidence. Improve the record.</h2>
          <p className="max-w-3xl leading-7 text-gray-700">The Hunter discovers Gĩkũyũ material across configured public sources, preserving evidence for language, provenance and reuse rights. Community submissions, transcript work, annotations and permission-filtered research exports belong to the same archive—not separate products.</p>
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
