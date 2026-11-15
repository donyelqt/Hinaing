import Image from "next/image";
import type { ToggleOption } from "../types";

type HeroSectionProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
};

export function HeroSection(_props: HeroSectionProps) {
  return (
    <div className="relative overflow-hidden rounded-xl brand-gradient p-6 text-white shadow-[0_12px_32px_-16px_rgb(var(--brand-from-rgb)_/_0.35),inset_0_1px_0_rgba(255,255,255,0.08)] ring-1 ring-white/10 md:p-7" role="banner">
      <style>{`
        @keyframes hinaing-breathe {
          0%, 100% { transform: translate3d(0, 3px, 0) scale(1.035, 0.96) rotate(-1.2deg); }
          50% { transform: translate3d(0, -7px, 0) scale(0.97, 1.05) rotate(1.4deg); }
        }
        .hinaing-breathe {
          animation: hinaing-breathe 2.9s cubic-bezier(0.77, 0, 0.175, 1) infinite;
          transform-origin: 50% 88%;
          will-change: transform;
        }
        @media (prefers-reduced-motion: reduce) { .hinaing-breathe { animation: none; } }
      `}</style>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(255,255,255,0.09),transparent_45%)]" aria-hidden="true" />
      <div className="relative flex items-center gap-3 sm:gap-6">
        <Image
          src="/hinaing-mascot.webp"
          alt="Himp, the HinAing lion mascot, waving hello"
          width={512}
          height={628}
          priority
          className="hinaing-breathe h-32 w-auto shrink-0 drop-shadow-[0_10px_16px_rgba(15,23,42,0.35)] sm:h-40 md:h-44"
        />

        <div className="relative min-w-0 rounded-2xl bg-white/95 p-4 text-slate-900 shadow-[0_12px_28px_-14px_rgba(15,23,42,0.45)] sm:p-5">
          <span aria-hidden="true" className="absolute -left-2 top-1/2 h-4 w-4 -translate-y-1/2 rotate-45 bg-white/95" />
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-from sm:text-[11px]">Hi! I&apos;m Himp.</p>
          <h1 className="mt-1 text-base font-semibold tracking-tight text-slate-900 text-balance sm:text-lg">Hinaing — Baguio City</h1>
          <p className="mt-1 max-w-md text-xs leading-relaxed text-slate-600 text-pretty sm:text-sm">Public sentiment console. Configure and generate a grounded briefing.</p>
        </div>
      </div>
    </div>
  );
}
