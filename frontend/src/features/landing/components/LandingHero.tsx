import Link from "next/link";
import { Card } from "@/components/ui/card";

export function LandingHero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-hinaing-blue-50/70 to-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-16 sm:px-6 lg:flex-row lg:items-center lg:gap-16 lg:py-20 xl:px-8">
        <div className="space-y-6 lg:max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-hinaing-blue-100 bg-white/80 px-3 py-1 text-xs font-medium text-hinaing-blue-700 shadow-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-hinaing-gold" />
            <span>Built for Baguio City teams</span>
          </div>

          <div className="space-y-3">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
              Monitor public sentiment
              <span className="block text-hinaing-blue-700">before it becomes a crisis.</span>
            </h1>
            <p className="max-w-xl text-sm leading-relaxed text-slate-600 sm:text-base">
              Hinaing turns noisy Facebook and Reddit conversations into clear, actionable briefings so Baguio City
              decision-makers can respond faster and plan better.
            </p>
          </div>

          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <Link
              href="/app"
              className="inline-flex items-center justify-center rounded-xl bg-hinaing-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-card shadow-hinaing-blue-600/30 transition hover:bg-hinaing-blue-500 hover:shadow-subtle"
            >
              Open console
            </Link>
            <Link
              href="#live-preview"
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 px-5 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-hinaing-blue-200 hover:text-hinaing-blue-700"
            >
              View sample briefing
            </Link>
          </div>

          <p className="text-xs text-slate-400">
            No credit card required. Prototype tuned for Baguio City use cases.
          </p>
        </div>

        <div className="lg:flex-1">
          <Card className="relative mx-auto max-w-md rounded-3xl border border-hinaing-blue-100 bg-gradient-to-br from-white/90 to-hinaing-blue-50/70 p-6 shadow-card">
            <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
              <span className="inline-flex items-center gap-1 rounded-full bg-hinaing-blue-600/10 px-3 py-1 font-medium text-hinaing-blue-700">
                Live sentiment snapshot
              </span>
              <span>Baguio City · Last 24 hours</span>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Overall mood</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">Cautious but engaged</p>
                <p className="text-xs text-slate-500">
                  Infrastructure and transport issues dominate, but support remains high for cleanup and tourism efforts.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-xl bg-rose-50 px-2 py-3">
                  <p className="text-lg font-semibold text-rose-600">52%</p>
                  <p className="text-[11px] uppercase tracking-wide text-rose-700">Negative</p>
                </div>
                <div className="rounded-xl bg-slate-50 px-2 py-3">
                  <p className="text-lg font-semibold text-slate-700">31%</p>
                  <p className="text-[11px] uppercase tracking-wide text-slate-600">Neutral</p>
                </div>
                <div className="rounded-xl bg-emerald-50 px-2 py-3">
                  <p className="text-lg font-semibold text-emerald-600">17%</p>
                  <p className="text-[11px] uppercase tracking-wide text-emerald-700">Positive</p>
                </div>
              </div>

              <div className="mt-2 space-y-1 rounded-2xl bg-white/80 p-3 text-xs text-slate-600 shadow-inner">
                <p className="font-medium text-slate-900">Tonight&apos;s briefing highlights:</p>
                <ul className="mt-1 space-y-1 list-disc pl-4">
                  <li>Rising complaints on evening traffic in Session Road and Naguilian Road.</li>
                  <li>Persistent chatter on water reliability in several barangays.</li>
                  <li>Strong positive sentiment around weekend park cleanup efforts.</li>
                </ul>
              </div>

              <p className="pt-1 text-[11px] text-slate-400">
                Generated layout preview. Actual data and filters are available inside the console.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
