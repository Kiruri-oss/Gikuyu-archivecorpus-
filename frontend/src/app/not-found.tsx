import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-xl space-y-5 py-20 text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-earth-700">404 · Not found</p>
      <h1 className="text-3xl font-bold text-earth-900">This page could not be found.</h1>
      <p className="leading-7 text-gray-600">The link may be outdated, or the original reference may no longer be available.</p>
      <div className="flex flex-wrap justify-center gap-3"><Link href="/" className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Go home</Link><Link href="/search" className="rounded-lg border border-earth-500 px-5 py-3 font-semibold text-earth-900">Search sources</Link></div>
    </section>
  );
}
