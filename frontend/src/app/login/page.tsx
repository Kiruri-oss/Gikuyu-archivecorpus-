"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

const backendConfigured = Boolean(process.env.NEXT_PUBLIC_API_URL);

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const tokens = await api.post<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", { email, password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/contribute");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not sign in. Check the connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="mx-auto max-w-lg space-y-6 py-10 sm:py-14"><header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Contributor access</p><h1 className="text-3xl font-bold text-earth-900">Sign in</h1><p className="leading-7 text-gray-600">Sign in to submit Gĩkũyũ material or access researcher tools.</p></header>{!backendConfigured && <p role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950">The production account API is not connected yet. Sign-in will work after the backend URL is configured and the service is running.</p>}<form onSubmit={submit} className="space-y-4 rounded-2xl border p-6"><div className="space-y-2"><label htmlFor="email" className="block text-sm font-semibold">Email</label><input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border p-3" /></div><div className="space-y-2"><label htmlFor="password" className="block text-sm font-semibold">Password</label><input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border p-3" /></div>{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-900">{error}</p>}<button type="submit" disabled={busy || !backendConfigured} className="w-full rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button><p className="text-sm text-gray-600">New to the archive? <Link href="/register" className="font-semibold text-earth-700 underline">Create an account</Link>.</p></form></section>;
}
