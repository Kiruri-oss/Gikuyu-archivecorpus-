import type { Media } from "@/types";

const SOURCES = [
  { host: "ki.wikipedia.org", label: "Kikuyu Wikipedia" },
  { host: "ki.wiktionary.org", label: "Kikuyu Wiktionary" },
  { host: "en.wikipedia.org", label: "English Wikipedia" },
] as const;

type WikiSearchItem = {
  pageid: number;
  title: string;
  snippet?: string;
};

type WikiSearchResponse = {
  query?: { search?: WikiSearchItem[] };
};

function makeId(host: string, pageId: number): string {
  return `${host}~${pageId}`;
}

export function parseWikiId(id: string): { host: string; pageId: number } | null {
  const match = /^(ki\.wikipedia\.org|ki\.wiktionary\.org|en\.wikipedia\.org)~(\d+)$/.exec(id);
  if (!match) return null;
  const pageId = Number(match[2]);
  if (!Number.isSafeInteger(pageId) || pageId < 1) return null;
  return { host: match[1], pageId };
}

export async function searchWikimedia(query: string, limit = 30): Promise<Media[]> {
  const cleanQuery = query.trim().slice(0, 120);
  const perSource = Math.max(1, Math.min(20, Math.ceil(limit / SOURCES.length)));
  const settled = await Promise.allSettled(SOURCES.map(async (source) => {
    const url = new URL(`https://${source.host}/w/api.php`);
    url.search = new URLSearchParams({
      action: "query",
      list: "search",
      srsearch: cleanQuery,
      srlimit: String(perSource),
      srnamespace: "0",
      format: "json",
      origin: "*",
    }).toString();
    const response = await fetch(url, {
      headers: { "User-Agent": "GikuyuLanguageArchive/1.0 (community language discovery)" },
      next: { revalidate: 300 },
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) throw new Error(`${source.host} returned HTTP ${response.status}`);
    const payload = await response.json() as WikiSearchResponse;
    return (payload.query?.search ?? []).map((item): Media => ({
      id: makeId(source.host, item.pageid),
      kind: "text",
      title: item.title,
      speaker: null,
      dialect: source.label,
      county: null,
      genre: "Public reference",
      duration_seconds: null,
      license: source.host === "en.wikipedia.org" ? "CC BY-SA (verify on source page)" : "Verify on source page",
      lang_score: null,
      summary: (item.snippet ?? "").replace(/<[^>]*>/g, "").replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&amp;/g, "&"),
      source_url: `https://${source.host}/?curid=${item.pageid}`,
      source_name: source.label,
    }));
  }));

  const results: Media[] = [];
  let successfulSources = 0;
  for (const result of settled) {
    if (result.status === "fulfilled") {
      successfulSources += 1;
      results.push(...result.value);
    }
  }
  if (successfulSources === 0) throw new Error("Public Wikimedia search is temporarily unavailable. Please try again shortly.");
  const unique = new Map<string, Media>();
  for (const item of results) unique.set(item.id, item);
  return [...unique.values()].slice(0, Math.max(1, Math.min(50, limit)));
}

export async function getWikimediaPage(id: string): Promise<(Media & { summary: string; source_url: string }) | null> {
  const parsed = parseWikiId(id);
  if (!parsed) return null;
  const url = new URL(`https://${parsed.host}/w/api.php`);
  url.search = new URLSearchParams({
    action: "query",
    pageids: String(parsed.pageId),
    prop: "extracts|info",
    exintro: "1",
    explaintext: "1",
    inprop: "url",
    format: "json",
    origin: "*",
  }).toString();
  const response = await fetch(url, {
    headers: { "User-Agent": "GikuyuLanguageArchive/1.0 (community language discovery)" },
    next: { revalidate: 900 },
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error("The source website could not be reached.");
  const payload = await response.json() as {
    query?: { pages?: Record<string, { pageid: number; title: string; extract?: string; fullurl?: string; missing?: boolean }> };
  };
  const page = payload.query?.pages?.[String(parsed.pageId)];
  if (!page || page.missing) return null;
  const source = SOURCES.find((item) => item.host === parsed.host);
  return {
    id,
    kind: "text",
    title: page.title,
    speaker: null,
    dialect: source?.label ?? parsed.host,
    county: null,
    genre: "Public reference",
    duration_seconds: null,
    license: "Check the source page for its applicable licence",
    lang_score: null,
    summary: page.extract ?? "",
    source_url: page.fullurl ?? `https://${parsed.host}/?curid=${parsed.pageId}`,
    source_name: source?.label ?? parsed.host,
  };
}
