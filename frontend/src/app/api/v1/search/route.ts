import { NextRequest, NextResponse } from "next/server";
import { searchWikimedia } from "@/lib/wikimedia";

export async function GET(request: NextRequest) {
  const query = (request.nextUrl.searchParams.get("q") ?? "").trim();
  const languageCode = (request.nextUrl.searchParams.get("lang") ?? "ki").trim().toLowerCase();
  if (languageCode !== "ki") {
    return NextResponse.json({ detail: "This archive is dedicated to Gĩkũyũ. Other language corpora are not part of this release." }, { status: 400 });
  }
  if (query.length === 1) return NextResponse.json({ detail: "Enter at least two characters to search." }, { status: 400 });
  if (query.length > 120) return NextResponse.json({ detail: "Search terms must be 120 characters or fewer." }, { status: 400 });

  // Once the FastAPI service is provisioned, search the actual archive first.
  // Do not silently fall back to Wikimedia if the archive backend is configured
  // but unavailable; that would make a broken corpus look like an empty one.
  const archiveApiUrl = process.env.ARCHIVE_API_URL?.trim().replace(/\/+$/, "");
  if (archiveApiUrl) {
    try {
      const target = new URL("/api/v1/search", archiveApiUrl);
      if (query) target.searchParams.set("q", query);
      target.searchParams.set("limit", "30");
      const response = await fetch(target, {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });
      const payload = await response.json().catch(() => ({})) as { detail?: string; media?: unknown[]; segments?: unknown[]; texts?: unknown[]; query?: string };
      if (!response.ok) {
        return NextResponse.json({ detail: payload.detail ?? "The archive search service is unavailable." }, {
          status: response.status >= 500 ? 502 : response.status,
          headers: { "Cache-Control": "no-store" },
        });
      }
      return NextResponse.json({ ...payload, query: payload.query ?? query, source: "archive_corpus" }, {
        headers: { "Cache-Control": "no-store" },
      });
    } catch {
      return NextResponse.json({ detail: "The archive database could not be reached. Please try again shortly." }, {
        status: 502,
        headers: { "Cache-Control": "no-store" },
      });
    }
  }

  // Before the backend is connected, retain the honest public-reference
  // discovery fallback. These results are not records stored by the archive.
  const discoveryQuery = query || "Gĩkũyũ OR Kikuyu";
  try {
    const media = await searchWikimedia(discoveryQuery, 30, "ki");
    return NextResponse.json({
      query: discoveryQuery,
      language: "ki",
      media,
      segments: [],
      texts: [],
      source: "public_reference_discovery",
    }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Search is temporarily unavailable.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
