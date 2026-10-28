"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";

type User = { email: string; full_name: string };

export default function RegisterPage() {
  const router = useRouter();
  const { status } = useAuth();
  useEffect(() => { if (status === "authenticated") router.replace("/account"); }, [status, router]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [dialect, setDialect] = useState("");
  const [county, setCounty] = useState("");
  const [institution, setInstitution] = useState("");
  const [error, setError] = useState("");
  const [created, setCreated] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setCreated(null);
    try {
      const user = await api.post<User>("/api/v1/auth/register", {
        full_name: name.trim(),
        email: email.trim(),
        password,
        dialect: dialect.trim() || null,
        county: county.trim() || null,
        institution: institution.trim() || null,
      });
      setCreated(user);
      setPassword("");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Account creation failed. Check your connection and details.");
    } finally {
      setLoading(false);
    }
  }

  if (status === "authenticated") return <div role="status" className="mx-auto max-w-2xl py-16 text-center text-sm text-gray-500">You are already signed in. Opening your archive…</div>;

  return (
    <div className="mx-auto max-w-2xl space-y-6 py-10 sm:py-14">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Join the archive</p><h1 className="text-3xl font-bold text-earth-900">Create a contributor account</h1><p className="leading-7 text-gray-600">Help build the Gĩkũyũ corpus through text contributions, recordings, transcription and review.</p></header>
      {error && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      {created && <div role="status" className="rounded-xl border border-green-300 bg-green-50 p-5 text-green-950"><h2 className="font-semibold">Account created</h2><p className="mt-1 text-sm leading-6">The account for {created.email} was created by the archive service. Sign in to continue.</p><Link href="/auth/login" className="mt-3 inline-flex rounded-lg bg-earth-900 px-4 py-2 font-semibold text-white">Sign in</Link></div>}
      <form onSubmit={submit} className="space-y-4 rounded-2xl border border-gray-200 p-5 sm:p-7">
        <div className="space-y-2"><label htmlFor="name" className="block text-sm font-semibold text-gray-800">Full name</label><input id="name" autoComplete="name" required minLength={2} maxLength={200} value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <div className="space-y-2"><label htmlFor="email" className="block text-sm font-semibold text-gray-800">Email address</label><input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <div className="space-y-2"><label htmlFor="password" className="block text-sm font-semibold text-gray-800">Password (at least 8 characters)</label><input id="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="dialect" className="block text-sm font-semibold text-gray-800">Gĩkũyũ dialect (optional)</label><input id="dialect" maxLength={100} value={dialect} onChange={(event) => setDialect(event.target.value)} placeholder="e.g. Ki-Murang'a" className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div><div className="space-y-2"><label htmlFor="county" className="block text-sm font-semibold text-gray-800">County (optional)</label><input id="county" maxLength={100} value={county} onChange={(event) => setCounty(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div></div>
        <div className="space-y-2"><label htmlFor="institution" className="block text-sm font-semibold text-gray-800">Institution (optional)</label><input id="institution" maxLength={200} value={institution} onChange={(event) => setInstitution(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <button type="submit" disabled={loading} className="w-full rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white hover:bg-earth-800 disabled:opacity-50">{loading ? "Creating account…" : "Create account"}</button>
      </form>
      <p className="text-sm text-gray-600">Already registered? <Link href="/auth/login" className="font-semibold text-earth-700 underline underline-offset-4">Sign in</Link>.</p>
    </div>
  );
}
