import Link from "next/link";
import type { Media } from "@/types";

export function MediaCard({ media }: { media: Media }) {
  return (
    <Link
      href={`/media/${media.id}`}
      className="block p-4 border rounded-lg hover:shadow-lg transition"
    >
      <h3 className="font-semibold truncate">{media.title}</h3>
      <p className="text-sm text-gray-600 mt-1">{media.speaker ?? "Unknown speaker"}</p>
      <p className="text-xs text-gray-500 mt-1">
        {media.dialect ?? "Unknown dialect"}
        {media.genre ? ` · ${media.genre}` : ""}
      </p>
    </Link>
  );
}