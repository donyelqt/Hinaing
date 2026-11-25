"use client";

import * as React from "react";
import { cn } from "../../../lib/utils";

/**
 * Fast Q&A thinking indicator.
 *
 * Fast Q&A is one retrieval pass then one generation pass, so this reads as a
 * single travelling head with a trail behind it. It deliberately does not use
 * the 7-node trajectory: that component paces a 12-second swarm, and a 600ms
 * request would never clear its first dwell.
 *
 * The row is decorative. The answer that replaces it is the status message a
 * screen reader reads, so nothing here is a live region: a node that mounts
 * and unmounts inside 600ms never enters the accessibility tree before the
 * mutation, and `aria-busy` on it would defer the announcement forever.
 */

export type FastQnaPhase =
  | { kind: "retrieval"; progress: number }
  | { kind: "generating"; progress: number };

export type FastQnaThinkingProps = {
  phase: FastQnaPhase;
  className?: string;
};

/** Both labels are always mounted so the row is as wide as its widest word. */
const LABELS: Record<FastQnaPhase["kind"], string> = {
  retrieval: "Searching for relevant information",
  generating: "Generating response",
};

/** Keeps the head visible when a phase reports zero progress. */
const MIN_PROGRESS = 0.08;

/**
 * Reads the live preference rather than a mount-time snapshot, so a user who
 * turns the setting on mid-session gets the still frame on the next render.
 */
function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = React.useState(false);

  React.useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = (): void => setReduced(query.matches);
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);

  return reduced;
}

export function FastQnaThinking({ phase, className }: FastQnaThinkingProps) {
  const progress = Math.min(1, Math.max(MIN_PROGRESS, phase.progress));

  const reduceMotion = usePrefersReducedMotion();
  const sweep = reduceMotion ? undefined : "transform 240ms cubic-bezier(0.22, 1, 0.36, 1)";

  return (
    <div
      aria-hidden="true"
      data-fast-qna=""
      data-phase={phase.kind}
      className={cn("relative h-10 w-full select-none", className)}
    >
      <div className="absolute inset-x-0 top-1 h-1 rounded-full bg-slate-200/70">
        <div
          className="absolute inset-y-0 left-0 w-full origin-left rounded-full bg-[linear-gradient(90deg,rgb(var(--brand-from-rgb)/0.35),rgb(var(--brand-to-rgb)/0.9))]"
          style={{ transform: `scaleX(${progress})`, transition: sweep }}
        />
        <div
          className="absolute inset-0"
          style={{ transform: `translateX(${(progress - 1) * 100}%)`, transition: sweep }}
        >
          <span className="absolute right-0 top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full bg-[linear-gradient(135deg,rgb(var(--brand-from-rgb)),rgb(var(--brand-to-rgb)))] shadow-[0_0_0_3px_rgb(var(--brand-from-rgb)/0.16)]" />
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 grid leading-4">
        {(Object.keys(LABELS) as FastQnaPhase["kind"][]).map((kind) => (
          <span
            key={kind}
            data-active={kind === phase.kind}
            className="col-start-1 row-start-1 truncate text-xs font-medium text-slate-500"
            style={kind === phase.kind ? undefined : { visibility: "hidden" }}
          >
            {LABELS[kind]}
          </span>
        ))}
      </div>
    </div>
  );
}