import type { ToggleOption } from '../types';
import { Sparkles } from 'lucide-react';

type HeroSectionProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
};

export function HeroSection({
  selectedWindowLabel,
  platformSummary,
  focusSummary,
  focusSummaryLabel,
}: HeroSectionProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-violet-600 via-indigo-600 to-blue-600 p-8 text-white shadow-xl shadow-indigo-500/20 md:p-12" role="banner">
      {/* Decorative background elements */}
      <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -bottom-24 -left-24 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />

      <div className="relative z-10 grid gap-10 xl:grid-cols-[1.8fr_1.2fr] xl:items-center">
        <div className="max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/90 backdrop-blur-md border border-white/10">
            <Sparkles className="h-3 w-3 text-yellow-300" />
            <span className="uppercase tracking-wide">AI-Powered Analysis</span>
          </div>

          <h2 className="text-4xl font-bold tracking-tight md:text-5xl xl:text-6xl leading-[1.1]">
            Pulse of the City
          </h2>

          <p className="text-lg text-blue-100/90 md:text-xl leading-relaxed max-w-2xl">
            Instantly decode public sentiment across Baguio City. Turn social chatter into actionable intelligence for rapid response.
          </p>
        </div>

        <div className="grid w-full gap-4 sm:grid-cols-2">
          <div className="group rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 p-6 transition-all hover:bg-white/15">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-200">Monitoring Window</span>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-2xl font-bold">{selectedWindowLabel}</p>
            </div>
            <p className="mt-1 text-sm text-blue-100/70 group-hover:text-blue-100 transition-colors">
              Across {platformSummary.length} platform{platformSummary.length === 1 ? "" : "s"}
            </p>
          </div>

          <div className="group rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 p-6 transition-all hover:bg-white/15">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-200">Focus Areas</span>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-2xl font-bold">{focusSummary.length}</p>
              <span className="text-sm font-medium text-blue-200">active</span>
            </div>
            <p className="mt-1 text-sm text-blue-100/70 group-hover:text-blue-100 transition-colors truncate">
              {focusSummaryLabel}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
