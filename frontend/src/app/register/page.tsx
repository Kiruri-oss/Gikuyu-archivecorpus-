"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

const backendConfigured = Boolean(process.env.NEXT_PUBLIC_API_URL);

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [dialect, setDialect] = useState("");
  const [county, setCounty] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.post("/api/v1/auth/register", {
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        dialect: dialect.trim() || null,
        county: county.trim() || null,
      });
      router.push("/login?registered=1");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not create the account. Check the connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="mx-auto max-w-xl space-y-6 py-10 sm:py-14"><header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Join the archive</p><h1 className="text-3xl font-bold text-earth-900">Create a contributor account</h1><p className="leading-7 text-gray-600">Help preserve Gĩkũyũ words, oral histories and stories. You can optionally share your dialect and county to help describe the material you contribute.</p></header>{!backendConfigured && <p role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950">Account storage is not connected to this production deployment yet. Registration is disabled until the backend is configured.</p>}<form onSubmit={submit} className="space-y-4 rounded-2xl border p-6"><div className="space-y-2"><label htmlFor="full-name" className="block text-sm font-semibold">Full name</label><input id="full-name" required minLength={2} maxLength={200} autoComplete="name" value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full rounded-lg border p-3" /></div><div className="space-y-2"><label htmlFor="email" className="block text-sm font-semibold">Email</label><input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border p-3" /></div><div className="space-y-2"><label htmlFor="password" className="block text-sm font-semibold">Password</label><input id="password" type="password" required minLength={8} maxLength={128} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border p-3" /><p className="text-xs text-gray-500">Use at least 8 characters.</p></div><div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><label htmlFor="dialect" className="block text-sm font-semibold">Dialect (optional)</label><input id="dialect" maxLength={100} value={dialect} onChange={(e) => setDialect(e.target.value)} className="w-full rounded-lg border p-3" /></div><div className="space-y-2"><label htmlFor="county" className="block text-sm font-semibold">County (optional)</label><input id="county" maxLength={100} value={county} onChange={(e) => setCounty(e.target.value)} className="w-full rounded-lg border p-3" /></div></div>{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-900">{error}</p>}<button type="submit" disabled={busy || !backendConfigured} className="w-full rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white disabled:opacity-50">{busy ? "Creating account…" : "Create account"}</button><p className="text-sm text-gray-600">Already registered? <Link href="/login" className="font-semibold text-earth-700 underline">Sign in</Link>.</p></form></section>;
}
