"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Media } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Media[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const data = query
          ? await api.get<{ media: Media[] }>(`/api/v1/search?q=${encodeURIComponent(query)}`)
          : { media: await api.get<Media[]>("/api/v1/media?limit=50") };
        if (!cancelled) setResults(data.media);
      } catch (err) {
        if (!cancelled) {
          setResults([]);
          setError(err instanceof ApiError ? err.message : "The archive could not load data. The backend may be unavailable.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query]);

  return (
    <div className="py-8 space-y-6">
      <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search Kikuyu words, phrases, speakers..." aria-label="Search archive" className="w-full p-4 border rounded-lg text-lg" />
      {loading && <p className="text-gray-500">Searching...</p>}
      {error && <div role="alert" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-950"><p className="font-semibold">Archive data is not connected</p><p className="mt-1 text-sm">{error}</p></div>}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {results.map((media) => <a key={media.id} href={`/media/${media.id}`} className="p-4 border rounded-lg hover:shadow-lg transition"><h3 className="font-semibold">{media.title}</h3><p className="text-sm text-gray-600">{media.speaker ?? "Unknown speaker"}</p><p className="text-xs text-gray-500">{media.dialect ?? "Unknown dialect"}</p></a>)}
      </div>
      {!loading && !error && results.length === 0 && <p className="text-gray-500">No results.</p>}
    </div>
  );
}
