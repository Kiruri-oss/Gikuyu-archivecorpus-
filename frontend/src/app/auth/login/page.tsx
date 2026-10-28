"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { setTokens } from "@/lib/auth";
import { useAuth } from "@/components/AuthProvider";

type TokenPair = { access_token: string; refresh_token: string; token_type: string };

export default function LoginPage() {
  const router = useRouter();
  const { status } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/account");
  }, [status, router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await api.post<TokenPair>("/api/v1/auth/login", { email: email.trim(), password });
      setTokens(tokens.access_token, tokens.refresh_token);
      const requested = new URLSearchParams(window.location.search).get("next");
      const destination = requested && requested.startsWith("/") && !requested.startsWith("//") && requested !== "/auth/login" && requested !== "/auth/register"
        ? requested
        : "/account";
      router.replace(destination);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Sign-in failed. Check your connection and credentials.");
    } finally {
      setLoading(false);
    }
  }

  if (status === "loading") return <div role="status" className="mx-auto max-w-xl py-16 text-center text-sm text-gray-500">Checking your archive session…</div>;
  if (status === "authenticated") return <div role="status" className="mx-auto max-w-xl py-16 text-center text-sm text-gray-500">You are already signed in. Opening your archive…</div>;

  return (
    <div className="mx-auto grid max-w-5xl overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm sm:my-10 lg:grid-cols-[0.9fr_1.1fr]">
      <aside className="bg-earth-900 px-6 py-8 text-white sm:px-9 sm:py-10">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-savanna-500">Gĩkũyũ Archive Corpus</p>
        <h1 className="mt-4 text-3xl font-bold leading-tight sm:text-4xl">Welcome back to the archive.</h1>
        <p className="mt-4 leading-7 text-white/75">Pick up where you left off: contribute language material, work on transcripts, and keep your place in the community archive.</p>
        <div className="mt-8 space-y-3 border-t border-white/15 pt-5 text-sm text-white/80">
          <p><span className="mr-2 text-savanna-500">01</span> Preserve Gĩkũyũ knowledge</p>
          <p><span className="mr-2 text-savanna-500">02</span> Improve records together</p>
          <p><span className="mr-2 text-savanna-500">03</span> Build a lasting contribution record</p>
        </div>
      </aside>
      <section className="px-6 py-8 sm:px-9 sm:py-10">
        <header className="mb-7 space-y-2"><h2 className="text-2xl font-bold text-earth-900">Sign in</h2><p className="leading-6 text-gray-600">Use the email and password connected to your archive account.</p></header>
        {status === "unavailable" && <p role="status" className="mb-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm leading-6 text-amber-900">The archive could not verify an existing session. You can still attempt to sign in below.</p>}
        {error && <p role="alert" className="mb-4 rounded-xl border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
        <form onSubmit={submit} className="space-y-5">
          <div className="space-y-2"><label htmlFor="email" className="block text-sm font-semibold text-gray-800">Email address</label><input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3.5 transition focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
          <div className="space-y-2"><div className="flex items-center justify-between gap-3"><label htmlFor="password" className="block text-sm font-semibold text-gray-800">Password</label></div><input id="password" type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3.5 transition focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
          <button type="submit" disabled={loading} className="w-full rounded-xl bg-earth-900 px-5 py-3.5 font-semibold text-white transition hover:bg-earth-800 disabled:opacity-60">{loading ? "Signing in…" : "Sign in to your archive"}</button>
        </form>
        <p className="mt-6 text-sm leading-6 text-gray-600">New to the archive? <Link href="/auth/register" className="font-semibold text-earth-700 underline underline-offset-4">Create an account</Link>.</p>
        <p className="mt-3 text-xs leading-5 text-gray-500">Your session is checked against the archive service. If the service is temporarily unavailable, the interface will say so rather than guessing your sign-in status.</p>
      </section>
    </div>
  );
}