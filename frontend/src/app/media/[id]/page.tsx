"use client";

import { use, useEffect, useState } from "react";
import { AudioPlayer } from "@/components/AudioPlayer";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/utils";
import type { Media, Segment } from "@/types";

export default function MediaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [media, setMedia] = useState<Media | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [m, s] = await Promise.all([
          api.get<Media>(`/api/v1/media/${encodeURIComponent(id)}`),
          api.get<Segment[]>(`/api/v1/segments/media/${encodeURIComponent(id)}`),
        ]);
        if (!cancelled) {
          setMedia(m);
          setSegments(s);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "The record could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [id]);

  if (loading) return <p className="py-16 text-center text-gray-500">Loading record...</p>;
  if (error || !media) return <div className="py-16 text-center space-y-3"><p className="text-red-600">{error ?? "Record not found."}</p><a className="text-earth-700 underline" href="/search">Return to search</a></div>;

  return (
    <article className="py-8 space-y-6">
      <header>
        <p className="text-sm text-gray-500">{media.source_name ?? "Gĩkũyũ Language Archive"}</p>
        <h1 className="text-3xl font-bold text-earth-900">{media.title}</h1>
        <p className="text-gray-600 mt-1">
          {media.speaker ?? "Speaker not listed"} · {media.dialect ?? "Dialect not specified"}
          {media.genre ? ` · ${media.genre}` : ""}
        </p>
      </header>

      {media.file_url && <AudioPlayer src={media.file_url} title={media.title} />}
      {media.summary && <section className="rounded-lg border bg-white p-5 space-y-2"><h2 className="font-semibold">About this source</h2><p className="whitespace-pre-wrap leading-7">{media.summary}</p></section>}
      {media.source_url && <p><a href={media.source_url} target="_blank" rel="noopener noreferrer" className="text-earth-700 underline">Open original source ↗</a></p>}
      <p className="text-sm text-gray-500">Licence: {media.license ?? "Not specified — check the original source before reuse."}</p>

      <section>
        <h2 className="text-xl font-semibold mb-3">Transcript segments</h2>
        {segments.length === 0 && <p className="text-gray-500">No community transcript segments have been added to this record.</p>}
        <ul className="space-y-3">
          {segments.map((segment) => (
            <li key={segment.id} className="p-4 border rounded-lg">
              <div className="text-xs text-gray-500 mb-2">
                {formatDuration(segment.start_seconds)} – {formatDuration(segment.end_seconds)}
                {segment.is_verified && <span className="ml-2 text-green-600">✓ verified</span>}
              </div>
              <p className="font-medium">{segment.transcript ?? "(no transcript)"}</p>
              {segment.translation && <p className="text-sm text-gray-600 mt-1 italic">{segment.translation}</p>}
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
