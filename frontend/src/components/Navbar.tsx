"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";

const links = [
  { href: "/languages", label: "The corpus" },
  { href: "/search", label: "Explore" },
  { href: "/orthography", label: "Orthography" },
  { href: "/transcribe", label: "Transcribe" },
  { href: "/contribute", label: "Contribute" },
  { href: "/researcher", label: "Research" },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));
}

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, status, refresh, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  function logOut() {
    signOut();
    setMenuOpen(false);
    router.replace("/");
  }

  function navLinkClass(href: string) {
    return `rounded-lg px-3 py-2 text-sm font-medium transition ${isActive(pathname, href) ? "bg-earth-50 text-earth-900" : "text-gray-600 hover:bg-gray-50 hover:text-earth-900"}`;
  }

  const accountActions = (
    <>
      {status === "loading" && <span role="status" className="px-2 text-xs text-gray-500">Checking session…</span>}
      {status === "unavailable" && <button type="button" onClick={() => void refresh()} className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900">Session unverified · Retry</button>}
      {status === "anonymous" && <>
        <Link href="/auth/login" onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2 text-sm font-semibold text-earth-900 hover:bg-gray-100">Sign in</Link>
        <Link href="/auth/register" onClick={() => setMenuOpen(false)} className="rounded-lg bg-earth-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-earth-800">Join the archive</Link>
      </>}
      {status === "authenticated" && user && <>
        <Link href="/account" onClick={() => setMenuOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-earth-900 hover:bg-earth-50" aria-label="Open your account">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-earth-100 text-xs font-bold text-earth-900">{user.full_name.trim().slice(0, 1).toUpperCase() || "G"}</span>
          <span className="max-w-32 truncate">{user.full_name.split(" ")[0] || "My archive"}</span>
        </Link>
        <button type="button" onClick={logOut} className="rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-600 transition hover:border-gray-300 hover:text-earth-900">Sign out</button>
      </>}
    </>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/90 bg-white/95 shadow-sm shadow-gray-900/[0.02] backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8" aria-label="Main navigation">
        <Link href="/" className="flex min-w-0 items-center gap-3 text-earth-900" aria-label="Gĩkũyũ Archive home" onClick={() => setMenuOpen(false)}>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-earth-900 text-lg font-bold text-white" aria-hidden="true">Gĩ</span>
          <span className="min-w-0"><span className="block truncate text-base font-bold sm:text-lg">Gĩkũyũ Archive</span><span className="hidden text-xs text-gray-500 sm:block">Language · Memory · Community</span></span>
        </Link>

        <div className="hidden items-center gap-0.5 lg:flex">
          {links.map((link) => <Link key={link.href} href={link.href} aria-current={isActive(pathname, link.href) ? "page" : undefined} className={navLinkClass(link.href)}>{link.label}</Link>)}
        </div>

        <div className="hidden shrink-0 items-center gap-1 lg:flex">{accountActions}</div>

        <button type="button" className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg border border-gray-200 px-3 text-sm font-semibold text-earth-900 hover:bg-gray-50 lg:hidden" aria-expanded={menuOpen} aria-controls="responsive-navigation" onClick={() => setMenuOpen((open) => !open)}>
          <span>{menuOpen ? "Close" : "Menu"}</span><span aria-hidden="true">{menuOpen ? "×" : "☰"}</span>
        </button>
      </nav>

      {menuOpen && <div id="responsive-navigation" className="border-t border-gray-100 bg-white px-4 pb-4 pt-3 sm:px-6 lg:hidden">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {links.map((link) => <Link key={link.href} href={link.href} aria-current={isActive(pathname, link.href) ? "page" : undefined} onClick={() => setMenuOpen(false)} className={navLinkClass(link.href)}>{link.label}</Link>)}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-3">{accountActions}</div>
      </div>}
    </header>
  );
}