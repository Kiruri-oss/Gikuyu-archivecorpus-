import { NextRequest, NextResponse } from "next/server";
import { searchWikimedia } from "@/lib/wikimedia";

export async function GET(request: NextRequest) {
  const limitParam = Number(request.nextUrl.searchParams.get("limit") ?? "30");
  const limit = Number.isFinite(limitParam) ? Math.max(1, Math.min(50, Math.floor(limitParam))) : 30;
  const languageCode = (request.nextUrl.searchParams.get("lang") ?? "ki").trim().toLowerCase();
  if (languageCode !== "ki") {
    return NextResponse.json({ detail: "This archive is dedicated to Gĩkũyũ. Other language corpora are not part of this release." }, { status: 400 });
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
    detail: "Recording storage is not yet configured. This deployment currently supports searching public reference sources only; uploads are not saved. Do not submit recordings until persistent storage is enabled.",
  }, { status: 503 });
}
