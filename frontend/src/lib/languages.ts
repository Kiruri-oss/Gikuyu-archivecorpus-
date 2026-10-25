export interface AfricanLanguage {
  code: string;
  name: string;
  nativeName: string;
  family: string;
  region: string;
  description: string;
  searchTerms: string;
}

export const AFRICAN_LANGUAGES: AfricanLanguage[] = [
  { code: "ki", name: "Kikuyu / Gĩkũyũ", nativeName: "Gĩkũyũ", family: "Bantu", region: "East Africa · Kenya", description: "A central Kenyan language with living oral traditions, literature, vocabulary, history and contemporary creative work.", searchTerms: "Gĩkũyũ OR Kikuyu" },
  { code: "sw", name: "Swahili / Kiswahili", nativeName: "Kiswahili", family: "Bantu", region: "East Africa", description: "A major regional language with a long literary, educational, trade and public-life history.", searchTerms: "Kiswahili OR Swahili" },
  { code: "rw", name: "Kinyarwanda", nativeName: "Ikinyarwanda", family: "Bantu", region: "East Africa · Rwanda", description: "A national language of Rwanda with rich oral, written and contemporary cultural expression.", searchTerms: "Kinyarwanda OR Ikinyarwanda" },
  { code: "ha", name: "Hausa", nativeName: "Hausa", family: "Chadic", region: "West Africa", description: "A major West African language with extensive oral, written, educational and media traditions.", searchTerms: "Hausa language" },
  { code: "yo", name: "Yorùbá", nativeName: "Yorùbá", family: "Niger-Congo", region: "West Africa", description: "A language with major literary, artistic, philosophical and oral traditions.", searchTerms: "Yoruba OR Yorùbá" },
  { code: "ig", name: "Igbo", nativeName: "Asụsụ Igbo", family: "Niger-Congo", region: "West Africa · Nigeria", description: "A major language with extensive community, literary, musical and oral expression.", searchTerms: "Igbo language" },
  { code: "am", name: "Amharic", nativeName: "አማርኛ", family: "Semitic", region: "Horn of Africa · Ethiopia", description: "A major Ethiopian language with a long written tradition and distinctive script.", searchTerms: "Amharic OR አማርኛ" },
  { code: "so", name: "Somali", nativeName: "Soomaali", family: "Cushitic", region: "Horn of Africa", description: "A language with a particularly rich oral poetry tradition and a growing written and digital presence.", searchTerms: "Somali language" },
  { code: "om", name: "Oromo", nativeName: "Afaan Oromoo", family: "Cushitic", region: "Horn of Africa", description: "A major Cushitic language with oral, written, educational and cultural traditions.", searchTerms: "Oromo OR Afaan Oromoo" },
  { code: "zu", name: "Zulu", nativeName: "isiZulu", family: "Bantu", region: "Southern Africa", description: "A major Southern African language with extensive spoken, written, educational and media use.", searchTerms: "Zulu OR isiZulu" },
  { code: "xh", name: "Xhosa", nativeName: "isiXhosa", family: "Bantu", region: "Southern Africa", description: "A major Southern African language with literary, oral and contemporary digital expression.", searchTerms: "Xhosa OR isiXhosa" },
  { code: "sn", name: "Shona", nativeName: "chiShona", family: "Bantu", region: "Southern Africa · Zimbabwe", description: "A major language with rich oral traditions and modern literary, educational and media use.", searchTerms: "Shona OR chiShona" },
  { code: "ln", name: "Lingala", nativeName: "Lingála", family: "Bantu", region: "Central Africa", description: "A widely used Central African language strongly represented in music, urban culture and everyday life.", searchTerms: "Lingala OR Lingála" },
  { code: "lg", name: "Luganda", nativeName: "Luganda", family: "Bantu", region: "East Africa · Uganda", description: "A major Ugandan language with oral, written, cultural and broadcast traditions.", searchTerms: "Luganda language" },
  { code: "st", name: "Sesotho", nativeName: "Sesotho", family: "Bantu", region: "Southern Africa", description: "A Southern African language with established literary and educational traditions.", searchTerms: "Sesotho language" },
  { code: "tn", name: "Setswana", nativeName: "Setswana", family: "Bantu", region: "Southern Africa", description: "A Southern African language with a rich oral and written cultural heritage.", searchTerms: "Setswana language" },
  { code: "mg", name: "Malagasy", nativeName: "Malagasy", family: "Austronesian", region: "Indian Ocean · Madagascar", description: "The principal language of Madagascar, with distinctive oral, written and regional traditions.", searchTerms: "Malagasy language" },
  { code: "af", name: "Afrikaans", nativeName: "Afrikaans", family: "Indo-European", region: "Southern Africa", description: "A Southern African language with extensive written, spoken, educational and media resources.", searchTerms: "Afrikaans language" },
  { code: "bm", name: "Bambara", nativeName: "Bamanankan", family: "Mande", region: "West Africa · Mali", description: "A major Mande language with strong oral traditions and an important contemporary role in Mali.", searchTerms: "Bambara OR Bamanankan" },
  { code: "wo", name: "Wolof", nativeName: "Wolof", family: "Niger-Congo", region: "West Africa · Senegal and neighbouring countries", description: "A major West African language with strong oral, written, musical and public-life traditions.", searchTerms: "Wolof language" },
];

export function getAfricanLanguage(code: string): AfricanLanguage | undefined {
  return AFRICAN_LANGUAGES.find((language) => language.code === code);
}
