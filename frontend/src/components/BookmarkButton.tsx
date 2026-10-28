"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";
import { hasSavedReference, removeSavedReference, saveReference } from "@/lib/saved-references";

interface BookmarkButtonProps {
  id: string;
  title: string;
  sourceName: string;
  sourceUrl: string;
  onChange?: (saved: boolean) => void;
}

type SavedApiItem = {
  id: string;
  reference_key: string;
  title: string;
  source_name: string;
  source_url: string;
  saved_at: string;
};

export function BookmarkButton({ id, title, sourceName, sourceUrl, onChange }: BookmarkButtonProps) {
  const { status } = useAuth();
  const [saved, setSaved] = useState(false);
  const [collectionId, setCollectionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setError("");
    if (status === "loading") return () => { cancelled = true; };
    if (status === "unavailable") {
      setLoading(false);
      setSaved(false);
      setCollectionId(null);
      setError("The account session could not be verified. Retry the session check before saving.");
      return () => { cancelled = true; };
    }
    if (status === "anonymous") {
      setSaved(hasSavedReference(id));
      setCollectionId(null);
      setLoading(false);
      return () => { cancelled = true; };
    }

    setLoading(true);
    api.get<{ items: SavedApiItem[] }>("/api/v1/community/saved-references")
      .then((result) => {
        if (cancelled) return;
        const item = result.items.find((row) => row.reference_key === id);
        setSaved(Boolean(item));
        setCollectionId(item?.id ?? null);
      })
      .catch(() => {
        if (!cancelled) setError("Your saved collection could not be checked. Try again.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [id, status]);

  async function toggleSaved() {
    setError("");
    setBusy(true);
    try {
      const nextSaved = !saved;
      if (status === "authenticated") {
        if (nextSaved) {
          const item = await api.post<SavedApiItem>("/api/v1/community/saved-references", {
            reference_key: id,
            title,
            source_name: sourceName,
            source_url: sourceUrl,
          });
          setCollectionId(item.id);
        } else {
          if (!collectionId) {
            const result = await api.get<{ items: SavedApiItem[] }>("/api/v1/community/saved-references");
            const item = result.items.find((row) => row.reference_key === id);
            if (item) await api.delete<void>(`/api/v1/community/saved-references/${encodeURIComponent(item.id)}`);
          } else {
            await api.delete<void>(`/api/v1/community/saved-references/${encodeURIComponent(collectionId)}`);
          }
          setCollectionId(null);
        }
      } else if (status === "anonymous") {
        if (nextSaved) saveReference({ id, title, source_name: sourceName, source_url: sourceUrl });
        else removeSavedReference(id);
      } else {
        throw new ApiError(0, "Sign-in status could not be verified. Try again before changing your collection.");
      }
      setSaved(nextSaved);
      onChange?.(nextSaved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Your saved collection could not be updated.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <button type="button" onClick={() => void toggleSaved()} disabled={loading || busy || status === "loading" || status === "unavailable"} aria-pressed={saved} className={`rounded-lg border px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${saved ? "border-earth-900 bg-earth-900 text-white" : "border-gray-300 text-gray-700 hover:border-earth-500 hover:text-earth-900"}`}>
        {loading || busy ? "Saving…" : saved ? "✓ Saved" : "＋ Save for later"}
      </button>
      {error && <p role="status" className="max-w-xs text-xs leading-5 text-amber-800">{error}</p>}
      {status === "anonymous" && !error && <p className="text-xs text-gray-500">Saved on this device. Sign in to sync across devices.</p>}
    </div>
  );
}
