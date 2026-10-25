import Link from "next/link";

const links = [
  { href: "/languages", label: "The Corpus" },
  { href: "/search", label: "Explore" },
  { href: "/orthography", label: "Orthography" },
  { href: "/contribute", label: "Contribute" },
  { href: "/login", label: "Account" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/80 bg-white/95 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:py-4" aria-label="Main navigation">
        <Link href="/" className="flex min-w-0 items-center gap-3 text-earth-900" aria-label="Gĩkũyũ Archive home">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-earth-900 text-lg font-bold text-white" aria-hidden="true">Gĩ</span>
          <span className="min-w-0"><span className="block truncate text-base font-bold sm:text-lg">Gĩkũyũ Archive</span><span className="hidden text-xs text-gray-500 sm:block">Gĩkũyũ language corpus</span></span>
        </Link>
        <div className="flex shrink-0 items-center gap-2 text-xs sm:gap-5 sm:text-sm">
          {links.map((link) => <Link key={link.href} href={link.href} className="font-medium text-gray-600 transition hover:text-earth-900">{link.label}</Link>)}
        </div>
      </nav>
    </header>
  );
}
