import type { ToggleOption } from '../types';

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
    <div className="overflow-hidden rounded-2xl bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-indigo-500 p-6 text-white shadow-lg md:p-10" role="banner">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,2.6fr)_minmax(0,1.4fr)] xl:items-center">
        <div className="max-w-3xl space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-white/70">Public Sentiment Generator</p>
          <h2 className="text-3xl font-semibold md:text-4xl xl:text-[44px] xl:leading-tight">Stay ahead of emerging concerns in Baguio City</h2>
          <p className="text-sm text-white/85 md:text-base xl:text-lg">
            Analyze public conversations across Facebook and Reddit, classify sentiment automatically, and deliver actionable insights for rapid response teams.
          </p>
        </div>
        <div className="grid w-full gap-3 sm:grid-cols-2">
          <div className="rounded-2xl bg-white/10 backdrop-blur-sm p-5">
            <span className="text-xs font-semibold uppercase tracking-wide text-white/80">Monitoring Window</span>
            <p className="mt-1 text-lg font-semibold">{selectedWindowLabel}</p>
            <p className="text-sm text-white/70">{platformSummary.length} platform{platformSummary.length === 1 ? "" : "s"}</p>
          </div>
          <div className="rounded-2xl bg-white/10 backdrop-blur-sm p-5">
            <span className="text-xs font-semibold uppercase tracking-wide text-white/80">Focus Areas</span>
            <p className="mt-1 text-lg font-semibold">{focusSummary.length}</p>
            <p className="text-sm text-white/70">{focusSummaryLabel}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
