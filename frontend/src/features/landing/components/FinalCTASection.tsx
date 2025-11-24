import Link from "next/link";

export function FinalCTASection() {
  return (
    <section className="border-t border-slate-100 bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-4xl px-4 py-12 text-center sm:px-6 lg:py-16 xl:px-0">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Start monitoring public sentiment in Baguio today
        </h2>
        <p className="mt-3 text-sm text-slate-600 sm:text-base">
          Use the console to explore a live prototype, generate sentiment snapshots, and understand how residents talk
          about issues that matter.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/app"
            className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-6 py-3 text-sm font-semibold text-white shadow-card shadow-hinaing-blue-600/30 transition hover:brightness-110 hover:shadow-subtle"
          >
            Open console
          </Link>
          <Link
            href="mailto:hello@hinaing.ai"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-violet-200 hover:text-slate-900"
          >
            Talk to us
          </Link>
        </div>
      </div>
    </section>
  );
}
