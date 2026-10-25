"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type LeaderboardEntry = {
  rank: number;
  display_name: string;
  approved_contributions: number;
  texts: number;
  recordings: number;
};

export function ContributorLeaderboard() {
  const [items, setItems] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.get<{ items: LeaderboardEntry[] }>("/api/v1/community/leaderboard?limit=10")
      .then((result) => { if (!cancelled) setItems(result.items); })
      .catch(() => { if (!cancelled) setFailed(true); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Community recognition</p><h2 className="mt-2 text-2xl font-bold text-earth-900">Gĩkũyũ contributors</h2><p className="mt-2 max-w-2xl leading-7 text-gray-600">Ranks are based on approved, publicly shared corpus records. Contributor identities are pseudonymous here; email addresses and full account names are never exposed.</p></div>
      </div>
      {loading ? <p role="status" className="mt-5 text-sm text-gray-500">Loading contributor totals…</p> : failed ? <p className="mt-5 rounded-lg bg-gray-50 p-4 text-sm text-gray-600">The leaderboard could not be loaded right now.</p> : items.length === 0 ? <p className="mt-5 rounded-lg bg-gray-50 p-4 text-sm leading-6 text-gray-600">No approved public contributions are counted yet. Contribute Gĩkũyũ material and help build the corpus.</p> : <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[28rem] text-left text-sm"><thead><tr className="border-b text-xs uppercase tracking-wide text-gray-500"><th className="py-3 pr-3">Rank</th><th className="py-3 pr-3">Contributor</th><th className="py-3 pr-3">Approved records</th><th className="py-3 pr-3">Texts</th><th className="py-3">Recordings</th></tr></thead><tbody>{items.map((item) => <tr key={item.display_name} className="border-b last:border-0"><td className="py-3 pr-3 font-semibold text-earth-900">{item.rank}</td><td className="py-3 pr-3">{item.display_name}</td><td className="py-3 pr-3 font-semibold">{item.approved_contributions}</td><td className="py-3 pr-3">{item.texts}</td><td className="py-3">{item.recordings}</td></tr>)}</tbody></table></div>}
    </section>
  );
}
