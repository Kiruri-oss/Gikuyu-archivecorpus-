import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://gikuyu-archivecorpus.vercel.app"),
  title: {
    default: "Gĩkũyũ Archive — Language, Memory, Community",
    template: "%s | Gĩkũyũ Archive",
  },
  description: "Explore public Gĩkũyũ and Kikuyu-language references. A transparent first step towards a community-governed language archive.",
  applicationName: "Gĩkũyũ Archive",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "Gĩkũyũ Archive",
    title: "Gĩkũyũ Archive — Language, Memory, Community",
    description: "Explore public Gĩkũyũ and Kikuyu-language references with source links and rights-aware guidance.",
    url: "https://gikuyu-archivecorpus.vercel.app",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#3d2f1f",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar />
        <main id="main-content" className="mx-auto min-h-[70vh] max-w-6xl px-4 py-2 sm:px-6">{children}</main>
        <footer className="mt-12 border-t border-gray-200 bg-gray-50">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-gray-600 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <p>Gĩkũyũ Archive · Public-source discovery, built with care.</p>
            <nav aria-label="Footer navigation" className="flex flex-wrap gap-x-5 gap-y-2">
              <Link href="/about">About</Link>
              <Link href="/privacy">Privacy</Link>
              <Link href="/takedown">Source concerns</Link>
              <a href="https://github.com/Kiruri-oss/Gikuyu-archivecorpus-" target="_blank" rel="noopener noreferrer">Open-source project ↗</a>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}
