import Link from "next/link";

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b bg-white" aria-label="Main navigation">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 p-4">
        <Link href="/" className="text-lg font-bold text-earth-900 sm:text-xl">
          Gĩkũyũ Archive
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/search" className="hover:text-earth-500">Search</Link>
          <Link href="/contribute" className="hover:text-earth-500">Contribute</Link>
          <Link href="/researcher" className="hover:text-earth-500">Research exports</Link>
        </div>
      </div>
    </nav>
  );
}
