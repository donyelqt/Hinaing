import type { ToggleOption } from '../types';

type HeroSectionProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
};

export function HeroSection(_props: HeroSectionProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-6" role="banner">
      <h1 className="text-base font-semibold tracking-tight text-slate-900">Hinaing — Baguio City</h1>
      <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">Public sentiment console. Configure and generate a grounded briefing.</p>
    </div>
  );
}
