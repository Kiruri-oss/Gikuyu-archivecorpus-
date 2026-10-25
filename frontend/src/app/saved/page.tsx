"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { readSavedReferences, removeSavedReference, type SavedReference } from "@/lib/saved-references";

export default function SavedPage() {
  const [items, setItems] = useState<SavedReference[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setItems(readSavedReferences());
    setReady(true);
  }, []);

  function remove(id: string) {
    setItems(removeSavedReference(id));
  }

  return (
    <section className="mx-auto max-w-4xl space-y-7 py-8 sm:py-12">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Your device, your list</p>
        <h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Saved references</h1>
        <p className="max-w-2xl leading-7 text-gray-600">Keep a reading list of public pages you want to revisit. This list is stored only in this browser on this device; it is not synced to an account or sent to the archive.</p>
      </header>
      {!ready ? <p role="status" className="text-gray-500">Loading your saved list…</p> : items.length === 0 ? <div className="rounded-2xl border border-dashed p-8 text-center"><h2 className="text-lg font-semibold text-earth-900">Nothing saved yet</h2><p className="mt-2 text-gray-600">When a result looks useful, save it here for later.</p><Link href="/search" className="mt-5 inline-flex rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white">Explore sources</Link></div> : <><div className="flex items-center justify-between text-sm text-gray-500"><p>{items.length} saved {items.length === 1 ? "reference" : "references"}</p><button type="button" onClick={() => { window.localStorage.removeItem("gikuyu-archive:saved-references:v1"); setItems([]); }} className="underline underline-offset-4">Clear reading list</button></div><ul className="space-y-3">{items.map((item) => <li key={item.id} className="flex flex-col gap-4 rounded-xl border border-gray-200 p-5 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0 space-y-1"><p className="text-xs font-semibold uppercase tracking-wide text-earth-700">{item.source_name}</p><h2 className="break-words font-semibold text-earth-900">{item.title}</h2><p className="break-all text-xs text-gray-500">{item.source_url}</p></div><div className="flex shrink-0 flex-wrap gap-3"><a href={item.source_url} target="_blank" rel="noopener noreferrer" className="rounded-lg bg-earth-900 px-3 py-2 text-sm font-semibold text-white">Open source ↗</a><button type="button" onClick={() => remove(item.id)} className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-700">Remove</button></div></li>)}</ul><p className="text-xs leading-6 text-gray-500">Saved items may be lost if you clear this browser's site data or switch devices. The list is limited to 200 items.</p></>}
    </section>
  );
}
