"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setTokens } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [dialect, setDialect] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName,
        dialect: dialect || null,
      });
      const tokens = await api.post<{ access_token: string; refresh_token: string }>(
        "/api/v1/auth/login",
        { email, password }
      );
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto py-16 space-y-4">
      <h1 className="text-2xl font-bold">Register</h1>
      <input
        type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
        placeholder="Full name" required aria-label="Full name"
        className="w-full p-3 border rounded-lg"
      />
      <input
        type="email" value={email} onChange={(e) => setEmail(e.target.value)}
        placeholder="Email" required aria-label="Email"
        className="w-full p-3 border rounded-lg"
      />
      <input
        type="password" value={password} onChange={(e) => setPassword(e.target.value)}
        placeholder="Password (min 8 chars)" required minLength={8} aria-label="Password"
        className="w-full p-3 border rounded-lg"
      />
      <input
        type="text" value={dialect} onChange={(e) => setDialect(e.target.value)}
        placeholder="Dialect (optional)" aria-label="Dialect"
        className="w-full p-3 border rounded-lg"
      />
      <button
        type="submit" disabled={loading}
        className="w-full py-3 bg-earth-500 text-white rounded-lg disabled:opacity-50"
      >
        {loading ? "Creating account..." : "Create account"}
      </button>
      {error && <p role="alert" className="text-red-600">{error}</p>}
      <p className="text-sm text-center text-gray-600">
        Already registered? <Link href="/auth/login" className="text-earth-500 underline">Sign in</Link>
      </p>
    </form>
  );
}