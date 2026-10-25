import Link from "next/link";

export default function TakedownAdminPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 py-10">
      <h1 className="text-3xl font-bold text-earth-900">Source corrections and takedowns</h1>
      <p className="leading-7 text-gray-600">
        This deployment discovers and links to public reference pages; it does not host copies of those pages or run a persistent takedown queue.
        For removal or correction of third-party material, use the original publisher's reporting process. A formal archive-side takedown workflow is not yet enabled.
      </p>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Return to search</Link>
    </div>
  );
}
