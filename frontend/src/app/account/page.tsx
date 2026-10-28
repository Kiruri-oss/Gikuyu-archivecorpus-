"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";
import { readSavedReferences } from "@/lib/saved-references";

type Contribution = {
  id: string;
  title: string;
  kind: "text" | "audio";
  genre?: string | null;
  status: string;
  created_at: string;
};

type MemberSummary = {
  totals: {
    total: number;
    texts: number;
    recordings: number;
    pending: number;
    approved: number;
    rejected: number;
    taken_down: number;
  };
  recent: Contribution[];
};

const statusNames: Record<string, string> = {
  pending: "In review",
  approved: "Approved",
  rejected: "Not approved",
  taken_down: "Withdrawn",
};

function dateLabel(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date unavailable" : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

function AccountContent() {
  const { user, status, refresh } = useAuth();
  const [summary, setSummary] = useState<MemberSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const syncSavedCount = async () => {
      const localItems = readSavedReferences();
      if (status !== "authenticated") {
        if (!cancelled) setSavedCount(localItems.length);
        return;
      }
      try {
        const result = await api.get<{ items: { reference_key: string }[] }>("/api/v1/community/saved-references");
        const remoteKeys = new Set(result.items.map((item) => item.reference_key));
        const unsyncedLocalCount = localItems.filter((item) => !remoteKeys.has(item.id)).length;
        if (!cancelled) setSavedCount(result.items.length + unsyncedLocalCount);
      } catch {
        if (!cancelled) setSavedCount(localItems.length);
      }
    };
    void syncSavedCount();
    const onFocus = () => { void syncSavedCount(); };
    const onStorage = () => { void syncSavedCount(); };
    window.addEventListener("storage", onStorage);
    window.addEventListener("focus", onFocus);
    return () => {
      cancelled = true;
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("focus", onFocus);
    };
  }, [status]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    api.get<MemberSummary>("/api/v1/community/me")
      .then((data) => { if (!cancelled) setSummary(data); })
      .catch((cause) => {
        if (cancelled) return;
        setError(cause instanceof ApiError ? cause.message : "Your contribution record could not be loaded.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-8 py-6 sm:py-10">
      <section className="rounded-3xl bg-earth-900 px-6 py-8 text-white sm:px-9 sm:py-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-savanna-500">Your place in the archive</p>
            <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Welcome, {user?.full_name.split(" ")[0] || "member"}.</h1>
            <p className="mt-3 leading-7 text-white/75">This is your account and contribution record. Your work enters the public corpus only after the archive review process approves it and its permissions allow publication.</p>
          </div>
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-2 text-sm text-white/90"><span className="h-2 w-2 rounded-full bg-savanna-500" /> Signed in · {user?.role ?? "member"}</span>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-[1.1fr_1.9fr]">
        <article className="rounded-2xl border border-gray-200 bg-white p-5 sm:p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-earth-700">Account details</p>
          <h2 className="mt-2 text-xl font-bold text-earth-900">{user?.full_name}</h2>
          <p className="mt-1 break-words text-sm text-gray-600">{user?.email}</p>
          <dl className="mt-5 space-y-3 border-t border-gray-100 pt-4 text-sm">
            <div className="flex items-start justify-between gap-3"><dt className="text-gray-500">Membership</dt><dd className="text-right font-medium capitalize text-earth-900">{user?.role}</dd></div>
            <div className="flex items-start justify-between gap-3"><dt className="text-gray-500">Email status</dt><dd className="text-right font-medium text-earth-900">{user?.is_verified ? "Verified" : "Not verified"}</dd></div>
            <div className="flex items-start justify-between gap-3"><dt className="text-gray-500">Joined</dt><dd className="text-right font-medium text-earth-900">{user?.created_at ? dateLabel(user.created_at) : "—"}</dd></div>
            {user?.dialect && <div className="flex items-start justify-between gap-3"><dt className="text-gray-500">Dialect</dt><dd className="text-right font-medium text-earth-900">{user.dialect}</dd></div>}
            {user?.county && <div className="flex items-start justify-between gap-3"><dt className="text-gray-500">County</dt><dd className="text-right font-medium text-earth-900">{user.county}</dd></div>}
          </dl>
          <p className="mt-4 rounded-xl bg-gray-50 p-3 text-xs leading-5 text-gray-600">Your account is checked against the archive service. Signing out here also updates the navigation and protected workspaces.</p>
        </article>

        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-earth-700">Your contribution record</p><h2 className="mt-1 text-xl font-bold text-earth-900">Work preserved under your account</h2></div><button type="button" onClick={() => { setLoading(true); void refresh(); api.get<MemberSummary>("/api/v1/community/me").then(setSummary).catch((cause) => setError(cause instanceof Error ? cause.message : "Could not refresh contributions.")).finally(() => setLoading(false)); }} className="shrink-0 rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-earth-900 hover:bg-gray-50">Refresh</button></div>
          {loading ? <p role="status" className="rounded-2xl border border-gray-200 p-5 text-sm text-gray-500">Loading your contribution record…</p> : error ? <div role="alert" className="rounded-2xl border border-amber-300 bg-amber-50 p-5"><p className="text-sm leading-6 text-amber-950">{error}</p><button type="button" onClick={() => { setLoading(true); setError(""); api.get<MemberSummary>("/api/v1/community/me").then(setSummary).catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load your contributions.")).finally(() => setLoading(false)); }} className="mt-3 text-sm font-semibold text-amber-950 underline underline-offset-4">Try again</button></div> : <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {[
                { label: "Total items", value: summary?.totals.total ?? 0 },
                { label: "Texts", value: summary?.totals.texts ?? 0 },
                { label: "Recordings", value: summary?.totals.recordings ?? 0 },
                { label: "In review", value: summary?.totals.pending ?? 0 },
                { label: "Approved", value: summary?.totals.approved ?? 0 },
                { label: "Not approved", value: summary?.totals.rejected ?? 0 },
              ].map((item) => <div key={item.label} className="rounded-xl border border-gray-200 bg-white p-4"><p className="text-xs text-gray-500">{item.label}</p><p className="mt-2 text-2xl font-bold tabular-nums text-earth-900">{item.value}</p></div>)}
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <h3 className="font-semibold text-earth-900">Recent contributions</h3>
              {summary?.recent.length ? <ul className="mt-3 divide-y divide-gray-100">{summary.recent.map((item) => <li key={item.id} className="flex flex-col gap-2 py-3 first:pt-0 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><p className="break-words font-medium text-gray-900">{item.title}</p><p className="mt-1 text-xs text-gray-500">{item.kind === "audio" ? "Audio recording" : item.genre || "Text"} · {dateLabel(item.created_at)}</p></div><span className={`w-fit shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${item.status === "approved" ? "bg-green-50 text-green-800" : item.status === "rejected" || item.status === "taken_down" ? "bg-gray-100 text-gray-700" : "bg-amber-50 text-amber-900"}`}>{statusNames[item.status] ?? item.status}</span></li>)}</ul> : <div className="mt-3 rounded-xl bg-gray-50 p-4"><p className="text-sm leading-6 text-gray-600">No contributions are recorded under this account yet. Your first approved contribution will be part of your lasting archive record.</p><Link href="/contribute" className="mt-3 inline-flex font-semibold text-earth-700 underline underline-offset-4">Add a Gĩkũyũ contribution</Link></div>}
            </div>
          </>}
        </div>
      </section>

      <section className="space-y-4">
        <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-earth-700">Continue from here</p><h2 className="mt-1 text-xl font-bold text-earth-900">Your archive workspace</h2></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link href="/contribute" className="group rounded-2xl border border-gray-200 p-5 transition hover:border-earth-300 hover:bg-earth-50"><span className="text-xs font-bold uppercase tracking-wide text-earth-700">Participate</span><h3 className="mt-2 font-semibold text-earth-900">Contribute material <span aria-hidden="true" className="transition group-hover:translate-x-1">→</span></h3><p className="mt-2 text-sm leading-6 text-gray-600">Submit text or audio, record consent and choose reuse permissions.</p></Link>
          <Link href="/transcribe" className="group rounded-2xl border border-gray-200 p-5 transition hover:border-earth-300 hover:bg-earth-50"><span className="text-xs font-bold uppercase tracking-wide text-earth-700">Improve</span><h3 className="mt-2 font-semibold text-earth-900">Transcribe and annotate <span aria-hidden="true">→</span></h3><p className="mt-2 text-sm leading-6 text-gray-600">Add time-aligned Gĩkũyũ transcripts and linguistic annotations to available recordings.</p></Link>
          <Link href="/saved" className="group rounded-2xl border border-gray-200 p-5 transition hover:border-earth-300 hover:bg-earth-50"><span className="text-xs font-bold uppercase tracking-wide text-earth-700">Return</span><h3 className="mt-2 font-semibold text-earth-900">Saved reading list <span aria-hidden="true">→</span></h3><p className="mt-2 text-sm leading-6 text-gray-600">{savedCount} saved {savedCount === 1 ? "reference" : "references"} on this device. This list is not yet synced across devices.</p></Link>
          {user && ["researcher", "reviewer", "admin"].includes(user.role) && <Link href="/researcher" className="group rounded-2xl border border-gray-200 p-5 transition hover:border-earth-300 hover:bg-earth-50"><span className="text-xs font-bold uppercase tracking-wide text-earth-700">Research</span><h3 className="mt-2 font-semibold text-earth-900">Researcher exports <span aria-hidden="true">→</span></h3><p className="mt-2 text-sm leading-6 text-gray-600">Create permission-filtered, source-traceable corpus exports.</p></Link>}
        </div>
      </section>
    </div>
  );
}

export default function AccountPage() {
  return <ProtectedRoute><AccountContent /></ProtectedRoute>;
}