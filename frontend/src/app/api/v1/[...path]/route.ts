import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = { params: Promise<{ path: string[] }> };

async function forward(request: NextRequest, context: RouteContext) {
  const baseUrl = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  if (!baseUrl) {
    return NextResponse.json({
      detail: "The persistent archive backend is not connected to this deployment. Your request was not saved.",
    }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }

  const { path } = await context.params;
  const safePath = path.map((part) => encodeURIComponent(part)).join("/");
  const target = `${baseUrl}/api/v1/${safePath}${request.nextUrl.search}`;
  const headers = new Headers();
  for (const name of ["accept", "content-type", "authorization"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  let body: ArrayBuffer | undefined;
  if (!["GET", "HEAD"].includes(request.method)) {
    const raw = await request.arrayBuffer();
    if (raw.byteLength > 2_200_000) {
      return NextResponse.json({
        detail: "This request is too large for the web proxy. Configure NEXT_PUBLIC_API_URL to point directly to the archive API for large media uploads.",
      }, { status: 413, headers: { "Cache-Control": "no-store" } });
    }
    body = raw;
  }

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    const responseHeaders = new Headers();
    for (const name of ["content-type", "content-disposition", "cache-control"]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    responseHeaders.set("Cache-Control", "no-store");
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return NextResponse.json({
      detail: "The archive backend could not be reached. Your request has not been confirmed.",
    }, { status: 502, headers: { "Cache-Control": "no-store" } });
  }
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
