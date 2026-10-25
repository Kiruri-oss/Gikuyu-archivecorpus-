import { NextRequest, NextResponse } from "next/server";
import { searchWikimedia } from "@/lib/wikimedia";

export async function GET(request: NextRequest) {
  const query = (request.nextUrl.searchParams.get("q") ?? "").trim();
  if (query.length < 2) {
    return NextResponse.json({ detail: "Enter at least two characters to search." }, { status: 400 });
  }
  if (query.length > 120) {
    return NextResponse.json({ detail: "Search terms must be 120 characters or fewer." }, { status: 400 });
  }
  try {
    const media = await searchWikimedia(query, 30);
    return NextResponse.json({ query, media, source: "Wikimedia public search" }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Search is temporarily unavailable.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
