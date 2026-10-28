"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

export function HomeMembershipPanel() {
  const { user, status, refresh } = useAuth();

  if (status === "loading") {
    return <section role="status" className="rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-sm text-gray-500">Checking your archive session…</section>;
  }

  if (status === "unavailable") {
    return <section className="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="font-semibold text-amber-950">Your session could not be verified</p><p className="mt-1 text-sm leading-6 text-amber-900">The archive will not guess whether you are signed in. Retry the check to update your account controls.</p></div>
      <button type="button" onClick={() => void refresh()} className="shrink-0 rounded-lg border border-amber-300 bg-white px-4 py-2.5 text-sm font-semibold text-amber-950">Retry session check</button>
    </section>;
  }

  if (status === "authenticated" && user) {
    return <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">Your place in the archive</p><h2 className="mt-2 text-xl font-bold text-earth-900">Welcome back, {user.full_name.split(" ")[0] || "member"}.</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-gray-700">Continue your contributions, check review status, or pick up the references you saved.</p></div>
        <Link href="/account" className="inline-flex shrink-0 justify-center rounded-lg bg-earth-900 px-5 py-3 text-sm font-semibold text-white hover:bg-earth-800">Open My archive</Link>
      </div>
      <div className="mt-4 flex flex-wrap gap-4 border-t border-earth-900/10 pt-4 text-sm font-semibold text-earth-800">
        <Link href="/contribute" className="underline underline-offset-4">Contribute material</Link><Link href="/saved" className="underline underline-offset-4">Saved references</Link><Link href="/transcribe" className="underline underline-offset-4">Transcription workspace</Link>
      </div>
    </section>;
  }

  return <section className="rounded-2xl border border-gray-200 bg-white p-5 sm:p-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">Explore first. Join when ready.</p><h2 className="mt-2 text-xl font-bold text-earth-900">Help keep Gĩkũyũ knowledge alive.</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-gray-600">You can explore public material without an account. Membership adds a personal collection, a contribution history, and a way to help build the corpus.</p></div>
      <div className="flex shrink-0 flex-wrap gap-2"><Link href="/search" className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-semibold text-gray-800 hover:border-earth-500">Explore first</Link><Link href="/auth/register" className="rounded-lg bg-earth-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-earth-800">Join the archive</Link></div>
    </div>
  </section>;
}
