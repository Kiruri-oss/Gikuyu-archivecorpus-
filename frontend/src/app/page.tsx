import Link from "next/link";

const features = [
  { number: "01", title: "Discover", text: "Search public reference pages across an expanding directory of African languages." },
  { number: "02", title: "Document", text: "Build towards a durable home for words, oral histories, stories, transcripts, translations and annotations." },
  { number: "03", title: "Enable research", text: "Develop rights-aware datasets that can support language technology while respecting contributors and communities." },
];

export default function HomePage() {
  return (
    <div className="space-y-16 py-8 sm:py-14">
      <section className="relative overflow-hidden rounded-3xl bg-earth-900 px-6 py-14 text-white sm:px-12 sm:py-20">
        <div aria-hidden="true" className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full border border-white/10 sm:h-96 sm:w-96" />
        <div aria-hidden="true" className="pointer-events-none absolute -right-4 -top-4 h-44 w-44 rounded-full border border-white/10 sm:h-72 sm:w-72" />
        <div className="relative max-w-3xl space-y-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-savanna-500 sm:text-sm">Language · Memory · Community · Technology</p>
          <h1 className="text-4xl font-bold leading-tight sm:text-6xl">African languages deserve a lasting digital home.</h1>
          <p className="max-w-2xl text-base leading-8 text-white/80 sm:text-lg">Starting with Gĩkũyũ, building towards a growing library of African language profiles, words, oral histories, recordings, transcripts and annotated research data.</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/languages" className="rounded-lg bg-savanna-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-savanna-50">Explore language profiles <span aria-hidden="true">→</span></Link>
            <Link href="/search" className="rounded-lg border border-white/30 px-5 py-3 font-semibold text-white transition hover:bg-white/10">Search public sources</Link>
          </div>
        </div>
      </section>
      <section className="grid gap-5 md:grid-cols-3">
        {features.map((feature) => <article key={feature.number} className="rounded-2xl border border-gray-200 p-6"><p className="text-sm font-bold tracking-widest text-earth-500">{feature.number}</p><h2 className="mt-4 text-xl font-semibold text-earth-900">{feature.title}</h2><p className="mt-3 leading-7 text-gray-600">{feature.text}</p></article>)}
      </section>
      <section className="grid gap-6 rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:grid-cols-[1fr_auto] sm:items-center sm:p-8">
        <div className="space-y-2"><h2 className="text-xl font-semibold text-earth-900">The beginning, not the ceiling</h2><p className="max-w-3xl leading-7 text-gray-700">The live release currently discovers public reference pages and keeps a reading list on the visitor&apos;s device. Persistent community records, recording uploads, transcription, annotation and research exports are the next major engineering milestones.</p></div>
        <Link href="/contribute" className="inline-flex justify-center rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900 hover:bg-white">Contribution status</Link>
      </section>
      <section className="space-y-3 text-sm leading-6 text-gray-500"><p>Public references are not automatically cleared for redistribution or AI training. Always review the original source&apos;s current licence and terms.</p><p>Gĩkũyũ language materials can contain personal, sacred or community-restricted knowledge. Responsible preservation requires more than collecting files.</p></section>
    </div>
  );
}
