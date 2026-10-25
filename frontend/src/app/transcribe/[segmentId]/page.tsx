import Link from "next/link";

export default function TranscribePage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 py-10">
      <h1 className="text-3xl font-bold text-earth-900">Community transcription</h1>
      <p className="leading-7 text-gray-600">
        Transcription editing is not enabled in this deployment because archive records and authentication are not connected to persistent services.
        No transcript entered here would be saved, so editing controls are intentionally unavailable.
      </p>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Search public sources</Link>
    </div>
  );
}
