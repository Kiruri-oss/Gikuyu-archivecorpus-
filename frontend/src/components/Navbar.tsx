"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function Navbar() {
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    setIsAuthed(Boolean(localStorage.getItem("access_token")));
  }, []);

  return (
    <nav className="border-b bg-white sticky top-0 z-50" aria-label="Main navigation">
      <div className="max-w-6xl mx-auto flex items-center justify-between p-4">
        <Link href="/" className="text-xl font-bold text-earth-900">
          Gĩkũyũ Archive
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/search" className="hover:text-earth-500">Search</Link>
          <Link href="/contribute" className="hover:text-earth-500">Contribute</Link>
          <Link href="/researcher" className="hover:text-earth-500">Research</Link>
          {isAuthed ? (
            <button
              type="button"
              onClick={() => {
                localStorage.removeItem("access_token");
                window.location.href = "/";
              }}
              className="text-red-600"
            >
              Sign out
            </button>
          ) : (
            <Link href="/auth/login" className="hover:text-earth-500">Sign in</Link>
          )}
        </div>
      </div>
    </nav>
  );
}