import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="mx-auto max-w-xl space-y-4 py-16">
      <h1 className="text-2xl font-bold text-earth-900">Accounts are not enabled</h1>
      <p className="leading-7 text-gray-600">
        Authentication is not connected to this deployment yet. No account or password is needed to search public reference sources.
      </p>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Search public sources</Link>
    </div>
  );
}
