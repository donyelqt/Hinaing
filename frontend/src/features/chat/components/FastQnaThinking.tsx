"use client";

import * as React from "react";
import { cn } from "../../../lib/utils";

/**
 * Fast Q&A thinking indicator.
 *
 * Fast Q&A is one retrieval pass then one generation pass, so this reads as a
 * single living orb rather than a checklist. The orb is the only place the
 * gradient lives, and the label carries the real state.
 *
 * There is no percentage and no bar. The request is a single pass, so a number
 * would be fake progress.
 *
 * The seven-node trajectory is deliberately not used here. It paces a node
 * every 1.6-2.4s and a Fast Q&A request finishes in about 600ms, so it would
 * never clear its first dwell.
 *
 * The row is decorative. The answer that replaces it is the status message a
 * screen reader reads, so nothing here is a live region: a row that mounts and
 * unmounts inside 600ms never enters the accessibility tree before the
 * mutation, and `aria-busy` on it would defer the announcement forever.
 */

export type FastQnaPhase =
  | { kind: "retrieval"; progress: number }
  | { kind: "generating"; progress: number };

export type FastQnaThinkingProps = {
  phase: FastQnaPhase;
  className?: string;
};

const LABELS: Record<FastQnaPhase["kind"], string> = {
  retrieval: "Searching for relevant information",
  generating: "Generating response",
};

/**
 * Keyframes are inlined because the repo already does this for the welcome
 * halo, and a one-off indicator does not earn a global block. The reduced
 * motion kill switch is the same shape as that block's.
 */
const KEYFRAMES = `
  @keyframes fq-orb-morph {
    0%, 100% { border-radius: 58% 42% 55% 45% / 45% 58% 42% 55%; }
    33%      { border-radius: 45% 55% 48% 52% / 58% 45% 55% 42%; }
    66%      { border-radius: 52% 48% 60% 40% / 42% 52% 45% 58%; }
  }
  @keyframes fq-orb-halo {
    0%, 100% { opacity: 0.26; transform: scale(1); }
    50%      { opacity: 0.46; transform: scale(1.12); }
  }
  @keyframes fq-orb-sweep {
    from { background-position: 130% 0; }
    to   { background-position: -130% 0; }
  }
  /* The base shape carries the still frame, so reduced motion keeps an orb
     instead of the square the unstyled box would otherwise be. */
  .fq-orb { border-radius: 58% 42% 55% 45% / 45% 58% 42% 55%; }
  .fq-orb-halo { opacity: 0.26; }
  @media (prefers-reduced-motion: reduce) {
    .fq-orb, .fq-orb-halo, .fq-orb-label { animation: none !important; }
  }
`;

export function FastQnaThinking({ phase, className }: FastQnaThinkingProps) {
  return (
    <div
      aria-hidden="true"
      data-fast-qna=""
      data-phase={phase.kind}
      className={cn("flex min-h-11 w-full select-none items-center gap-2.5 py-1.5", className)}
    >
      <style>{KEYFRAMES}</style>

      <span className="relative grid h-7 w-7 shrink-0 place-items-center">
        <span
          className="fq-orb-halo absolute inset-0 rounded-full bg-[radial-gradient(circle_at_35%_30%,rgb(var(--brand-to-rgb)),rgb(var(--brand-from-rgb)))] blur-[6px] motion-safe:animate-[fq-orb-halo_3400ms_ease-in-out_infinite]"
        />
        <span className="fq-orb relative h-6 w-6 bg-[radial-gradient(circle_at_35%_30%,rgb(var(--brand-to-rgb)),rgb(var(--brand-from-rgb)))] shadow-[0_0_0_1px_rgb(var(--brand-from-rgb)/0.2)] motion-safe:animate-[fq-orb-morph_2400ms_ease-in-out_infinite]" />
      </span>

      <span
        className="fq-orb-label truncate text-xs font-medium text-slate-600 motion-safe:animate-[fq-orb-sweep_2400ms_linear_infinite]"
        style={{
          backgroundImage:
            "linear-gradient(100deg,rgb(71 85 105) 0%,rgb(71 85 105) 40%,rgb(var(--brand-to-rgb)) 50%,rgb(71 85 105) 60%,rgb(71 85 105) 100%)",
          backgroundSize: "230% 100%",
          backgroundClip: "text",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        {LABELS[phase.kind]}
      </span>
    </div>
  );
}