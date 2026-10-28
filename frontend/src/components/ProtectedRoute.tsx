"use client";

import Link from "next/link";
import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

interface ProtectedRouteProps {
  children: ReactNode;
  roles?: string[];
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, status, refresh } = useAuth();

  useEffect(() => {
    if (status === "anonymous") {
      const next = pathname.startsWith("/") && !pathname.startsWith("//") ? pathname : "/account";
      router.replace(`/auth/login?next=${encodeURIComponent(next)}`);
    }
  }, [status, pathname, router]);

  if (status === "loading") {
    return <div role="status" className="mx-auto max-w-3xl py-20 text-center"><span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-earth-200 border-t-earth-900" /><p className="mt-4 text-sm text-gray-500">Checking your archive session…</p></div>;
  }

  if (status === "unavailable") {
    return <section className="mx-auto max-w-xl py-16 text-center"><h1 className="text-2xl font-bold text-earth-900">We could not verify your session</h1><p className="mt-3 leading-7 text-gray-600">Your sign-in has not been treated as valid or invalid because the archive service could not confirm it. Check your connection and retry.</p><button type="button" onClick={() => void refresh()} className="mt-5 rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Retry session check</button><p className="mt-4"><Link href="/auth/login" className="font-semibold text-earth-700 underline underline-offset-4">Sign in again</Link></p></section>;
  }

  if (status === "anonymous" || !user) return <div role="status" className="py-16 text-center text-sm text-gray-500">Taking you to sign in…</div>;

  if (roles && !roles.includes(user.role)) {
    return <section className="mx-auto max-w-xl py-16 text-center"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Access level</p><h1 className="mt-3 text-2xl font-bold text-earth-900">This workspace is not available to your account</h1><p className="mt-3 leading-7 text-gray-600">You are signed in as {user.role}. This workspace requires: {roles.join(", ")}. Your account remains signed in.</p><Link href="/account" className="mt-5 inline-flex rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Return to My archive</Link></section>;
  }

  return <>{children}</>;
}