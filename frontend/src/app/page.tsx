import Link from "next/link";

const archivePillars = [
  {
    number: "01",
    title: "Words & written tradition",
    text: "Proverbs, riddles, vocabulary, folklore, translations, original writing and public-domain literature—with source and licence records.",
  },
  {
    number: "02",
    title: "Voices & oral memory",
    text: "Consent-based recordings of stories, conversations, songs where permitted, and knowledge carried by Gĩkũyũ speakers.",
  },
  {
    number: "03",
    title: "Transcription & annotation",
    text: "Time-aligned transcripts, translations, dialect labels and careful orthography, including the distinctive letters ĩ and ũ.",
  },
  {
    number: "04",
    title: "Research-ready corpus",
    text: "Curated, provenance-rich datasets for language research and AI, with reuse permissions kept separate from public access.",
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
          <h1 className="text-4xl font-bold leading-tight sm:text-6xl">Gĩkũyũ deserves a permanent home on the internet.</h1>
          <p className="max-w-2xl text-base leading-8 text-white/85 sm:text-lg">The mission is to build a serious, searchable Gĩkũyũ corpus: words, proverbs, riddles, stories, literature, oral histories, recordings, transcripts and annotated language data. Built for speakers first, and for the researchers building tomorrow’s language technology.</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/search" className="rounded-lg bg-savanna-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-savanna-50">Browse available material <span aria-hidden="true">→</span></Link>
            <Link href="/contribute" className="rounded-lg border border-white/30 px-5 py-3 font-semibold text-white transition hover:bg-white/10">Contribute to the corpus</Link>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-white/65">The current public release provides source discovery. Persistent community submissions, audio storage and review workflows are still being connected; this site will not pretend an upload has been saved when it has not.</p>
        </div>
      </section>

      <section className="space-y-5">
        <div className="max-w-3xl space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">The archive we are building</p>
          <h2 className="text-2xl font-bold text-earth-900 sm:text-3xl">Not just a search page. A corpus.</h2>
          <p className="leading-7 text-gray-600">Every eligible record should retain its provenance, language or dialect, licence, consent and permitted uses. Collection should be ambitious; publication and training use must be deliberate.</p>
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
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">A larger African language mission</p>
          <h2 className="text-xl font-semibold text-earth-900 sm:text-2xl">Start with depth. Expand with purpose.</h2>
          <p className="max-w-3xl leading-7 text-gray-700">Gĩkũyũ is the foundation, not a placeholder. Once the archive pipeline is dependable, the same rights-aware infrastructure can support other African languages without reducing them to a directory of external links.</p>
        </div>
        <Link href="/languages" className="inline-flex justify-center rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-white">Language profiles</Link>
      </section>

      <section className="space-y-2 border-t border-gray-200 pt-6 text-sm leading-6 text-gray-500">
        <p>The Hunter is being designed to respect robots.txt and archive only material with an identifiable supported open licence. Websites, books, news, video and recordings without verified rights require permission.</p>
        <p>AI-training permission is tracked separately from permission to display or research a record. Publicly accessible does not automatically mean reusable.</p>
      </section>
    </div>
  );
}
