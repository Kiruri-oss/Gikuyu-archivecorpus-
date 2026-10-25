"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { BookmarkButton } from "@/components/BookmarkButton";
import type { Media } from "@/types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

type CorpusText = {
  id: string;
  title: string;
  body: string;
  source_url?: string | null;
  language_code?: string;
  dialect?: string | null;
  genre?: string | null;
  license?: string | null;
};

type CorpusMedia = Partial<Media> & { id: string; title: string };
type CorpusSegment = {
  id: string;
  media_id?: string;
  title?: string;
  transcript?: string | null;
  translation?: string | null;
  start_seconds?: number;
  end_seconds?: number;
};

type CorpusSearchResponse = {
  media?: CorpusMedia[];
  texts?: CorpusText[];
  segments?: CorpusSegment[];
};

type ArchiveResult = Media & {
  resultType: "reference" | "archive-text" | "archive-media" | "transcript";
  targetHref: string;
};

function normaliseMedia(item: CorpusMedia): ArchiveResult {
  return {
    id: item.id,
    kind: item.kind ?? "audio",
    title: item.title,
    speaker: item.speaker ?? null,
    dialect: item.dialect ?? "Gĩkũyũ",
    county: item.county ?? null,
    genre: item.genre ?? null,
    duration_seconds: item.duration_seconds ?? null,
    license: item.license ?? null,
    lang_score: item.lang_score ?? null,
    file_url: item.file_url,
    summary: item.summary,
    source_url: item.source_url,
    source_name: "Gĩkũyũ Archive Corpus",
    resultType: "archive-media",
    targetHref: `/media/${encodeURIComponent(item.id)}`,
  };
}

function normaliseText(item: CorpusText): ArchiveResult {
  return {
    id: item.id,
    kind: "text",
    title: item.title,
    speaker: null,
    dialect: item.dialect ?? "Gĩkũyũ",
    county: null,
    genre: item.genre ?? "Archived text",
    duration_seconds: null,
    license: item.license ?? null,
    lang_score: null,
    summary: item.body,
    source_url: item.source_url ?? undefined,
    source_name: "Gĩkũyũ Archive Corpus",
    resultType: "archive-text",
    targetHref: `/texts/${encodeURIComponent(item.id)}`,
  };
}

function normaliseSegment(item: CorpusSegment): ArchiveResult {
  const time = typeof item.start_seconds === "number" ? ` · ${item.start_seconds.toFixed(1)}s` : "";
  return {
    id: item.id,
    kind: "text",
    title: item.title ?? "Gĩkũyũ transcript segment",
    speaker: null,
    dialect: "Gĩkũyũ",
    county: null,
    genre: "Transcript",
    duration_seconds: null,
    license: null,
    lang_score: null,
    summary: [item.transcript, item.translation].filter(Boolean).join("\nTranslation: ") + time,
    source_name: "Gĩkũyũ transcript",
    resultType: "transcript",
    targetHref: item.media_id ? `/media/${encodeURIComponent(item.media_id)}` : "/research",
  };
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ArchiveResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

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
        if (API_URL) {
          if (query.trim()) {
            const data = await api.get<CorpusSearchResponse>(`/api/v1/search?q=${encodeURIComponent(query.trim())}`);
            const archived = [
              ...(data.texts ?? []).map(normaliseText),
              ...(data.media ?? []).map(normaliseMedia),
              ...(data.segments ?? []).map(normaliseSegment),
            ];
            if (!cancelled) setResults(archived);
          } else {
            const [media, texts] = await Promise.all([
              api.get<CorpusMedia[]>("/api/v1/media?limit=30"),
              api.get<CorpusText[]>("/api/v1/text-records?language_code=ki&limit=30"),
            ]);
            if (!cancelled) setResults([...texts.map(normaliseText), ...media.map(normaliseMedia)]);
          }
        } else {
          const data: CorpusSearchResponse = query.trim()
            ? await api.get<CorpusSearchResponse>(`/api/v1/search?q=${encodeURIComponent(query.trim())}`)
            : { media: await api.get<Media[]>("/api/v1/media?limit=30") };
          if (!cancelled) {
            if (query.trim() && (data.texts !== undefined || data.segments !== undefined)) {
              setResults([
                ...(data.texts ?? []).map(normaliseText),
                ...(data.media ?? []).map(normaliseMedia),
                ...(data.segments ?? []).map(normaliseSegment),
              ]);
            } else {
              setResults((data.media ?? []).map((item) => ({
                ...item as Media,
                resultType: "reference",
                targetHref: `/media/${encodeURIComponent(item.id)}`,
              })));
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          setResults([]);
          setError(err instanceof ApiError ? err.message : "Gĩkũyũ sources could not be reached. Check your connection and try again.");
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
        <p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Gĩkũyũ Archive Corpus</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Explore Gĩkũyũ material</h1>
        <p className="leading-7 text-gray-600">Search archived Gĩkũyũ texts, recordings and transcripts when the corpus API is connected. Until then, search the currently connected Gĩkũyũ public references. Reference results link to their original sources and are not stored by this archive.</p>
      </header>
      <div className="space-y-2">
        <label htmlFor="archive-search" className="block text-sm font-medium text-gray-700">Search Gĩkũyũ words, proverbs, stories, transcripts or titles</label>
        <input id="archive-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try Gĩkũyũ, Kikuyu, mũciĩ, proverb…" aria-label="Search Gĩkũyũ corpus" autoComplete="off" className="w-full rounded-xl border border-gray-300 bg-white p-4 text-base shadow-sm placeholder:text-gray-400 focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20" />
        <p className="text-xs text-gray-500">Enter at least two characters. Search requests are not saved as personal search history.</p>
      </div>
      <div className="flex min-h-6 items-center justify-between gap-3" aria-live="polite">
        {loading ? <p className="text-sm text-gray-500">Searching Gĩkũyũ material…</p> : !error && <p className="text-sm text-gray-500">{results.length} {results.length === 1 ? "result" : "results"}</p>}
        {query && <button type="button" onClick={() => setQuery("")} className="text-sm font-medium text-earth-700 underline underline-offset-4">Clear search</button>}
      </div>
      {error && <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><p className="font-semibold">We couldn’t reach the Gĩkũyũ archive sources</p><p className="mt-1 text-sm leading-6">{error}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="mt-3 rounded-lg border border-amber-700 px-4 py-2 text-sm font-semibold hover:bg-amber-100">Try again</button></div>}
      {!loading && !error && query.trim().length === 1 && <p className="rounded-lg bg-gray-50 p-5 text-sm text-gray-600">Add one more character to start searching.</p>}
      {!loading && !error && query.trim().length !== 1 && results.length === 0 && <p className="rounded-lg border border-dashed p-8 text-center text-gray-600">No matching Gĩkũyũ records were found. Try a different spelling or related Gĩkũyũ term.</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((item) => (
          <article key={`${item.resultType}:${item.id}`} className="flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{item.source_name ?? item.dialect ?? "Gĩkũyũ record"}</p>
            <h2 className="mt-2 break-words text-lg font-semibold leading-6 text-earth-900">{item.title}</h2>
            {item.summary && <p className="mt-2 line-clamp-4 whitespace-pre-line text-sm leading-6 text-gray-600">{item.summary.replace(/\s+/g, " ")}</p>}
            {item.license && <p className="mt-2 text-xs text-gray-500">Licence: {item.license}</p>}
            <div className="mt-auto flex flex-wrap items-center gap-3 pt-5 text-sm">
              <Link href={item.targetHref} className="font-semibold text-earth-700 underline underline-offset-4">{item.resultType === "archive-text" ? "Read archived text" : item.resultType === "transcript" ? "Open recording" : "View details"}</Link>
              {item.source_url && <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-600 underline underline-offset-4">Original ↗</a>}
              {item.source_url && <BookmarkButton id={item.id} title={item.title} sourceName={item.source_name ?? item.dialect ?? "Gĩkũyũ reference"} sourceUrl={item.source_url} />}
            </div>
          </article>
        ))}
      </div>
      <p className="border-t pt-5 text-xs leading-6 text-gray-500">The objective is a persistent Gĩkũyũ corpus, not a wrapper around external websites. Archived records, contributions, transcripts and annotations appear here when the production archive API and database are connected.</p>
    </div>
  );
}
