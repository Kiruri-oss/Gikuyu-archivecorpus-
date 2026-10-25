"use client";

import { useEffect, useState } from "react";
import { hasSavedReference, removeSavedReference, saveReference } from "@/lib/saved-references";

interface BookmarkButtonProps {
  id: string;
  title: string;
  sourceName: string;
  sourceUrl: string;
  onChange?: (saved: boolean) => void;
}

export function BookmarkButton({ id, title, sourceName, sourceUrl, onChange }: BookmarkButtonProps) {
  const [saved, setSaved] = useState(false);

  useEffect(() => setSaved(hasSavedReference(id)), [id]);

  function toggleSaved() {
    const nextSaved = !saved;
    if (nextSaved) {
      saveReference({ id, title, source_name: sourceName, source_url: sourceUrl });
    } else {
      removeSavedReference(id);
    }
    setSaved(nextSaved);
    onChange?.(nextSaved);
  }

  return (
    <button type="button" onClick={toggleSaved} aria-pressed={saved} className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${saved ? "border-earth-900 bg-earth-900 text-white" : "border-gray-300 text-gray-700 hover:border-earth-500 hover:text-earth-900"}`}>
      {saved ? "✓ Saved" : "＋ Save for later"}
    </button>
  );
}
