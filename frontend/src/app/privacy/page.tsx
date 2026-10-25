import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy",
  description: "What the current Gĩkũyũ Archive discovery service does and does not collect.",
};

export default function PrivacyPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-7 py-10 sm:py-14">
      <header className="space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-earth-700">Plain-language notice</p><h1 className="text-3xl font-bold text-earth-900 sm:text-4xl">Privacy</h1><p className="leading-7 text-gray-600">This notice describes the current public-source discovery version of Gĩkũyũ Archive, not a future archive platform.</p></header>
      <section className="space-y-2"><h2 className="text-lg font-semibold text-earth-900">Searches</h2><p className="leading-7 text-gray-700">Search terms are sent by the server to the selected public Wikimedia services to retrieve results. The application does not intentionally save a personal search history or create user profiles.</p></section>
      <section className="space-y-2"><h2 className="text-lg font-semibold text-earth-900">Technical data</h2><p className="leading-7 text-gray-700">The hosting provider and network infrastructure may process technical request information, such as IP address, browser details and request timestamps, for delivery, security and operational purposes under their own policies. This application does not control all provider-level logging or retention.</p></section>
      <section className="space-y-2"><h2 className="text-lg font-semibold text-earth-900">Accounts and contributions</h2><p className="leading-7 text-gray-700">This version does not offer active account registration, audio upload, transcript submission or dataset download. Do not send recordings or personal information through this site expecting them to be stored in an archive.</p></section>
      <section className="space-y-2"><h2 className="text-lg font-semibold text-earth-900">Third-party sources</h2><p className="leading-7 text-gray-700">Opening an original source takes you to a third-party service with its own privacy and content policies. Review that service&apos;s terms directly.</p></section>
      <section className="space-y-2"><h2 className="text-lg font-semibold text-earth-900">Future changes</h2><p className="leading-7 text-gray-700">Before accounts, contributions or persistent archive records are enabled, the project will need a fuller privacy notice, data-retention rules, access controls and workable correction and deletion processes.</p></section>
      <p className="border-t pt-5 text-sm leading-6 text-gray-500">This is an operational notice, not legal advice or a claim that every third-party processing activity is controlled by this project.</p>
    </article>
  );
}
