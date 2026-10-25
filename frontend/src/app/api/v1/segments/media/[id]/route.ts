import { NextResponse } from "next/server";
import { parseWikiId } from "@/lib/wikimedia";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!parseWikiId(id)) {
    return NextResponse.json({ detail: "This is not a public reference record." }, { status: 400 });
  }
  return NextResponse.json([], {
    headers: { "Cache-Control": "public, max-age=300" },
  });
}
