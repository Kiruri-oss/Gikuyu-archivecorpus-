"use client";

import { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Takedown } from "@/types";

export default function TakedownAdminPage() {
  const [takedowns, setTakedowns] = useState<Takedown[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await api.get<Takedown[]>("/api/v1/takedowns");
      setTakedowns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const action = async (id: string) => {
    await api.post(`/api/v1/takedowns/${id}/action`, { admin_notes: "Actioned via admin UI" });
    await load();
  };

  return (
    <ProtectedRoute>
      <div className="py-8 space-y-6">
        <h1 className="text-2xl font-bold">Takedowns</h1>
        <p className="text-sm text-gray-600">
          Content removed within 72 hours of valid request. Tombstone preserved for audit.
        </p>

        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        <div className="space-y-3">
          {takedowns.map((t) => (
            <div key={t.id} className="p-4 border rounded-lg flex justify-between items-start gap-4">
              <div>
                <p className="font-medium break-all">{t.url}</p>
                <p className="text-sm text-gray-600">{t.requester_name}</p>
                <p className="text-xs text-gray-500">
                  Status: {t.status} · {formatDate(t.created_at)}
                </p>
              </div>
              {t.status === "received" && (
                <button
                  type="button"
                  onClick={() => action(t.id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm"
                >
                  Action
                </button>
              )}
            </div>
          ))}
          {!loading && takedowns.length === 0 && <p className="text-gray-500">No takedowns.</p>}
        </div>
      </div>
    </ProtectedRoute>
  );
}