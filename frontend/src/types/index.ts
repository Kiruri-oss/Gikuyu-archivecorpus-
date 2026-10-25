export type UserRole = "contributor" | "researcher" | "reviewer" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution: string | null;
  dialect: string | null;
  county: string | null;
  bio: string | null;
  is_active: boolean;
  is_verified: boolean;
}

export interface Media {
  id: string;
  kind: "audio" | "video" | "image";
  title: string;
  speaker: string | null;
  dialect: string | null;
  county: string | null;
  genre: string | null;
  duration_seconds: number | null;
  license: string | null;
  lang_score: number | null;
  file_url?: string;
}

export interface Segment {
  id: string;
  media_id: string;
  start_seconds: number;
  end_seconds: number;
  transcript: string | null;
  translation: string | null;
  is_verified: boolean;
  confidence: number | null;
}

export type TakedownStatus = "received" | "under_review" | "actioned" | "rejected";

export interface Takedown {
  id: string;
  url: string;
  requester_name: string;
  status: TakedownStatus;
  created_at: string;
  actioned_at: string | null;
}
