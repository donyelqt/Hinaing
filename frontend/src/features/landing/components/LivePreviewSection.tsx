import { Card } from "@/components/ui/card";
import { Sparkles } from "lucide-react";

export function LivePreviewSection() {
  return (
    <section
      id="live-preview"
      className="relative overflow-hidden bg-slate-50 bg-grid-pattern py-24"
    >
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-bl from-violet-100/50 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-blue-100/50 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="grid gap-16 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:items-center">
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-700">
              <Sparkles className="h-3 w-3" />
              <span>Intelligent Analysis</span>
            </div>

            <h2 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl leading-tight">
              A briefing that feels like a colleague, <br className="hidden lg:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-blue-600">not a dashboard.</span>
            </h2>

            <p className="text-lg text-slate-600 leading-relaxed max-w-xl">
              Inside the console, you can generate snapshots that summarise overall sentiment, highlight the most
              important issues, and flag potential misinformation for review. Each briefing is tuned to the time window
              and focus areas you care about.
            </p>

            <div className="flex flex-wrap gap-3 text-xs font-medium text-slate-500">
              <span className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-blue-500" />
                Sources: Facebook & Reddit
              </span>
              <span className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-violet-500" />
                Window: last 48 hours
              </span>
            </div>
          </div>

          <div className="relative perspective-1000">
            <div
              className="pointer-events-none absolute -inset-10 rounded-[3rem] bg-gradient-to-br from-violet-500/20 via-blue-500/20 to-cyan-500/20 blur-2xl"
              aria-hidden="true"
            />

            {/* Preserved Card Content */}
            <Card className="relative rounded-3xl bg-white/95 p-5 shadow-card shadow-hinaing-blue-900/10 backdrop-blur-sm border-0 ring-1 ring-slate-100/50">
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
                  <span className="rounded-full bg-slate-100 px-3 py-1">Configured by: your team</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
