"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";

type TextRecord = {
  id: string;
  title: string;
  body: string;
  source_url?: string | null;
  language_code: string;
  dialect?: string | null;
  genre?: string | null;
  license: string;
  author?: string | null;
  year?: number | null;
  allow_research_use: boolean;
  allow_ai_training: boolean;
  allow_commercial_use: boolean;
  created_at: string;
};

export default function TextRecordPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [record, setRecord] = useState<TextRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.get<TextRecord>(`/api/v1/text-records/${encodeURIComponent(id)}`)
      .then((value) => { if (!cancelled) setRecord(value); })
      .catch((cause) => { if (!cancelled) setError(cause instanceof Error ? cause.message : "The archived text could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  if (loading) return <div role="status" className="mx-auto max-w-3xl py-20 text-gray-500">Loading archived Gĩkũyũ text…</div>;
  if (error || !record) return <div className="mx-auto max-w-2xl space-y-4 py-20"><p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Record unavailable</p><h1 className="text-2xl font-bold text-earth-900">This archived text could not be loaded</h1><p className="leading-7 text-gray-600">{error || "The record may have been removed or may not be publicly approved."}</p><Link href="/search" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white">Back to corpus search</Link></div>;

  return (
    <article className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <Link href="/search" className="text-sm font-semibold text-earth-700 underline underline-offset-4">← Back to corpus search</Link>
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">Gĩkũyũ Archive Corpus · {record.genre ?? "Text record"}</p>
        <h1 className="break-words text-3xl font-bold leading-tight text-earth-900 sm:text-4xl">{record.title}</h1>
        <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-500">{record.author && <span>Author: {record.author}</span>}{record.year && <span>Year: {record.year}</span>}{record.dialect && <span>Dialect: {record.dialect}</span>}<span>Language: Gĩkũyũ</span></div>
      </header>
      <section className="rounded-2xl border border-gray-200 bg-white p-5 sm:p-8">
        <h2 className="text-lg font-semibold text-earth-900">Text</h2>
        <div className="mt-4 whitespace-pre-wrap break-words text-base leading-8 text-gray-800">{record.body}</div>
      </section>
      <section className="space-y-3 rounded-2xl bg-earth-50 p-5 sm:p-7">
        <h2 className="font-semibold text-earth-900">Record provenance and permissions</h2>
        <dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-gray-500">Licence</dt><dd className="mt-1 font-medium text-earth-900">{record.license}</dd></div><div><dt className="text-gray-500">Dialect</dt><dd className="mt-1 font-medium text-earth-900">{record.dialect ?? "Not specified"}</dd></div><div><dt className="text-gray-500">Research use</dt><dd className="mt-1 font-medium text-earth-900">{record.allow_research_use ? "Permitted" : "Not permitted"}</dd></div><div><dt className="text-gray-500">AI training</dt><dd className="mt-1 font-medium text-earth-900">{record.allow_ai_training ? "Permitted" : "Not permitted"}</dd></div><div><dt className="text-gray-500">Commercial use</dt><dd className="mt-1 font-medium text-earth-900">{record.allow_commercial_use ? "Permitted" : "Not permitted"}</dd></div></dl>
        {record.source_url && <a href={record.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white">Open original source ↗</a>}
      </section>
      <p className="text-xs leading-6 text-gray-500">Reuse only for purposes permitted by this record and its underlying source terms. If this record appears incorrect or should be removed, submit a request through the archive's correction and removal form.</p>
      <Link href="/takedown" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Request correction or removal</Link>
    </article>
  );
}
