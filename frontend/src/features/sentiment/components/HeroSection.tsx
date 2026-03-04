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

          <h2 className="text-3xl font-bold tracking-tight md:text-4xl leading-[1.15]">
            Autonomous Good Governance
          </h2>

          <p className="text-sm md:text-base text-blue-100/80 leading-relaxed max-w-xl">
            Agentic AI synthesizes novel search queries using domain context + temporal awareness,
            then deploys 5-signal credibility verification and ensemble sentiment analysis to
            quantify public concerns across Web, Facebook, and Reddit.
          </p>

          {/* Architecture Badges - Compact */}
          <div className="flex flex-wrap gap-1.5 text-[11px]">
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full text-white/90 border border-white/10">
              <span className="w-1 h-1 rounded-full bg-yellow-300 animate-pulse" />
              Agentic Queries
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full text-white/90 border border-white/10">
              <span className="w-1 h-1 rounded-full bg-emerald-300 animate-pulse" />
              5-Signal Credibility
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full text-white/90 border border-white/10">
              <span className="w-1 h-1 rounded-full bg-amber-300 animate-pulse" />
              Ensemble Sentiment
            </span>
          </div>
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
