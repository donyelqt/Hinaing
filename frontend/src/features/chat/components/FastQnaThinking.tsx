"use client";

import * as React from "react";
import { cn } from "../../../lib/utils";

/**
 * Thinking indicator, anime cel style.
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
 * Anime cel shading, not a soft 3D sphere. Three hard bands replace the smooth
 * falloff, the rim is a bright keyline instead of a shadow, and the interior
 * field is a sharp-edged crescent that sweeps rather than a blur that drifts.
 * Hard edges are the whole tell: a cel reads as drawn, a blur reads as rendered.
 *
 * The row is decorative. The answer that replaces it is the status message a
 * screen reader reads, so nothing here is a live region: a row that mounts and
 * unmounts inside 600ms never enters the accessibility tree before the
 * mutation, and `aria-busy` on it would defer the announcement forever.
 */

export type FastQnaStage = "thinking" | "retrieval" | "generating";

export type FastQnaThinkingProps = {
  /** Defaults to `thinking`, which is all the seed message knows. */
  stage?: FastQnaStage;
  className?: string;
};

/**
 * One label per stage. The wait says Thinking, then each pass names itself, so
 * the user can see the request move rather than watch one word sit still.
 */
const LABELS: Record<FastQnaStage, string> = {
  thinking: "Thinking",
  retrieval: "Searching for relevant information",
  generating: "Generating response",
};

/**
 * Three hard bands. The highlight is a flat white cap, the mid is the brand
 * violet, the shadow is a deep indigo, and each stop is a hard edge rather than
 * a fade. That banding is what makes it read as cel shaded.
 */
const CEL =
  "radial-gradient(circle at 32% 26%, #ffffff 0%, #ffffff 26%, rgb(var(--brand-to-rgb)) 27%, rgb(var(--brand-to-rgb)) 58%, rgb(var(--brand-from-rgb)) 59%, rgb(30 27 75) 100%)";

/**
 * A sharp crescent inside the body. Two hard stops and no fade, so it reads as
 * a drawn shape sliding across the sphere rather than a glow.
 */
const CRESCENT =
  "radial-gradient(circle at 74% 70%, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 52%, rgba(255,255,255,0.92) 53%, rgba(255,255,255,0.92) 62%, rgba(255,255,255,0) 63%)";

/** The anime keyline: a bright rim, brightest at the top left. */
const KEYLINE =
  "conic-gradient(from 210deg, #ffffff 0deg, rgba(255,255,255,0.95) 40deg, rgba(255,255,255,0.25) 120deg, rgba(255,255,255,0.1) 220deg, rgba(255,255,255,0.85) 320deg, #ffffff 360deg)";

/** Keeps the keyline on the rim instead of across the face. */
const RING =
  "radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 1px))";

/** A tight halo, the anime glow. Small and bright, not a wide bloom. */
const HALO =
  "radial-gradient(circle, rgb(var(--brand-to-rgb)/0.55) 0%, rgb(var(--brand-from-rgb)/0.3) 52%, rgba(0,0,0,0) 74%)";

/**
 * Keyframes are inlined because the repo already does this for the welcome
 * halo, and a one-off indicator does not earn a global block. The reduced
 * motion kill switch is the same shape as that block's.
 */
const KEYFRAMES = `
  /* Hard steps, not a smooth ramp. The crescent jumps between positions the way
     a cel layer snaps, which is the anime tell. */
  @keyframes fq-orb-crescent {
    0%, 100% { background-position: 0% 0%; }
    50%      { background-position: 100% 100%; }
  }
  @keyframes fq-orb-keyline {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  @keyframes fq-orb-halo {
    0%, 100% { opacity: 0.4;  transform: scale(0.96); }
    50%      { opacity: 0.72; transform: scale(1.08); }
  }
  @keyframes fq-orb-sweep {
    from { background-position: 130% 0; }
    to   { background-position: -130% 0; }
  }
  /* The base opacities carry the still frame, so reduced motion keeps a drawn
     orb instead of an unstyled box. */
  .fq-orb-halo { opacity: 0.4; }
  @media (prefers-reduced-motion: reduce) {
    .fq-orb, .fq-orb-crescent, .fq-orb-keyline, .fq-orb-halo, .fq-orb-label { animation: none !important; }
  }
`;

export function FastQnaThinking({ stage = "thinking", className }: FastQnaThinkingProps) {
  return (
    <div
      aria-hidden="true"
      data-fast-qna=""
      data-stage={stage}
      className={cn("flex min-h-11 w-full select-none items-center gap-3 py-1.5", className)}
    >
      <style>{KEYFRAMES}</style>

      <span className="relative grid h-8 w-8 shrink-0 place-items-center">
        <span
          className="fq-orb-halo absolute -inset-1 rounded-full motion-safe:animate-[fq-orb-halo_2600ms_ease-in-out_infinite]"
          style={{ backgroundImage: HALO }}
        />
        <span
          className="fq-orb relative h-7 w-7 overflow-hidden rounded-full motion-safe:animate-[fq-orb-crescent_1800ms_steps(1,end)_infinite]"
          style={{
            backgroundImage: CEL,
            boxShadow: "0 0 0 1.5px rgb(var(--brand-from-rgb))",
          }}
        >
          <span
            className="absolute inset-0"
            style={{ backgroundImage: CRESCENT, backgroundSize: "200% 200%" }}
          />
        </span>
        <span
          className="fq-orb-keyline absolute inset-0 rounded-full motion-safe:animate-[fq-orb-keyline_4200ms_linear_infinite]"
          style={{ backgroundImage: KEYLINE, maskImage: RING, WebkitMaskImage: RING }}
        />
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
        {LABELS[stage]}
      </span>
    </div>
  );
}