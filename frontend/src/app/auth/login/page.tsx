"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";

type TokenPair = { access_token: string; refresh_token: string; token_type: string };

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await api.post<TokenPair>("/api/v1/auth/login", { email: email.trim(), password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/contribute");
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Sign-in failed. Check your connection and credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 py-10 sm:py-14">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Community archive</p><h1 className="text-3xl font-bold text-earth-900">Sign in</h1><p className="leading-7 text-gray-600">Sign in to contribute Gĩkũyũ material, transcribe recordings or access researcher tools.</p></header>
      {error && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm leading-6 text-red-900">{error}</p>}
      <form onSubmit={submit} className="space-y-4 rounded-2xl border border-gray-200 p-5 sm:p-7">
        <div className="space-y-2"><label htmlFor="email" className="block text-sm font-semibold text-gray-800">Email address</label><input id="email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <div className="space-y-2"><label htmlFor="password" className="block text-sm font-semibold text-gray-800">Password</label><input id="password" type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-gray-300 p-3 text-gray-900 focus:border-earth-500 focus:outline-none focus:ring-2 focus:ring-earth-500/20" /></div>
        <button type="submit" disabled={loading} className="w-full rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white hover:bg-earth-800 disabled:opacity-50">{loading ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="text-sm text-gray-600">New to the archive? <Link href="/auth/register" className="font-semibold text-earth-700 underline underline-offset-4">Create a contributor account</Link>.</p>
    </div>
  );
}
