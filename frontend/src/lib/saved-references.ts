export interface SavedReference {
  id: string;
  title: string;
  source_name: string;
  source_url: string;
  saved_at: string;
}

const STORAGE_KEY = "gikuyu-archive:saved-references:v1";

export function readSavedReferences(): SavedReference[] {
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is SavedReference =>
      item !== null &&
      typeof item === "object" &&
      typeof item.id === "string" &&
      typeof item.title === "string" &&
      typeof item.source_name === "string" &&
      typeof item.source_url === "string" &&
      typeof item.saved_at === "string"
    );
  } catch {
    return [];
  }
}

export function saveReference(reference: Omit<SavedReference, "saved_at">): SavedReference[] {
  const current = readSavedReferences().filter((item) => item.id !== reference.id);
  const next = [{ ...reference, saved_at: new Date().toISOString() }, ...current].slice(0, 200);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export function removeSavedReference(id: string): SavedReference[] {
  const next = readSavedReferences().filter((item) => item.id !== id);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export function hasSavedReference(id: string): boolean {
  return readSavedReferences().some((item) => item.id === id);
}
