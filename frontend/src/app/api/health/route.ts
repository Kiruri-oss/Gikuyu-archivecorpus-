import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const baseUrl = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  if (!baseUrl) {
    return NextResponse.json({
      status: "ok",
      service: "gikuyu-archive-web",
      mode: "public-source-discovery",
      persistence: "not-configured",
      timestamp: new Date().toISOString(),
    }, {
      headers: { "Cache-Control": "no-store" },
    });
  }

  try {
    const upstream = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
    });
    const data = await upstream.json().catch(() => ({}));
    return NextResponse.json({
      status: upstream.ok ? "ok" : "degraded",
      service: "gikuyu-archive-web",
      mode: upstream.ok ? "persistent-archive" : "backend-unavailable",
      persistence: upstream.ok && data.persistence === "connected" ? "connected" : "unavailable",
      backend: data.status ?? "unavailable",
      timestamp: new Date().toISOString(),
    }, {
      status: upstream.ok ? 200 : 503,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({
      status: "degraded",
      service: "gikuyu-archive-web",
      mode: "backend-unavailable",
      persistence: "unavailable",
      timestamp: new Date().toISOString(),
    }, {
      status: 503,
      headers: { "Cache-Control": "no-store" },
    });
  }
}
