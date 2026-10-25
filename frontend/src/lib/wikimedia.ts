import type { Media } from "@/types";
import { getAfricanLanguage } from "@/lib/languages";

type WikiSearchItem = { pageid: number; title: string; snippet?: string };
type WikiSearchResponse = { query?: { search?: WikiSearchItem[] } };

const ALLOWED_HOSTS = new Set(["ki.wikipedia.org", "en.wikipedia.org", "ki.wiktionary.org"]);

function makeId(host: string, pageId: number): string {
  return `${host}~${pageId}`;
}

export function parseWikiId(id: string): { host: string; pageId: number } | null {
  const match = /^([a-z]+\.wikipedia\.org|ki\.wiktionary\.org)~(\d+)$/.exec(id);
  if (!match || !ALLOWED_HOSTS.has(match[1])) return null;
  const pageId = Number(match[2]);
  if (!Number.isSafeInteger(pageId) || pageId < 1) return null;
  return { host: match[1], pageId };
}

function sourceLabel(host: string): string {
  if (host === "en.wikipedia.org") return "English Wikipedia (supporting reference)";
  if (host === "ki.wiktionary.org") return "Kikuyu Wiktionary";
  return "Gĩkũyũ Wikipedia";
}

export async function searchWikimedia(query: string, limit = 30, languageCode = "ki"): Promise<Media[]> {
  if (languageCode !== "ki") throw new Error("This archive currently supports Gĩkũyũ only.");
  const language = getAfricanLanguage("ki")!;
  const cleanQuery = query.trim().slice(0, 120);
  const perSource = Math.max(1, Math.min(20, Math.ceil(limit / 2)));
  const hosts = ["ki.wikipedia.org", "en.wikipedia.org", "ki.wiktionary.org"];

  const settled = await Promise.allSettled(hosts.map(async (host) => {
    const url = new URL(`https://${host}/w/api.php`);
    url.search = new URLSearchParams({
      action: "query", list: "search", srsearch: cleanQuery,
      srlimit: String(perSource), srnamespace: "0", format: "json", origin: "*",
    }).toString();
    const response = await fetch(url, {
      headers: { "User-Agent": "GikuyuArchiveCorpus/1.0 (Gĩkũyũ language discovery)" },
      next: { revalidate: 300 },
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) throw new Error(`${host} returned HTTP ${response.status}`);
    const payload = await response.json() as WikiSearchResponse;
    return (payload.query?.search ?? []).map((item): Media => ({
      id: makeId(host, item.pageid),
      kind: "text",
      title: item.title,
      speaker: null,
      dialect: host === "en.wikipedia.org" ? "Supporting English reference" : language.name,
      county: null,
      genre: "External public reference",
      duration_seconds: null,
      license: "Check the original source page for licence and reuse terms",
      lang_score: null,
      summary: (item.snippet ?? "").replace(/<[^>]*>/g, "").replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&amp;/g, "&"),
      source_url: `https://${host}/?curid=${item.pageid}`,
      source_name: sourceLabel(host),
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
  if (successfulSources === 0) throw new Error("Public reference search is temporarily unavailable. Please try again shortly.");
  const unique = new Map<string, Media>();
  for (const item of results) unique.set(item.id, item);
  return [...unique.values()].slice(0, Math.max(1, Math.min(50, limit)));
}

export async function getWikimediaPage(id: string): Promise<(Media & { summary: string; source_url: string }) | null> {
  const parsed = parseWikiId(id);
  if (!parsed) return null;
  const url = new URL(`https://${parsed.host}/w/api.php`);
  url.search = new URLSearchParams({
    action: "query", pageids: String(parsed.pageId), prop: "extracts|info",
    exintro: "1", explaintext: "1", inprop: "url", format: "json", origin: "*",
  }).toString();
  const response = await fetch(url, {
    headers: { "User-Agent": "GikuyuArchiveCorpus/1.0 (Gĩkũyũ language discovery)" },
    next: { revalidate: 900 },
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error("The source website could not be reached.");
  const payload = await response.json() as {
    query?: { pages?: Record<string, { pageid: number; title: string; extract?: string; fullurl?: string; missing?: boolean }> };
  };
  const page = payload.query?.pages?.[String(parsed.pageId)];
  if (!page || page.missing) return null;
  return {
    id, kind: "text", title: page.title, speaker: null,
    dialect: parsed.host === "en.wikipedia.org" ? "Supporting English reference" : "Gĩkũyũ",
    county: null, genre: "External public reference", duration_seconds: null,
    license: "Check the original source page for its applicable licence",
    lang_score: null, summary: page.extract ?? "",
    source_url: page.fullurl ?? `https://${parsed.host}/?curid=${parsed.pageId}`,
    source_name: sourceLabel(parsed.host),
  };
}
