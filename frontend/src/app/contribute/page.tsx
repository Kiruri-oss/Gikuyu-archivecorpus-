import Link from "next/link";

export default function ContributePage() {
  return (
    <div className="mx-auto max-w-2xl space-y-5 py-10">
      <h1 className="text-3xl font-bold text-earth-900">Contribute to the archive</h1>
      <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950">
        <h2 className="font-semibold">Recording submissions are not enabled yet</h2>
        <p className="mt-2 leading-7">
          The production deployment does not have persistent audio storage or a configured archive database.
          To protect your work and avoid implying that a recording was saved when it was not, this page will not
          record or upload audio. Nothing you enter here is collected.
        </p>
      </div>
      <p className="leading-7 text-gray-700">
        The next infrastructure step is to connect a persistent database and object storage with access controls,
        consent and licence metadata, and a tested deletion process. Public-source discovery is available in the meantime.
      </p>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Explore public sources</Link>
    </div>
  );
}
