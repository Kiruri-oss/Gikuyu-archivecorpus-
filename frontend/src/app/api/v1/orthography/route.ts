import { NextResponse } from "next/server";

const SUGGESTIONS: Record<string, string> = {
  mucii: "mũciĩ",
  gikuyu: "gĩkũyũ",
  mundu: "mũndũ",
  andu: "andũ",
};

type OrthographyChange = {
  original: string;
  suggested: string;
  start: number;
  end: number;
};

function preserveCase(original: string, suggested: string): string {
  if (original === original.toLocaleUpperCase("en")) return suggested.toLocaleUpperCase("en");
  if (original.length > 0 && original[0] === original[0].toLocaleUpperCase("en")) {
    return suggested[0].toLocaleUpperCase("en") + suggested.slice(1);
  }
  return suggested;
}

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Send a valid JSON object containing text." }, { status: 400 });
  }

  const text = typeof payload === "object" && payload !== null && "text" in payload
    ? (payload as { text?: unknown }).text
    : undefined;
  if (typeof text !== "string" || !text.trim()) {
    return NextResponse.json({ detail: "Enter some Gĩkũyũ text to check." }, { status: 400 });
  }
  if (text.length > 20_000) {
    return NextResponse.json({ detail: "Text must be 20,000 characters or fewer." }, { status: 413 });
  }

  const pattern = /(?<![\p{L}\p{N}_])(mucii|gikuyu|mundu|andu)(?![\p{L}\p{N}_])/giu;
  const suggestions: OrthographyChange[] = [];
  const suggestedText = text.replace(pattern, (original, token: string, start: number) => {
    const suggested = preserveCase(original, SUGGESTIONS[token.toLowerCase()]);
    suggestions.push({ original, suggested, start, end: start + original.length });
    return suggested;
  });

  return NextResponse.json({
    original_text: text,
    suggested_text: suggestedText,
    suggestions,
    note: "Suggestions are not automatically saved. Confirm them with a fluent speaker before publishing.",
  }, { headers: { "Cache-Control": "no-store" } });
}
