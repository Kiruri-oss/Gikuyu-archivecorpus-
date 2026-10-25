import { NextRequest, NextResponse } from "next/server";
import { searchWikimedia } from "@/lib/wikimedia";

export async function GET(request: NextRequest) {
  const query = (request.nextUrl.searchParams.get("q") ?? "").trim();
  const languageCode = (request.nextUrl.searchParams.get("lang") ?? "ki").trim().toLowerCase();
  if (languageCode !== "ki") {
    return NextResponse.json({ detail: "This archive is dedicated to Gĩkũyũ. Other language corpora are not part of this release." }, { status: 400 });
  }
  if (query.length < 2) return NextResponse.json({ detail: "Enter at least two characters to search." }, { status: 400 });
  if (query.length > 120) return NextResponse.json({ detail: "Search terms must be 120 characters or fewer." }, { status: 400 });

  const backend = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  if (backend) {
    try {
      const upstream = await fetch(backend + "/api/v1/search?q=" + encodeURIComponent(query) + "&limit=30", {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(12000),
      });
      const payload = await upstream.json().catch(() => ({ detail: "The archive search returned an unreadable response." }));
      return NextResponse.json(payload, { status: upstream.status, headers: { "Cache-Control": "no-store" } });
    } catch {
      return NextResponse.json({ detail: "The Gĩkũyũ archive search service could not be reached." }, { status: 502 });
    }
  }

  try {
    const media = await searchWikimedia(query, 30, "ki");
    return NextResponse.json({ query, language: "ki", media, source: "Wikimedia public reference discovery" }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Search is temporarily unavailable.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
