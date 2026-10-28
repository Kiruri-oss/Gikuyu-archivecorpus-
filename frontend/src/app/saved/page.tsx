"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { readSavedReferences, removeSavedReference, type SavedReference } from "@/lib/saved-references";

type SavedApiItem = {
  id: string;
  reference_key: string;
  title: string;
  source_name: string;
  source_url: string;
  saved_at: string;
};

function fromApi(item: SavedApiItem): SavedReference {
  return {
    id: item.reference_key,
    collection_id: item.id,
    title: item.title,
    source_name: item.source_name,
    source_url: item.source_url,
    saved_at: item.saved_at,
  };
}

export default function SavedPage() {
  const { status } = useAuth();
  const [items, setItems] = useState<SavedReference[]>([]);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (status === "loading") return;
    setReady(false);
    setError("");
    setNotice("");

    if (status === "anonymous") {
      setItems(readSavedReferences());
      setReady(true);
      return;
    }
    if (status === "unavailable") {
      setItems(readSavedReferences());
      setError("Your account session could not be verified. Showing only this device's saved references.");
      setReady(true);
      return;
    }

    try {
      const response = await api.get<{ items: SavedApiItem[] }>("/api/v1/community/saved-references");
      const merged = new Map<string, SavedReference>(
        response.items.map((item) => {
          const saved = fromApi(item);
          return [saved.id, saved];
        }),
      );
      const localItems = readSavedReferences();
      let migrated = 0;

      for (const item of localItems) {
        if (merged.has(item.id)) continue;
        try {
          const saved = await api.post<SavedApiItem>("/api/v1/community/saved-references", {
            reference_key: item.id,
            title: item.title,
            source_name: item.source_name,
            source_url: item.source_url,
          });
          merged.set(saved.reference_key, fromApi(saved));
          migrated += 1;
        } catch {
          // Keep failed items in local storage and display them below.
          merged.set(item.id, item);
        }
      }

      const itemsSorted = [...merged.values()].sort((a, b) => b.saved_at.localeCompare(a.saved_at));
      setItems(itemsSorted);
      const localIds = new Set(localItems.map((item) => item.id));
      const failedLocal = itemsSorted.some((item) => localIds.has(item.id) && !item.collection_id);
      if (!failedLocal && localItems.length > 0) {
        window.localStorage.removeItem("gikuyu-archive:saved-references:v1");
      }
      if (migrated > 0) setNotice(`${migrated} device-saved ${migrated === 1 ? "reference has" : "references have"} been added to your account collection.`);
      if (failedLocal) setError("Some device-saved references could not be synced. They remain on this device; try again later.");
    } catch (cause) {
      setItems(readSavedReferences());
      setError(cause instanceof Error ? cause.message : "Your account collection could not be loaded.");
    } finally {
      setReady(true);
    }
  }, [status]);

  useEffect(() => { void load(); }, [load]);

  async function remove(item: SavedReference) {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      if (status === "authenticated" && item.collection_id) {
        await api.delete<void>(`/api/v1/community/saved-references/${encodeURIComponent(item.collection_id)}`);
      } else {
        removeSavedReference(item.id);
      }
      setItems((current) => current.filter((row) => row.id !== item.id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The reference could not be removed.");
    } finally {
      setBusy(false);
    }
  }

  async function clearCollection() {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const remoteItems = items.filter((item) => item.collection_id);
      await Promise.all(remoteItems.map((item) => api.delete<void>(`/api/v1/community/saved-references/${encodeURIComponent(item.collection_id!)}`)));
      window.localStorage.removeItem("gikuyu-archive:saved-references:v1");
      setItems([]);
      setNotice("Your saved reading list has been cleared.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The collection could not be completely cleared. Refresh and try again.");
      await load();
    } finally {
      setBusy(false);
    }
  }

  const signedIn = status === "authenticated";

  return (
    <section className="mx-auto max-w-5xl space-y-7 py-8 sm:py-12">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-3xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">{signedIn ? "Your member collection" : "Your device, your list"}</p>
          <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Saved references</h1>
          <p className="leading-7 text-gray-600">{signedIn
            ? "Keep a personal collection of useful Gĩkũyũ sources. Your saved references belong to your account and follow you across devices."
            : "Save useful source pages while exploring. When you sign in, this device's reading list can be brought into your account collection."}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link href="/search" className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-semibold text-gray-800 transition hover:border-earth-500">Explore material</Link>
          {signedIn && <Link href="/account" className="rounded-lg bg-earth-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-earth-800">My archive</Link>}
        </div>
      </header>

      {error && <p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950">{error} <button type="button" onClick={() => void load()} className="ml-1 font-semibold underline underline-offset-4">Retry</button></p>}
      {notice && <p role="status" className="rounded-xl border border-green-200 bg-green-50 p-4 text-sm leading-6 text-green-900">{notice}</p>}
      {!ready ? <p role="status" className="py-8 text-center text-gray-500">Loading your saved collection…</p> : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 px-6 py-12 text-center">
          <h2 className="text-lg font-semibold text-earth-900">Your reading list starts here</h2>
          <p className="mx-auto mt-2 max-w-lg leading-7 text-gray-600">Save a useful reference from the Explore pages and return to it when you need it. Members can keep their collection with their account.</p>
          <Link href="/search" className="mt-5 inline-flex rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Explore Gĩkũyũ sources</Link>
        </div>
      ) : <>
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-500">
          <p>{items.length} saved {items.length === 1 ? "reference" : "references"}{signedIn ? " in your account/device collection" : " on this device"}</p>
          <button type="button" disabled={busy} onClick={() => void clearCollection()} className="rounded-lg border border-gray-300 px-3 py-2 font-semibold text-gray-700 transition hover:border-gray-400 disabled:opacity-50">{busy ? "Updating…" : "Clear reading list"}</button>
        </div>
        <ul className="space-y-3">
          {items.map((item) => <li key={item.id} className="flex flex-col gap-4 rounded-2xl border border-gray-200 bg-white p-5 transition hover:border-gray-300 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 space-y-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{item.source_name}</p>
              <h2 className="break-words font-semibold text-earth-900">{item.title}</h2>
              <p className="break-all text-xs leading-5 text-gray-500">{item.source_url}</p>
              <p className="text-xs text-gray-400">{item.collection_id ? "Synced to account" : "Saved on this device"}</p>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="rounded-lg bg-earth-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-earth-800">Open source ↗</a>
              <button type="button" disabled={busy} onClick={() => void remove(item)} className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 transition hover:border-gray-400 disabled:opacity-50">Remove</button>
            </div>
          </li>)}
        </ul>
      </>}
    </section>
  );
}
