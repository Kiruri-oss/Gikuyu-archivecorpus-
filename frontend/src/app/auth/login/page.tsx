"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const tokens = await api.post<{ access_token: string; refresh_token: string }>(
        "/api/v1/auth/login",
        { email, password }
      );
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto py-16 space-y-4">
      <h1 className="text-2xl font-bold">Sign in</h1>
      <input
        type="email" value={email} onChange={(e) => setEmail(e.target.value)}
        placeholder="Email" required aria-label="Email"
        className="w-full p-3 border rounded-lg"
      />
      <input
        type="password" value={password} onChange={(e) => setPassword(e.target.value)}
        placeholder="Password" required aria-label="Password"
        className="w-full p-3 border rounded-lg"
      />
      <button
        type="submit" disabled={loading}
        className="w-full py-3 bg-earth-500 text-white rounded-lg disabled:opacity-50"
      >
        {loading ? "Signing in..." : "Sign in"}
      </button>
      {error && <p role="alert" className="text-red-600">{error}</p>}
    </form>
  );
}