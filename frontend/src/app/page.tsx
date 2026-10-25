import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-12 py-10">
      <section className="mx-auto max-w-3xl space-y-5 text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Language discovery · Community preservation</p>
        <h1 className="text-4xl font-bold text-earth-900 sm:text-5xl">Preserve Gĩkũyũ. Together.</h1>
        <p className="mx-auto max-w-2xl text-lg leading-8 text-gray-600">
          Discover Gĩkũyũ and Kikuyu-language material indexed by public reference sites.
          Each result links back to its original publisher so you can inspect the source and its reuse terms.
        </p>
        <div className="flex flex-wrap justify-center gap-4 pt-2">
          <Link href="/search" className="rounded-lg bg-earth-500 px-6 py-3 font-medium text-white">Search public sources</Link>
          <Link href="/contribute" className="rounded-lg border border-earth-500 px-6 py-3 font-medium text-earth-700">Contribution status</Link>
        </div>
      </section>
      <section className="mx-auto grid max-w-4xl gap-4 sm:grid-cols-3">
        <div className="rounded-xl border p-5"><h2 className="font-semibold">Discover</h2><p className="mt-2 text-sm leading-6 text-gray-600">Search public Wikimedia reference pages through a server-side API. Results link to their source.</p></div>
        <div className="rounded-xl border p-5"><h2 className="font-semibold">Respect rights</h2><p className="mt-2 text-sm leading-6 text-gray-600">Source links and licence reminders are shown. Always check the original page before reusing material.</p></div>
        <div className="rounded-xl border p-5"><h2 className="font-semibold">Build carefully</h2><p className="mt-2 text-sm leading-6 text-gray-600">Persistent submissions, accounts, community transcripts, and curated dataset exports are not enabled in this deployment yet.</p></div>
      </section>
    </div>
  );
}
