import Link from "next/link";

export function FinalCTASection() {
  return (
    <section className="border-t border-slate-100 bg-gradient-to-b from-slate-50 to-white bg-grid-pattern">
      <div className="mx-auto max-w-6xl px-4 py-12 text-center sm:px-6 lg:py-16 xl:px-8">
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
            className="inline-flex items-center justify-center rounded-xl brand-gradient px-6 py-3 text-sm font-semibold text-white shadow-[0_8px_20px_-12px_rgb(var(--brand-from-rgb)_/_0.4)] transition hover:brightness-[1.04] hover:shadow-[0_12px_32px_-16px_rgb(var(--brand-from-rgb)_/_0.35)] active:scale-[0.98]"
          >
            Open console
          </Link>
          <Link
            href="mailto:hello@hinaing.ai"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-medium text-slate-700 transition hover:border-brand-to/40 hover:text-brand-from hover:shadow-[0_4px_12px_-4px_rgb(var(--brand-from-rgb)_/_0.12)]"
          >
            Talk to us
          </Link>
        </div>
      </div>
    </section>
  );
}
