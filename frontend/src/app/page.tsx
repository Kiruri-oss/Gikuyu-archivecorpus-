import Link from "next/link";

const features = [
  { number: "01", title: "Discover", text: "Search public reference pages for Gĩkũyũ words, language topics and related knowledge." },
  { number: "02", title: "Follow the source", text: "Open the original publisher&apos;s page to review its context, licence and reuse terms." },
  { number: "03", title: "Preserve responsibly", text: "Help shape a future community archive built around consent, attribution and respect for cultural knowledge." },
];

export default function HomePage() {
  return (
    <div className="space-y-16 py-8 sm:py-14">
      <section className="relative overflow-hidden rounded-3xl bg-earth-900 px-6 py-14 text-white sm:px-12 sm:py-20">
        <div aria-hidden="true" className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full border border-white/10 sm:h-96 sm:w-96" />
        <div aria-hidden="true" className="pointer-events-none absolute -right-4 -top-4 h-44 w-44 rounded-full border border-white/10 sm:h-72 sm:w-72" />
        <div className="relative max-w-3xl space-y-6">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-savanna-500 sm:text-sm">Language · Memory · Community</p>
          <h1 className="text-4xl font-bold leading-tight sm:text-6xl">Gĩkũyũ knowledge deserves a lasting home.</h1>
          <p className="max-w-2xl text-base leading-8 text-white/80 sm:text-lg">Explore public Gĩkũyũ and Kikuyu-language references while we build towards a community-governed archive that respects the people behind the knowledge.</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/search" className="rounded-lg bg-savanna-500 px-5 py-3 font-semibold text-earth-900 transition hover:bg-savanna-50">Explore public sources <span aria-hidden="true">→</span></Link>
            <Link href="/about" className="rounded-lg border border-white/30 px-5 py-3 font-semibold text-white transition hover:bg-white/10">Our approach</Link>
          </div>
        </div>
      </section>
      <section className="grid gap-5 md:grid-cols-3">
        {features.map((feature) => <article key={feature.number} className="rounded-2xl border border-gray-200 p-6"><p className="text-sm font-bold tracking-widest text-earth-500">{feature.number}</p><h2 className="mt-4 text-xl font-semibold text-earth-900">{feature.title}</h2><p className="mt-3 leading-7 text-gray-600">{feature.text}</p></article>)}
      </section>
      <section className="grid gap-6 rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:grid-cols-[1fr_auto] sm:items-center sm:p-8">
        <div className="space-y-2"><h2 className="text-xl font-semibold text-earth-900">A transparent beginning</h2><p className="max-w-3xl leading-7 text-gray-700">This live version is a public-source discovery tool. It does not yet store community recordings, transcripts, accounts or research datasets. We will not invite contributions until storage, consent, security and deletion controls are ready.</p></div>
        <Link href="/contribute" className="inline-flex justify-center rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900 hover:bg-white">Contribution status</Link>
      </section>
      <section className="space-y-3 text-sm leading-6 text-gray-500"><p>Public references are not automatically cleared for redistribution or AI training. Always review the original source&apos;s current licence and terms.</p><p>Gĩkũyũ language materials can contain personal, sacred or community-restricted knowledge. Responsible preservation requires more than collecting files.</p></section>
    </div>
  );
}
