"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Media } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Media[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      if (query.trim().length > 0 && query.trim().length < 2) {
        setResults([]);
        setError("");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError("");
      try {
        const data = query.trim()
          ? await api.get<{ media: Media[] }>(`/api/v1/search?q=${encodeURIComponent(query.trim())}`)
          : { media: await api.get<Media[]>("/api/v1/media?limit=30") };
        if (!cancelled) setResults(data.media);
      } catch (err) {
        if (!cancelled) {
          setResults([]);
          setError(err instanceof ApiError ? err.message : "Public sources could not be reached. Check your connection and try again.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, query.trim() ? 350 : 0);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query, retry]);

  return (
    <div className="space-y-7 py-8">
      <header className="max-w-3xl space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Public-source discovery</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Explore Gĩkũyũ resources</h1>
        <p className="leading-7 text-gray-600">Search reference pages from Kikuyu Wikipedia, Kikuyu Wiktionary and English Wikipedia. These are links to third-party material, not records held by this archive.</p>
      </header>
      <div className="space-y-2">
        <label htmlFor="archive-search" className="block text-sm font-medium text-gray-700">Search by word, phrase, topic or title</label>
        <input id="archive-search" type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try: Gĩkũyũ, culture, language…" aria-label="Search public reference sources" autoComplete="off" className="w-full rounded-xl border border-gray-300 bg-white p-4 text-base shadow-sm placeholder:text-gray-400 focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20" />
        <p className="text-xs text-gray-500">Enter at least two characters. Search requests are sent to public reference services; this site does not save your search history.</p>
      </div>
      <div className="flex min-h-6 items-center justify-between gap-3" aria-live="polite">
        {loading ? <p className="text-sm text-gray-500">Searching public sources…</p> : !error && <p className="text-sm text-gray-500">{results.length} {results.length === 1 ? "result" : "results"}</p>}
        {query && <button type="button" onClick={() => setQuery("")} className="text-sm font-medium text-earth-700 underline underline-offset-4">Clear search</button>}
      </div>
      {error && <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><p className="font-semibold">We couldn’t reach the public sources</p><p className="mt-1 text-sm leading-6">{error}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="mt-3 rounded-lg border border-amber-700 px-4 py-2 text-sm font-semibold hover:bg-amber-100">Try again</button></div>}
      {!loading && !error && query.trim().length === 1 && <p className="rounded-lg bg-gray-50 p-5 text-sm text-gray-600">Add one more character to start searching.</p>}
      {!loading && !error && query.trim().length !== 1 && results.length === 0 && <p className="rounded-lg border border-dashed p-8 text-center text-gray-600">No matching public reference pages were found. Try a broader spelling or a related term.</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((media) => (
          <article key={media.id} className="flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{media.source_name ?? media.dialect ?? "Public reference"}</p>
            <h2 className="mt-2 break-words text-lg font-semibold leading-6 text-earth-900">{media.title}</h2>
            {media.summary && <p className="mt-2 line-clamp-3 text-sm leading-6 text-gray-600">{media.summary.replace(/\s+/g, " ")}</p>}
            <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 pt-5 text-sm">
              <Link href={`/media/${encodeURIComponent(media.id)}`} className="font-semibold text-earth-700 underline underline-offset-4">View details</Link>
              {media.source_url && <a href={media.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-600 underline underline-offset-4">Original page ↗</a>}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
