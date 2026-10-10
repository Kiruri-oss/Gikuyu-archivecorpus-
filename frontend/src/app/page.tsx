import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-12 py-8">
      <section className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-earth-900">
          Preserve Gĩkũyũ. Together.
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          A community-controlled archive of Kikuyu audio, literature, and oral
          history. Contribute recordings, transcribe, translate, and build the
          dataset that will power Kikuyu AI.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/contribute" className="px-6 py-3 bg-earth-500 text-white rounded-lg">
            Contribute
          </Link>
          <Link href="/search" className="px-6 py-3 border border-earth-500 text-earth-500 rounded-lg">
            Browse Archive
          </Link>
        </div>
      </section>
    </div>
  );
}