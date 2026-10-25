import { NextRequest, NextResponse } from "next/server";
import { searchWikimedia } from "@/lib/wikimedia";

export async function GET(request: NextRequest) {
  const limitParam = Number(request.nextUrl.searchParams.get("limit") ?? "30");
  const limit = Number.isFinite(limitParam) ? Math.max(1, Math.min(50, Math.floor(limitParam))) : 30;
  const languageCode = (request.nextUrl.searchParams.get("lang") ?? "ki").trim().toLowerCase();
  if (languageCode !== "ki") {
    return NextResponse.json({ detail: "This archive is dedicated to Gĩkũyũ. Other language corpora are not part of this release." }, { status: 400 });
  }

  const backend = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  if (backend) {
    try {
      const upstream = await fetch(backend + "/api/v1/media?limit=" + limit, {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(12000),
      });
      const payload = await upstream.json().catch(() => ({ detail: "The archive returned an unreadable response." }));
      return NextResponse.json(payload, { status: upstream.status, headers: { "Cache-Control": "no-store" } });
    } catch {
      return NextResponse.json({ detail: "The Gĩkũyũ archive service could not be reached." }, { status: 502 });
    }
  }

  const query = (request.nextUrl.searchParams.get("q") ?? "Gĩkũyũ OR Kikuyu").trim().slice(0, 120);
  try {
    const media = await searchWikimedia(query, limit, "ki");
    return NextResponse.json(media, { headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Public archive discovery is temporarily unavailable.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}

export async function POST() {
  return NextResponse.json({
    detail: "Audio upload requires a connected archive backend. For large files, configure NEXT_PUBLIC_API_URL to point directly to the backend so the upload does not pass through the web proxy.",
  }, { status: 503 });
}
