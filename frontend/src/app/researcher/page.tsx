import Link from "next/link";

export default function ResearcherPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-5 py-10">
      <h1 className="text-3xl font-bold text-earth-900">Researcher exports</h1>
      <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950">
        <h2 className="font-semibold">Curated dataset exports are not enabled</h2>
        <p className="mt-2 leading-7">
          Search results are links to third-party public sources, not records that have been collected, reviewed, or cleared for dataset redistribution.
          CSV and JSONL exports will remain disabled until persistent archive storage, source-level licence tracking, and export filters are implemented and tested.
        </p>
      </div>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Search public sources</Link>
    </div>
  );
}
