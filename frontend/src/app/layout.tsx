import Link from "next/link";
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/Navbar";
import { AuthProvider } from "@/components/AuthProvider";
import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://gikuyu-archivecorpus.vercel.app"),
  title: {
    default: "Gĩkũyũ Archive Corpus — Language, Memory, Research",
    template: "%s | Gĩkũyũ Archive",
  },
  description: "A growing Gĩkũyũ language corpus for words, proverbs, stories, oral histories, transcription, annotation and rights-aware language research.",
  applicationName: "Gĩkũyũ Archive",
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    siteName: "Gĩkũyũ Archive",
    title: "Gĩkũyũ Archive — Language, Memory, Community",
    description: "Explore and help build a searchable Gĩkũyũ corpus with provenance, transcription, annotation and permission-aware research datasets.",
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
        <AuthProvider>
          <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-earth-900">Skip to content</a>
          <ServiceWorkerRegister />
          <Navbar />
          <main id="main-content" className="mx-auto min-h-[70vh] max-w-7xl px-4 py-4 sm:px-6 lg:px-8">{children}</main>
          <footer className="mt-16 border-t border-gray-200 bg-gray-50">
            <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-8 text-sm text-gray-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
              <p>Gĩkũyũ Archive Corpus · Preserve the language. Build the record. Respect the people.</p>
              <nav aria-label="Footer navigation" className="flex flex-wrap gap-x-5 gap-y-2">
                <Link href="/about">About</Link>
                <Link href="/privacy">Privacy</Link>
                <Link href="/takedown">Source concerns</Link>
                <a href="https://github.com/Kiruri-oss/Gikuyu-archivecorpus-" target="_blank" rel="noopener noreferrer">Open-source project ↗</a>
              </nav>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}