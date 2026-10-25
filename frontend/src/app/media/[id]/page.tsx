"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Media } from "@/types";

export default function MediaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [media, setMedia] = useState<Media | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const record = await api.get<Media>(`/api/v1/media/${encodeURIComponent(id)}`);
        if (!cancelled) setMedia(record);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "The source page could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [id]);

  if (loading) return <div className="mx-auto max-w-3xl py-20" role="status"><p className="animate-pulse text-gray-500">Loading source details…</p></div>;
  if (error || !media) return <div className="mx-auto max-w-2xl space-y-4 py-20"><p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Source unavailable</p><h1 className="text-2xl font-bold text-earth-900">This reference could not be loaded</h1><p className="leading-7 text-gray-600">{error ?? "The source page may have been removed or moved."}</p><Link className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white" href="/search">Back to search</Link></div>;

  return (
    <article className="mx-auto max-w-3xl space-y-7 py-8 sm:py-12">
      <Link href="/search" className="text-sm font-semibold text-earth-700 underline underline-offset-4">← Back to search</Link>
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-earth-700">{media.source_name ?? media.dialect ?? "Public reference"}</p>
        <h1 className="break-words text-3xl font-bold leading-tight text-earth-900 sm:text-4xl">{media.title}</h1>
        <p className="text-sm text-gray-500">Third-party reference · Not hosted by this archive</p>
      </header>
      <section className="rounded-2xl border border-gray-200 bg-white p-5 sm:p-7">
        <h2 className="text-lg font-semibold text-earth-900">Source overview</h2>
        {media.summary ? <p className="mt-3 whitespace-pre-wrap leading-8 text-gray-700">{media.summary}</p> : <p className="mt-3 leading-7 text-gray-600">The publisher did not provide an introductory summary for this result.</p>}
      </section>
      <section className="space-y-3 rounded-2xl bg-earth-50 p-5 sm:p-7">
        <h2 className="font-semibold text-earth-900">Before you reuse this material</h2>
        <p className="leading-7 text-gray-700">The licence can vary by page and by included media. Check the original page for attribution requirements, restrictions and any third-party rights. Discovery here does not mean permission for redistribution or AI training.</p>
        {media.source_url && <a href={media.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white hover:bg-earth-700">Open original page <span className="ml-2" aria-hidden="true">↗</span></a>}
      </section>
      <p className="text-sm leading-6 text-gray-500">This version of Gĩkũyũ Archive indexes public reference pages only. Community recordings, verified transcripts and curated datasets are not hosted here yet.</p>
    </article>
  );
}
