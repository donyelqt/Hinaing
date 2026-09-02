import type { ToggleOption } from "../types";

type HeroSectionProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
};

export function HeroSection(_props: HeroSectionProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] p-6 text-white shadow-[0_12px_32px_-16px_rgba(48,86,214,0.35),inset_0_1px_0_rgba(255,255,255,0.08)] ring-1 ring-white/10 md:p-7" role="banner">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(255,255,255,0.09),transparent_45%)]" aria-hidden="true" />
      <div className="absolute inset-0 opacity-[0.015]" style={{backgroundImage:"url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.4'/%3E%3C/svg%3E\")"}} aria-hidden="true" />
      <div className="relative">
        <h1 className="text-base font-semibold tracking-tight text-white text-balance">Hinaing — Baguio City</h1>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-white/85 text-pretty">Public sentiment console. Configure and generate a grounded briefing.</p>
      </div>
    </div>
  );
}
