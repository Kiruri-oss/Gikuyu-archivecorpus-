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
    const load = async () => {
      try {
        const [m, s] = await Promise.all([
          api.get<Media>(`/api/v1/media/${id}`),
          api.get<Segment[]>(`/api/v1/segments/media/${id}`),
        ]);
        setMedia(m);
        setSegments(s);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Load failed");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id]);

  if (loading) return <p className="py-16 text-center text-gray-500">Loading...</p>;
  if (error || !media) return <p className="py-16 text-center text-red-600">Media not found.</p>;

  return (
    <div className="py-8 space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-earth-900">{media.title}</h1>
        <p className="text-gray-600 mt-1">
          {media.speaker ?? "Unknown speaker"} · {media.dialect ?? "Unknown dialect"}
          {media.genre ? ` · ${media.genre}` : ""}
        </p>
      </header>

      {media.file_url && <AudioPlayer src={media.file_url} title={media.title} />}

      <section>
        <h2 className="text-xl font-semibold mb-3">Segments</h2>
        {segments.length === 0 && <p className="text-gray-500">No segments yet.</p>}
        <ul className="space-y-3">
          {segments.map((segment) => (
            <li key={segment.id} className="p-4 border rounded-lg">
              <div className="text-xs text-gray-500 mb-2">
                {formatDuration(segment.start_seconds)} – {formatDuration(segment.end_seconds)}
                {segment.is_verified && <span className="ml-2 text-green-600">✓ verified</span>}
              </div>
              <p className="font-medium">{segment.transcript ?? "(no transcript)"}</p>
              {segment.translation && (
                <p className="text-sm text-gray-600 mt-1 italic">{segment.translation}</p>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}