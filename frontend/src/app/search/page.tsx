"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { BookmarkButton } from "@/components/BookmarkButton";
import { AFRICAN_LANGUAGES } from "@/lib/languages";
import type { Media } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("ki");
  const [results, setResults] = useState<Media[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("lang");
    if (requested && AFRICAN_LANGUAGES.some((item) => item.code === requested)) setLanguage(requested);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      if (query.trim().length === 1) {
        setResults([]);
        setError("");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError("");
      try {
        const suffix = `lang=${encodeURIComponent(language)}`;
        const data = query.trim()
          ? await api.get<{ media: Media[] }>(`/api/v1/search?q=${encodeURIComponent(query.trim())}&${suffix}`)
          : { media: await api.get<Media[]>(`/api/v1/media?limit=30&${suffix}`) };
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
  }, [query, language, retry]);

  const selectedLanguage = AFRICAN_LANGUAGES.find((item) => item.code === language) ?? AFRICAN_LANGUAGES[0];

  return (
    <div className="space-y-7 py-8">
      <header className="max-w-3xl space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-earth-700">African language discovery</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Explore language resources</h1>
        <p className="leading-7 text-gray-600">Search public reference pages for Gĩkũyũ and other African languages. Each result links to its original publisher; it is not a record hosted by this archive. Coverage varies by language and source.</p>
      </header>
      <div className="space-y-2">
        <label htmlFor="language-profile" className="block text-sm font-medium text-gray-700">Language profile</label>
        <select id="language-profile" value={language} onChange={(event) => setLanguage(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white p-3 text-base focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20">
          {AFRICAN_LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.name} — {item.nativeName}</option>)}
        </select>
        <p className="text-sm text-gray-600">{selectedLanguage.region} · {selectedLanguage.family}</p>
        <label htmlFor="archive-search" className="block pt-2 text-sm font-medium text-gray-700">Search by word, phrase, topic or title</label>
        <input id="archive-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Try a word or topic in ${selectedLanguage.name}…`} aria-label="Search public reference sources" autoComplete="off" className="w-full rounded-xl border border-gray-300 bg-white p-4 text-base shadow-sm placeholder:text-gray-400 focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20" />
        <p className="text-xs text-gray-500">Enter at least two characters. Search requests are sent to public reference services; this site does not save your search history.</p>
      </div>
      <div className="flex min-h-6 items-center justify-between gap-3" aria-live="polite">
        {loading ? <p className="text-sm text-gray-500">Searching {selectedLanguage.name} and English reference sources…</p> : !error && <p className="text-sm text-gray-500">{results.length} {results.length === 1 ? "result" : "results"}</p>}
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
            <div className="mt-auto flex flex-wrap items-center gap-3 pt-5 text-sm">
              <Link href={`/media/${encodeURIComponent(media.id)}`} className="font-semibold text-earth-700 underline underline-offset-4">View details</Link>
              {media.source_url && <a href={media.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-600 underline underline-offset-4">Original ↗</a>}
              {media.source_url && <BookmarkButton id={media.id} title={media.title} sourceName={media.source_name ?? media.dialect ?? "Public reference"} sourceUrl={media.source_url} />}
            </div>
          </article>
        ))}
      </div>
      <p className="border-t pt-5 text-xs leading-6 text-gray-500">These profiles are an initial directory, not a claim of equal coverage or community approval. A true African language library requires local contributors, curated sources, consent and licensing metadata.</p>
    </div>
  );
}
