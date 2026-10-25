export interface ArchiveLanguage {
  code: "ki";
  name: "Gĩkũyũ";
  nativeName: "Gĩkũyũ";
  family: "Bantu";
  region: "Central Kenya";
  description: string;
  searchTerms: string;
}

export const ARCHIVE_LANGUAGE: ArchiveLanguage = {
  code: "ki",
  name: "Gĩkũyũ",
  nativeName: "Gĩkũyũ",
  family: "Bantu",
  region: "Central Kenya",
  description: "A dedicated digital corpus for Gĩkũyũ vocabulary, proverbs, riddles, folklore, literature, oral histories, recordings, transcripts and annotated language data.",
  searchTerms: "Gĩkũyũ OR Kikuyu",
};

export function getAfricanLanguage(code: string): ArchiveLanguage | undefined {
  return code === "ki" ? ARCHIVE_LANGUAGE : undefined;
}
