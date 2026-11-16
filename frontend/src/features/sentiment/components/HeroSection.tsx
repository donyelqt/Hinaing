"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { ToggleOption } from "../types";

type HeroSectionProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
};

const NARRATIVES = [
  "I read every Baguio post so you don't have to.",
  "Tell me the window. I'll do the digging.",
  "Ask me what Baguio is saying today.",
  "Every complaint counts. I keep score.",
  "Grounded briefings, straight from Baguio streets.",
];

function pickNarrative(): string {
  try {
    const stored = window.sessionStorage.getItem("bronny-narrative-index");
    const prev = stored !== null ? Number(stored) : -1;
    let index = Math.floor(Math.random() * NARRATIVES.length);
    if (!Number.isFinite(index) || (NARRATIVES.length > 1 && index === prev)) {
      index = (prev + 1 + NARRATIVES.length) % NARRATIVES.length;
    }
    window.sessionStorage.setItem("bronny-narrative-index", String(index));
    return NARRATIVES[index];
  } catch {
    return NARRATIVES[Math.floor(Math.random() * NARRATIVES.length)];
  }
}

export function HeroSection(_props: HeroSectionProps) {
  const [narrative, setNarrative] = useState<string | null>(null);
  const [typed, setTyped] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    setNarrative(pickNarrative());
  }, []);

  useEffect(() => {
    if (!narrative) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setTyped(narrative);
      setDone(true);
      return;
    }
    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      setTyped(narrative.slice(0, i));
      if (i >= narrative.length) {
        window.clearInterval(id);
        setDone(true);
      }
    }, 28);
    return () => window.clearInterval(id);
  }, [narrative]);

  return (
    <div className="relative overflow-hidden rounded-xl brand-gradient p-6 text-white shadow-[0_12px_32px_-16px_rgb(var(--brand-from-rgb)_/_0.35),inset_0_1px_0_rgba(255,255,255,0.08)] ring-1 ring-white/10 md:p-7" role="banner">
      <style>{`
        @keyframes hinaing-breathe {
          0%, 100% { transform: translate3d(0, 3px, 0) scale(1.035, 0.96) rotate(-1.2deg); }
          50% { transform: translate3d(0, -7px, 0) scale(0.97, 1.05) rotate(1.4deg); }
        }
        @keyframes hinaing-wave {
          0%, 47% { transform: rotate(0deg) translate3d(0, 0, 0); animation-timing-function: cubic-bezier(0.23, 1, 0.32, 1); }
          52% { transform: rotate(-9deg) translate3d(0, -1.5px, 0); animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1); }
          56% { transform: rotate(2.5deg) translate3d(0, 0, 0); animation-timing-function: cubic-bezier(0.77, 0, 0.175, 1); }
          60.5% { transform: rotate(-13.5deg) translate3d(0, -3px, 0); animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1); }
          64.5% { transform: rotate(-4deg) translate3d(0, 0, 0); animation-timing-function: cubic-bezier(0.77, 0, 0.175, 1); }
          68.5% { transform: rotate(-12.5deg) translate3d(0, -2.5px, 0); animation-timing-function: cubic-bezier(0.77, 0, 0.175, 1); }
          72.5% { transform: rotate(-6deg) translate3d(0, 0, 0); animation-timing-function: cubic-bezier(0.77, 0, 0.175, 1); }
          77.5% { transform: rotate(-10deg) translate3d(0, -1px, 0); animation-timing-function: cubic-bezier(0.32, 0.72, 0, 1); }
          92%, 100% { transform: rotate(0deg) translate3d(0, 0, 0); animation-timing-function: cubic-bezier(0.32, 0.72, 0, 1); }
        }
        @keyframes hinaing-sleeve {
          0%, 47%, 100% { transform: rotate(0deg); }
          52% { transform: rotate(-2.3deg); animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1); }
          57% { transform: rotate(0.4deg); }
          62% { transform: rotate(-1.8deg); }
          72% { transform: rotate(-1deg); }
          82% { transform: rotate(0deg); }
        }
        @keyframes hinaing-lean {
          0%, 47%, 100% { transform: rotate(0deg); }
          53% { transform: rotate(-1.5deg); }
          57% { transform: rotate(-0.2deg); }
          64% { transform: rotate(-1.3deg); }
          73% { transform: rotate(-0.8deg); }
          85% { transform: rotate(0deg); }
        }
        @keyframes bronny-caret {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .bronny-caret {
          display: inline-block;
          width: 0.55em;
          background: currentColor;
          height: 1em;
          margin-left: 2px;
          vertical-align: -0.12em;
          animation: bronny-caret 0.95s steps(1) infinite;
        }
        .bronny-caret[data-done="true"] {
          animation: none;
          opacity: 0;
          transition: opacity 300ms ease 1100ms;
        }
        .hinaing-breathe {
          animation: hinaing-breathe 2.9s cubic-bezier(0.77, 0, 0.175, 1) infinite;
          transform-origin: 50% 88%;
          will-change: transform;
        }
        .hinaing-wave {
          animation: hinaing-wave 7s cubic-bezier(0.23, 1, 0.32, 1) infinite;
          transform-origin: 21.9% 57.0%;
          will-change: transform;
        }
        .hinaing-sleeve {
          animation: hinaing-sleeve 7s cubic-bezier(0.23, 1, 0.32, 1) infinite;
          transform-origin: 20.5% 64.8%;
          will-change: transform;
        }
        .hinaing-lean {
          animation: hinaing-lean 7s cubic-bezier(0.77, 0, 0.175, 1) infinite;
          transform-origin: 50% 82%;
          will-change: transform;
        }
        @media (prefers-reduced-motion: reduce) {
          .hinaing-breathe, .hinaing-wave, .hinaing-sleeve, .hinaing-lean { animation: none; }
          .bronny-caret { animation: none; opacity: 0; }
        }
      `}</style>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(255,255,255,0.09),transparent_45%)]" aria-hidden="true" />
      <div className="relative flex items-center gap-3 sm:gap-6">
        <div className="hinaing-lean h-32 w-auto shrink-0 drop-shadow-[0_10px_16px_rgba(15,23,42,0.35)] sm:h-40 md:h-44">
          <div className="hinaing-breathe relative h-full w-auto">
            <Image
              src="/hinaing-body.webp"
              alt="Bronny, the HinAing lion mascot, waving hello"
              width={512}
              height={628}
              priority
              className="h-32 w-auto sm:h-40 md:h-44"
            />
            <Image
              src="/hinaing-forearm.webp"
              alt=""
              width={512}
              height={628}
              priority
              className="hinaing-sleeve absolute inset-0 h-32 w-auto sm:h-40 md:h-44"
            />
            <Image
              src="/hinaing-paw.webp"
              alt=""
              width={512}
              height={628}
              priority
              className="hinaing-wave absolute inset-0 h-32 w-auto sm:h-40 md:h-44"
            />
          </div>
        </div>

        <div className="relative min-w-0 rounded-2xl bg-white/95 p-4 text-slate-900 shadow-[0_12px_28px_-14px_rgba(15,23,42,0.45)] sm:p-5">
          <span aria-hidden="true" className="absolute -left-2 top-1/2 h-4 w-4 -translate-y-1/2 rotate-45 bg-white/95" />
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-from sm:text-[11px]">Hi! I&apos;m Bronny.</p>
          <h1 className="mt-1 text-base font-semibold tracking-tight text-slate-900 text-balance sm:text-lg">Hinaing — Baguio City</h1>
          <p
            className="mt-1.5 min-h-[2.25rem] max-w-md text-xs leading-relaxed text-slate-600 text-pretty sm:min-h-[1.5rem] sm:text-sm"
            aria-live="polite"
          >
            {narrative !== null && (
              <>
                <span aria-hidden="true">
                  {typed}
                  <span className="bronny-caret text-brand-from" data-done={done} />
                </span>
                <span className="sr-only">{narrative}</span>
              </>
            )}
          </p>
          <p className="mt-1 hidden text-[11px] font-medium text-slate-500 sm:block">Public sentiment console. Configure and generate a grounded briefing.</p>
        </div>
      </div>
    </div>
  );
}
