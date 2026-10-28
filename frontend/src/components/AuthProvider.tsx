"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, ApiError } from "@/lib/api";
import { AUTH_EVENT, clearTokens, getAccessToken } from "@/lib/auth";

export type ArchiveUser = {
  id: string;
  email: string;
  full_name: string;
  role: "contributor" | "researcher" | "reviewer" | "admin" | string;
  institution?: string | null;
  dialect?: string | null;
  county?: string | null;
  bio?: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

export type AuthStatus = "loading" | "authenticated" | "anonymous" | "unavailable";

type AuthContextValue = {
  user: ArchiveUser | null;
  status: AuthStatus;
  refresh: () => Promise<void>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ArchiveUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refresh = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setStatus("anonymous");
      return;
    }

    setStatus((current) => current === "authenticated" ? current : "loading");
    try {
      const currentUser = await api.get<ArchiveUser>("/api/v1/auth/me");
      setUser(currentUser);
      setStatus("authenticated");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearTokens();
        setUser(null);
        setStatus("anonymous");
        return;
      }
      setUser(null);
      setStatus("unavailable");
    }
  }, []);

  const signOut = useCallback(() => {
    clearTokens();
    setUser(null);
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    void refresh();
    const onAuthChanged = () => { void refresh(); };
    const onStorage = (event: StorageEvent) => {
      if (event.key === "access_token" || event.key === "refresh_token" || event.key === null) {
        void refresh();
      }
    };
    window.addEventListener(AUTH_EVENT, onAuthChanged);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(AUTH_EVENT, onAuthChanged);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

  const value = useMemo(() => ({ user, status, refresh, signOut }), [user, status, refresh, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}