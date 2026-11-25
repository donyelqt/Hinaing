"use client";

import * as React from "react";
import { cn } from "../../../lib/utils";

/**
 * Fast Q&A thinking indicator.
 *
 * Fast Q&A is one retrieval pass then one generation pass, so this reads as a
 * single living sphere rather than a checklist. The sphere is the only place
 * the gradient lives, and the label carries the real state.
 *
 * There is no percentage and no bar. The request is a single pass, so a number
 * would be fake progress.
 *
 * The seven-node trajectory is deliberately not used here. It paces a node
 * every 1.6-2.4s and a Fast Q&A request finishes in about 600ms, so it would
 * never clear its first dwell.
 *
 * Depth comes from stacked light, not from blur. A specular highlight, a
 * drifting inner field, a masked rim sheen and a soft bloom read as a lit
 * sphere. Blur alone reads as a smudge, which is what the first pass looked
 * like.
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
 * Lit sphere. The highlight has to hold for a visible distance, so the white
 * stop runs to 22% before the terminator. A tight 5% stop renders as a black
 * disc with a pinprick, which is what the first build measured.
 */
const SPHERE =
  "radial-gradient(circle at 30% 24%, #ffffff 0%, rgba(255,255,255,0.94) 12%, rgb(var(--brand-to-rgb)) 34%, rgb(var(--brand-from-rgb)) 66%, rgb(24 32 92) 100%)";

/**
 * A second field inside the body, in the magenta both references carry. It
 * drifts on its own path so the sphere has an interior that moves, which is
 * what separates a lit orb from a flat disc.
 */
const CORE =
  "radial-gradient(circle at 68% 72%, rgba(232,54,223,0.85) 0%, rgba(199,56,181,0.5) 34%, rgba(0,0,0,0) 68%)";

/** A narrow band of light that travels around the rim. */
const SHEEN =
  "conic-gradient(from 0deg, rgba(255,255,255,0) 0deg, rgba(255,255,255,0.9) 42deg, rgba(255,255,255,0) 96deg, rgba(255,255,255,0) 200deg, rgba(255,255,255,0.55) 248deg, rgba(255,255,255,0) 304deg)";

/** Keeps the sheen on the rim instead of across the face. */
const RING =
  "radial-gradient(farthest-side, transparent calc(100% - 2.5px), #000 calc(100% - 1.5px))";

const BLOOM =
  "radial-gradient(circle, rgb(var(--brand-to-rgb)/0.5) 0%, rgb(var(--brand-from-rgb)/0.26) 45%, rgba(0,0,0,0) 72%)";

/**
 * Keyframes are inlined because the repo already does this for the welcome
 * halo, and a one-off indicator does not earn a global block. The reduced
 * motion kill switch is the same shape as that block's.
 */
const KEYFRAMES = `
  @keyframes fq-orb-light {
    0%, 100% { background-position: 0% 0%; }
    50%      { background-position: 100% 100%; }
  }
  @keyframes fq-orb-spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  @keyframes fq-orb-bloom {
    0%, 100% { opacity: 0.34; transform: scale(0.94); }
    50%      { opacity: 0.6;  transform: scale(1.06); }
  }
  @keyframes fq-orb-core {
    0%, 100% { background-position: 100% 100%; }
    50%      { background-position: 0% 0%; }
  }
  @keyframes fq-orb-sweep {
    from { background-position: 130% 0; }
    to   { background-position: -130% 0; }
  }
  /* The base opacities carry the still frame, so reduced motion keeps a lit
     sphere instead of an unstyled box. */
  .fq-orb-bloom { opacity: 0.34; }
  @media (prefers-reduced-motion: reduce) {
    .fq-orb, .fq-orb-core, .fq-orb-sheen, .fq-orb-bloom, .fq-orb-label { animation: none !important; }
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
          className="fq-orb-bloom absolute -inset-1.5 rounded-full motion-safe:animate-[fq-orb-bloom_3400ms_ease-in-out_infinite]"
          style={{ backgroundImage: BLOOM }}
        />
        <span
          className="fq-orb relative h-7 w-7 overflow-hidden rounded-full motion-safe:animate-[fq-orb-light_5200ms_ease-in-out_infinite]"
          style={{
            backgroundImage: SPHERE,
            backgroundSize: "180% 180%",
            boxShadow:
              "inset -3px -4px 8px rgba(12,18,60,0.5), inset 2px 2px 6px rgba(255,255,255,0.32), 0 0 0 1px rgb(var(--brand-from-rgb)/0.22)",
          }}
        >
          <span
            className="absolute inset-0 motion-safe:animate-[fq-orb-core_3600ms_ease-in-out_infinite]"
            style={{ backgroundImage: CORE, backgroundSize: "160% 160%" }}
          />
        </span>
        <span
          className="fq-orb-sheen absolute inset-0 rounded-full motion-safe:animate-[fq-orb-spin_5200ms_linear_infinite]"
          style={{ backgroundImage: SHEEN, maskImage: RING, WebkitMaskImage: RING }}
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