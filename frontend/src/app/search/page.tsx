"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Media } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Media[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = query
          ? await api.get<{ media: Media[] }>(`/api/v1/search?q=${encodeURIComponent(query)}`)
          : { media: await api.get<Media[]>("/api/v1/media?limit=50") };
        setResults(data.media);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="py-8 space-y-6">
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search Kikuyu words, phrases, speakers..."
        aria-label="Search archive"
        className="w-full p-4 border rounded-lg text-lg"
      />
      {loading && <p className="text-gray-500">Searching...</p>}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {results.map((media) => (
          <a
            key={media.id}
            href={`/media/${media.id}`}
            className="p-4 border rounded-lg hover:shadow-lg transition"
          >
            <h3 className="font-semibold">{media.title}</h3>
            <p className="text-sm text-gray-600">{media.speaker ?? "Unknown speaker"}</p>
            <p className="text-xs text-gray-500">{media.dialect ?? "Unknown dialect"}</p>
          </a>
        ))}
      </div>
      {!loading && results.length === 0 && <p className="text-gray-500">No results.</p>}
    </div>
  );
}