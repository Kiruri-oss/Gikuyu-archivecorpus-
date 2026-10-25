"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { BookmarkButton } from "@/components/BookmarkButton";
import type { Media } from "@/types";

type CorpusText = { id: string; title: string; body: string; source_url: string; language_code: string; dialect: string | null; license: string | null };
type CorpusSegment = { id: string; media_id: string; media_title: string; source_url: string; start_seconds: number; end_seconds: number; transcript: string | null; translation: string | null; dialect: string | null; license: string | null };
type SearchResponse = { query: string; source: string; media: Media[]; segments: CorpusSegment[]; texts: CorpusText[] };

function timecode(seconds: number) {
  const value = Math.max(0, Math.floor(seconds));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [media, setMedia] = useState<Media[]>([]);
  const [texts, setTexts] = useState<CorpusText[]>([]);
  const [segments, setSegments] = useState<CorpusSegment[]>([]);
  const [source, setSource] = useState("public_reference_discovery");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      if (query.trim().length === 1) {
        setMedia([]); setTexts([]); setSegments([]); setError(""); setLoading(false);
        return;
      }
      setLoading(true); setError("");
      try {
        const path = query.trim() ? `/api/v1/search?q=${encodeURIComponent(query.trim())}` : "/api/v1/search";
        const data = await api.get<SearchResponse>(path);
        if (!cancelled) {
          setMedia(data.media ?? []); setTexts(data.texts ?? []); setSegments(data.segments ?? []);
          setSource(data.source ?? "public_reference_discovery");
        }
      } catch (err) {
        if (!cancelled) {
          setMedia([]); setTexts([]); setSegments([]);
          setError(err instanceof ApiError ? err.message : "The search service could not be reached. Try again.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, query.trim() ? 350 : 0);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query, retry]);

  const total = media.length + texts.length + segments.length;
  const archive = source === "archive_corpus";

  return (
    <div className="space-y-8 py-8">
      <header className="max-w-3xl space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-earth-700">Gĩkũyũ Archive Corpus</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Search the Gĩkũyũ corpus</h1>
        <p className="leading-7 text-gray-600">Search approved texts, transcripts and media records when the archive backend is connected. Until then, this page searches public references and labels them as external discovery—not material hosted by the archive.</p>
      </header>
      <div className="space-y-2">
        <label htmlFor="archive-search" className="block text-sm font-medium text-gray-700">Search words, proverbs, stories, transcripts or titles</label>
        <input id="archive-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try Gĩkũyũ, mũciĩ, a proverb or story title…" autoComplete="off" className="w-full rounded-xl border border-gray-300 bg-white p-4 text-base shadow-sm focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20" />
        <p className="text-xs text-gray-500">Search terms are not saved as a history.</p>
      </div>
      <div className="flex items-center justify-between gap-3" aria-live="polite">
        {loading ? <p className="text-sm text-gray-500">Searching the archive and connected references…</p> : !error && <p className="text-sm text-gray-500">{total} {total === 1 ? "result" : "results"}</p>}
        {query && <button type="button" onClick={() => setQuery("")} className="text-sm font-medium text-earth-700 underline">Clear search</button>}
      </div>
      {!loading && !error && <p className={archive ? "rounded-xl border border-earth-500/30 bg-earth-50 p-4 text-sm text-earth-900" : "rounded-xl border bg-gray-50 p-4 text-sm text-gray-700"}>{archive ? "Archive corpus: approved records stored by this project." : "Public-reference discovery: results link to external publishers and are not stored in this archive."}</p>}
      {error && <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950"><p className="font-semibold">We couldn’t search the archive</p><p className="mt-1 text-sm">{error}</p><button type="button" onClick={() => setRetry((n) => n + 1)} className="mt-3 rounded-lg border border-amber-700 px-4 py-2 text-sm font-semibold">Try again</button></div>}
      {!loading && !error && query.trim().length === 1 && <p className="rounded-lg bg-gray-50 p-5 text-sm text-gray-600">Add one more character to search.</p>}

      {!loading && texts.length > 0 && <section className="space-y-4"><h2 className="text-xl font-semibold text-earth-900">Text corpus ({texts.length})</h2><div className="grid gap-4 sm:grid-cols-2">
        {texts.map((item) => <article key={item.id} className="flex flex-col rounded-xl border p-5"><p className="text-xs font-semibold uppercase text-earth-700">{item.dialect ?? item.language_code} {item.license ? `· ${item.license}` : ""}</p><h3 className="mt-2 text-lg font-semibold text-earth-900">{item.title}</h3><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-gray-600">{item.body.slice(0, 300)}{item.body.length > 300 ? "…" : ""}</p><div className="mt-auto flex flex-wrap gap-3 pt-4 text-sm"><a href={item.source_url} target="_blank" rel="noopener noreferrer" className="font-semibold text-earth-700 underline">Source ↗</a><BookmarkButton id={item.id} title={item.title} sourceName="Gĩkũyũ Archive Corpus" sourceUrl={item.source_url} /></div></article>)}
      </div></section>}

      {!loading && segments.length > 0 && <section className="space-y-4"><h2 className="text-xl font-semibold text-earth-900">Transcripts and annotations ({segments.length})</h2><div className="space-y-3">
        {segments.map((item) => <article key={item.id} className="rounded-xl border p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-earth-900">{item.media_title}</h3><p className="text-xs text-gray-500">{item.dialect ?? "Gĩkũyũ"} {item.license ? `· ${item.license}` : ""}</p></div><span className="text-xs text-gray-500">{timecode(item.start_seconds)}–{timecode(item.end_seconds)}</span></div>{item.transcript && <p className="mt-3 leading-7 text-gray-800">{item.transcript}</p>}{item.translation && <p className="mt-2 border-l-2 pl-3 text-sm leading-6 text-gray-600">{item.translation}</p>}<a href={item.source_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex text-sm font-semibold text-earth-700 underline">Original source ↗</a></article>)}
      </div></section>}

      {!loading && media.length > 0 && <section className="space-y-4"><h2 className="text-xl font-semibold text-earth-900">{archive ? "Audio and media" : "Public reference pages"} ({media.length})</h2><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {media.map((item) => <article key={item.id} className="flex flex-col rounded-xl border p-5 shadow-sm"><p className="text-xs font-semibold uppercase text-earth-700">{item.source_name ?? item.kind}</p><h3 className="mt-2 break-words text-lg font-semibold text-earth-900">{item.title}</h3>{item.summary && <p className="mt-2 line-clamp-3 text-sm leading-6 text-gray-600">{item.summary.replace(/\s+/g, " ")}</p>}{item.speaker && <p className="mt-2 text-sm text-gray-500">Speaker: {item.speaker}</p>}<div className="mt-auto flex flex-wrap gap-3 pt-5 text-sm"><Link href={`/media/${encodeURIComponent(item.id)}`} className="font-semibold text-earth-700 underline">View details</Link>{item.source_url && <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-600 underline">Original ↗</a>}{item.source_url && <BookmarkButton id={item.id} title={item.title} sourceName={item.source_name ?? "Gĩkũyũ Archive Corpus"} sourceUrl={item.source_url} />}</div></article>)}
      </div></section>}

      {!loading && !error && query.trim().length !== 1 && total === 0 && <p className="rounded-lg border border-dashed p-8 text-center text-gray-600">No matching approved corpus records or public references were found.</p>}
      <p className="border-t pt-5 text-xs leading-6 text-gray-500">Public-source discovery is not permission to redistribute or train AI. Review each source’s licence. Archive records are shown only after review.</p>
      <p className="text-sm text-gray-600">Check spellings with the <Link href="/orthography" className="font-semibold text-earth-700 underline">Gĩkũyũ orthography tool</Link>.</p>
    </div>
  );
}
