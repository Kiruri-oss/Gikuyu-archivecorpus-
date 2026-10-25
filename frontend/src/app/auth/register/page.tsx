import Link from "next/link";

export default function RegisterPage() {
  return (
    <div className="mx-auto max-w-xl space-y-4 py-16">
      <h1 className="text-2xl font-bold text-earth-900">Community accounts are not enabled</h1>
      <p className="leading-7 text-gray-600">
        Account creation is disabled until the production authentication service and persistent archive database are connected.
        This page does not collect or submit personal information.
      </p>
      <Link href="/search" className="inline-flex rounded-lg bg-earth-500 px-5 py-3 font-medium text-white">Search public sources</Link>
    </div>
  );
}
