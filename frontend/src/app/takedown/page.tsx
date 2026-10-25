import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Source concerns and removal",
  description: "How to raise concerns about a public reference linked from Gĩkũyũ Archive.",
};

export default function TakedownPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-7 py-10 sm:py-14">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Rights and corrections</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Source concerns and removal</h1><p className="leading-7 text-gray-600">The current service links to third-party reference pages. It does not host those pages or their media files.</p></header>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">If the original material should be removed</h2><p className="leading-7 text-gray-700">Contact the publisher or platform that hosts the material, using its own correction, privacy or copyright process. Removing a result from this search tool does not remove the original content from the internet.</p></section>
      <section className="space-y-3"><h2 className="text-xl font-semibold text-earth-900">If this site displays a broken or inappropriate result</h2><p className="leading-7 text-gray-700">You can report a technical issue through the project's GitHub repository. Please do not include private contact details, identity documents or other sensitive information in a public issue.</p><a href="https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/issues" target="_blank" rel="noopener noreferrer" className="inline-flex rounded-lg bg-earth-900 px-4 py-3 font-semibold text-white">Open project issues ↗</a></section>
      <section className="rounded-2xl border border-amber-300 bg-amber-50 p-5"><h2 className="font-semibold text-amber-950">Important limitation</h2><p className="mt-2 leading-7 text-amber-950">A dedicated private takedown intake and review queue is not yet configured. Do not treat this page as confirmation that a formal removal request has been received or actioned.</p></section>
      <Link href="/about" className="text-sm font-semibold text-earth-700 underline underline-offset-4">Read about the current project scope</Link>
    </article>
  );
}
