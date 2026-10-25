"use client";

import { useState } from "react";

type OrthographyChange = {
  original: string;
  suggested: string;
  start: number;
  end: number;
};

type OrthographyResult = {
  original_text: string;
  suggested_text: string;
  suggestions: OrthographyChange[];
  note: string;
};

export default function OrthographyPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<OrthographyResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function checkOrthography() {
    if (!text.trim()) {
      setError("Enter some Gĩkũyũ text first.");
      setResult(null);
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/api/v1/orthography", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Could not check the text.");
      setResult(payload as OrthographyResult);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not check the text. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-7 py-8 sm:py-12">
      <header className="max-w-3xl space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Language tools</p>
        <h1 className="text-3xl font-bold leading-tight text-earth-900 sm:text-4xl">Gĩkũyũ orthography suggestions</h1>
        <p className="leading-7 text-gray-600">Check text for a small initial set of common spellings that may need the letters ĩ and ũ. Suggestions are shown for review; nothing is silently changed or saved.</p>
      </header>

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-7">
        <label htmlFor="orthography-input" className="block text-sm font-semibold text-earth-900">Your text</label>
        <textarea
          id="orthography-input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={20000}
          rows={8}
          placeholder="Paste Gĩkũyũ text here…"
          className="w-full rounded-xl border border-gray-300 p-4 leading-7 text-gray-900 outline-none focus:border-earth-500 focus:ring-2 focus:ring-earth-500/20"
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-gray-500">{text.length.toLocaleString()} / 20,000 characters · Text is not saved.</p>
          <button
            type="button"
            onClick={checkOrthography}
            disabled={loading || !text.trim()}
            className="rounded-lg bg-earth-900 px-5 py-3 font-semibold text-white transition hover:bg-earth-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Checking…" : "Suggest spelling"}
          </button>
        </div>
      </section>

      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</p>}

      {result && (
        <section className="space-y-4" aria-live="polite">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-earth-900">Suggestions</h2>
            <span className="rounded-full bg-earth-50 px-3 py-1 text-sm font-medium text-earth-900">{result.suggestions.length} found</span>
          </div>
          {result.suggestions.length === 0 ? (
            <p className="rounded-xl border border-gray-200 p-5 text-gray-700">No matches from the current suggestion list. This is not a complete grammar or spelling check.</p>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2">
              {result.suggestions.map((item, index) => (
                <li key={`${item.start}-${index}`} className="rounded-xl border border-gray-200 p-4">
                  <span className="font-mono text-gray-500 line-through">{item.original}</span>
                  <span className="mx-2 text-gray-400" aria-hidden="true">→</span>
                  <span className="font-semibold text-earth-900">{item.suggested}</span>
                </li>
              ))}
            </ul>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-earth-900">Original</h3>
              <p className="min-h-32 whitespace-pre-wrap break-words rounded-xl border border-gray-200 bg-gray-50 p-4 leading-7 text-gray-700">{result.original_text}</p>
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-earth-900">Suggested version</h3>
              <p className="min-h-32 whitespace-pre-wrap break-words rounded-xl border border-earth-500/30 bg-earth-50 p-4 leading-7 text-gray-800">{result.suggested_text}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => { setText(result.suggested_text); setResult(null); }} className="rounded-lg bg-earth-900 px-4 py-3 text-sm font-semibold text-white hover:bg-earth-800">Use suggested version in editor</button>
            <button type="button" onClick={() => { setResult(null); setError(""); }} className="rounded-lg border border-gray-300 px-4 py-3 text-sm font-semibold text-earth-900 hover:bg-gray-50">Dismiss suggestions</button>
          </div>
          <p className="text-sm leading-6 text-gray-500">{result.note} The current dictionary is intentionally small and must be expanded and reviewed by fluent Gĩkũyũ speakers.</p>
        </section>
      )}
    </div>
  );
}
