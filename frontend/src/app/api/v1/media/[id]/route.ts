import { NextResponse } from "next/server";
import { getWikimediaPage } from "@/lib/wikimedia";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    const media = await getWikimediaPage(id);
    if (!media) return NextResponse.json({ detail: "Source page not found." }, { status: 404 });
    return NextResponse.json(media, {
      headers: { "Cache-Control": "public, s-maxage=900, stale-while-revalidate=1800" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "The source page is temporarily unavailable.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
