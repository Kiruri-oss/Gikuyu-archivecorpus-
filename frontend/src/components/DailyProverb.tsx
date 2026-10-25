"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

type TextRecord = {
  id: string;
  title: string;
  body: string;
  genre?: string | null;
  dialect?: string | null;
  source_url?: string | null;
  license?: string;
};

function dayNumber(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 0);
  return Math.floor((date.getTime() - start.getTime()) / 86400000);
}

export function DailyProverb() {
  const [record, setRecord] = useState<TextRecord | null>(null);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!API_URL) return;
    let cancelled = false;
    setLoading(true);
    api.get<TextRecord[]>("/api/v1/text-records?language_code=ki&limit=100")
      .then((records) => {
        const eligible = records.filter((item) => {
          const genre = (item.genre ?? "").toLowerCase();
          return genre.includes("proverb") || genre.includes("riddle");
        }).sort((a, b) => a.id.localeCompare(b.id));
        if (cancelled) return;
        setCount(eligible.length);
        if (eligible.length > 0) setRecord(eligible[dayNumber(new Date()) % eligible.length]);
      })
      .catch(() => {
        if (!cancelled) {
          setRecord(null);
          setLoadError(true);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <section className="rounded-2xl border border-earth-500/20 bg-earth-50 p-6 sm:p-8">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Daily Gĩkũyũ proverb or riddle</p>
      {record ? <>
        <h2 className="mt-3 text-2xl font-bold text-earth-900">{record.title}</h2>
        <p className="mt-3 whitespace-pre-wrap text-lg leading-8 text-gray-800">{record.body}</p>
        <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-600"><span>{record.genre ?? "Community record"}</span>{record.dialect && <span>Dialect: {record.dialect}</span>}{record.license && <span>Licence: {record.license}</span>}</div>
        <Link href={`/texts/${encodeURIComponent(record.id)}`} className="mt-5 inline-flex font-semibold text-earth-700 underline underline-offset-4">Read record details</Link>
      </> : <p className="mt-3 max-w-2xl leading-7 text-gray-700">{!API_URL ? "This feature will display a daily proverb or riddle from the verified corpus when the production archive API is connected." : loading ? "Finding an approved Gĩkũyũ proverb or riddle…" : loadError ? "The daily record could not be loaded. Try again when the archive is reachable." : count === 0 ? "No approved proverb or riddle is in the connected corpus yet. Contribute a Gĩkũyũ saying or riddle to help build this collection." : "The daily record could not be loaded. Try again when the archive is reachable."}</p>}
    </section>
  );
}
