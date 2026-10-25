import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const baseUrl = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  if (!baseUrl) {
    return NextResponse.json({
      detail: "The takedown service is not connected to a persistent archive yet. Your request has not been submitted.",
    }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }

  let body: unknown;
  try {
    const raw = await request.text();
    if (raw.length > 12_000) {
      return NextResponse.json({ detail: "Request is too large." }, { status: 413 });
    }
    body = JSON.parse(raw);
  } catch {
    return NextResponse.json({ detail: "Send a valid JSON request." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${baseUrl}/api/v1/takedowns`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    const payload = await upstream.json().catch(() => ({ detail: "Archive service returned an unreadable response." }));
    return NextResponse.json(payload, {
      status: upstream.status,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({
      detail: "The archive service could not be reached. Your request has not been confirmed; please retry later.",
    }, { status: 502, headers: { "Cache-Control": "no-store" } });
  }
}
