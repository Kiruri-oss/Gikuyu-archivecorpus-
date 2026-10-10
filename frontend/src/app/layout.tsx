import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Gĩkũyũ Language Archive",
  description: "Community-controlled archive for Kikuyu audio and literature.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ki">
      <body className={inter.className}>
        <Navbar />
        <main className="max-w-6xl mx-auto p-4">{children}</main>
      </body>
    </html>
  );
}