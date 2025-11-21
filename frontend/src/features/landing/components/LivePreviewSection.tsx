import { Card } from "@/components/ui/card";

export function LivePreviewSection() {
  return (
    <section id="live-preview" className="bg-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 xl:px-8">
        <div className="mb-8 grid gap-8 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:items-center">
          <div className="space-y-3">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
              A briefing that feels like a colleague, not a dashboard
            </h2>
            <p className="text-sm text-slate-600 sm:text-base">
              Inside the console, you can generate snapshots that summarise overall sentiment, highlight the most
              important issues, and flag potential misinformation for review. Each briefing is tuned to the time window
              and focus areas you care about.
            </p>
          </div>

          <Card className="rounded-3xl bg-white/90 p-5 shadow-card">
            <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
              <span className="rounded-full bg-slate-100 px-3 py-1 font-semibold uppercase tracking-wide text-slate-500">
                Sample briefing
              </span>
              <span>Generated for: last 48 hours</span>
            </div>

            <div className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Overall summary</p>
                <p className="mt-1 text-sm font-medium text-slate-900">
                  Public mood is strained around transport and water, but support remains strong for cleanup and
                  community initiatives.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center text-xs">
                <div className="rounded-xl bg-rose-50 p-3">
                  <p className="text-xl font-semibold text-rose-600">54%</p>
                  <p className="text-[11px] uppercase tracking-wide text-rose-700">Negative</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xl font-semibold text-slate-700">30%</p>
                  <p className="text-[11px] uppercase tracking-wide text-slate-600">Neutral</p>
                </div>
                <div className="rounded-xl bg-emerald-50 p-3">
                  <p className="text-xl font-semibold text-emerald-600">16%</p>
                  <p className="text-[11px] uppercase tracking-wide text-emerald-700">Positive</p>
                </div>
              </div>

              <div className="space-y-3 text-xs text-slate-700">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Actionable insights</p>
                <ul className="space-y-2 list-disc pl-4">
                  <li>
                    Consider a focused update on water scheduling in barangays with repeated outage complaints over the
                    last week.
                  </li>
                  <li>
                    Coordinate with traffic management for peak-hour interventions on Session Road and Marcos Highway.
                  </li>
                  <li>
                    Amplify positive narratives around cleanup drives to balance the current negative tilt.
                  </li>
                </ul>
              </div>

              <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                <span className="rounded-full bg-slate-100 px-3 py-1">Sources: Facebook, Reddit</span>
                <span className="rounded-full bg-slate-100 px-3 py-1">Configured by: your team</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
