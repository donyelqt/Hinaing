"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { CheckCheck } from "lucide-react";

/**
 * AgenticHinaing 7-node pipeline — progressive spawn, light theme.
 *
 * Invariants appear as the backend reaches them. Nothing below is drawn
 * until the run is there. Completed rows stay on as the receipt.
 *
 * Stage tokens via /chat/analyze/status:
 *   query_orchestrator · retrieval · recall · analyze · memory · themes · snapshot
 */

type NodeDef = {
  id: string;
  index: number;
  label: string;
  signature: string;
  workers?: { name: string; tag: string }[];
};

const NODES: NodeDef[] = [
  { id: "query_orchestrator", index: 1, label: "Query Orchestrator", signature: "ReAct planner — Gemini 2.5 Flash Lite" },
  { id: "retrieval",          index: 2, label: "Retrieval Agent",     signature: "LangSearch primary · Tavily backfill", workers: [{ name: "langsearch-01", tag: "primary fetch" }, { name: "tavily-01", tag: "backfill + verify" }] },
  { id: "recall",             index: 3, label: "RAG Recall",          signature: "Qdrant internal memory · BGE-large-en-v1.5" },
  { id: "analyze",            index: 4, label: "Analysis Swarm",      signature: "Sentiment ensemble ∥ 5-signal credibility", workers: [{ name: "sentiment-01", tag: "RoBERTa ∥ Groq" }, { name: "cred-01", tag: "Domain · CrossRef · FactChk · LLM · Tavily" }] },
  { id: "memory",             index: 5, label: "Memory Consolidation", signature: "Context Augmentation — Qdrant upsert" },
  { id: "themes",             index: 6, label: "Theme Swarm",         signature: "Router → 6 specialists across civic domains", workers: [{ name: "theme-router", tag: "route by intent" }, { name: "theme-infra", tag: "roads · water · grid" }, { name: "theme-health", tag: "hospitals · dengue" }, { name: "theme-safety", tag: "crime · disaster" }, { name: "theme-tourism", tag: "visitors · events" }, { name: "theme-economy", tag: "markets · livelihood" }, { name: "theme-env", tag: "waste · air · flood" }] },
  { id: "snapshot",           index: 7, label: "Verification",        signature: "FaithfulnessAgent — NLI entailment · citation diff" },
];

const TOTAL = NODES.length;

function stripProgressGlyphs(value: string | undefined): string {
  if (!value) return "";
  // Backend emits messages like "📡 Query Orchestrator: ..." — drop the glyph and colon prefix.
  return value.replace(/^\s*[^\sA-Za-z0-9]{1,4}\s*/, "").replace(/^\s*[A-Za-z]+\s*:\s*/, "").trim();
}

type NodeState = "done" | "active";

function Node({ def, state }: { def: NodeDef; state: NodeState }) {
  const active = state === "active";

  return (
    <li
      className={cn(
        "relative pl-8 sm:pl-10 motion-safe:animate-[fade-up-soft_420ms_cubic-bezier(0.22,1,0.36,1)_both]",
        "before:absolute before:left-[17px] sm:before:left-[21px] before:top-0 before:bottom-0 before:w-px before:bg-slate-200",
        active && "before:bg-[rgb(var(--brand-from-rgb)_/_0.35)]"
      )}
    >
      {/* Spine junction */}
      <span
        aria-hidden="true"
        className={cn(
          "absolute left-0 top-[3px] sm:top-[5px] flex items-center justify-center",
          "h-7 w-7 sm:h-8 sm:w-8 rounded-full border transition-[border-color,box-shadow,background-color] duration-300 ease-out",
          active
            ? "border-violet-500/40 bg-violet-50 shadow-[0_0_0_4px_rgba(91,60,200,0.08)]"
            : "border-slate-200 bg-white"
        )}
      >
        {active ? (
          <>
            <span aria-hidden="true" className="absolute inset-0 rounded-full border border-violet-500/25 motion-safe:animate-ping motion-reduce:hidden" />
            <span aria-hidden="true" className="h-[9px] w-[9px] rounded-full bg-[rgb(var(--brand-from-rgb))] motion-safe:animate-pulse" />
          </>
        ) : (
          <CheckCheck className="h-3.5 w-3.5 text-[rgb(var(--brand-from-rgb))]/80" aria-hidden="true" />
        )}
      </span>

      {/* Row body */}
      <div
        className={cn(
          "rounded-xl border bg-white transition-[border-color,box-shadow] duration-300 ease-out",
          active
            ? "border-[rgb(var(--brand-from-rgb)_/_0.25)] bg-[linear-gradient(180deg,rgb(var(--brand-to-rgb))_0%,rgb(var(--brand-from-rgb))_100%)] shadow-sm"
            : "border-slate-100"
        )}
      >
        {/* Micro strip */}
        <div className="flex items-center justify-between gap-2 px-3 pt-2">
          <span
            className={cn(
              "font-mono text-[8.5px] sm:text-[9.5px] font-semibold tracking-[0.16em]",
              active ? "text-white/80" : "text-slate-400"
            )}
          >
            {String(def.index).padStart(2, "0")}<span className="text-slate-300"> / 07</span>
          </span>
          <span
            className={cn(
              "font-mono text-[8px] sm:text-[9px] tracking-[0.18em] uppercase",
              active ? "text-white/85" : "text-slate-400"
            )}
          >
            {active ? "running" : "done"}
          </span>
        </div>

        {/* Body */}
        <div className="px-3 pb-2.5 pt-1">
          <p
            className={cn(
              "text-[11px] sm:text-[12px] font-semibold leading-snug tracking-[-0.01em]",
              active ? "text-white" : "text-slate-500"
            )}
          >
            {def.label}
          </p>
          <p
            className={cn(
              "mt-0.5 font-mono text-[8.5px] sm:text-[9px] leading-snug tracking-[-0.005em]",
              active ? "text-white/80" : "text-slate-400"
            )}
          >
            {def.signature}
          </p>
        </div>

        {/* Spawned agents — materialize with the node, never before */}
        {def.workers && (
          <div className="px-2 pb-2">
            <div
              className="grid grid-cols-2 sm:grid-cols-3 gap-1"
              role="list"
              aria-label={`Agents spawned by ${def.label}`}
            >
              {def.workers.map((w, i) => (
                <div
                  key={w.name}
                  role="listitem"
                  style={{ animationDelay: `${i * 60}ms` }}
                  className={cn(
                    "rounded-md border px-1.5 py-1",
                    "motion-safe:animate-[fade-up-soft_300ms_cubic-bezier(0.22,1,0.36,1)_both]",
                    active
                      ? "border-white/20 bg-white/15 text-white/90"
                      : "border-emerald-200/80 bg-emerald-50/70 text-emerald-800"
                  )}
                >
                  <div className="flex items-center gap-1">
                    <span
                      aria-hidden="true"
                      className={cn(
                        "h-1 w-1 rounded-full shrink-0",
                        active ? "bg-white/90 motion-safe:animate-pulse" : "bg-emerald-500"
                      )}
                    />
                    <span className={cn("font-mono text-[7.5px] sm:text-[8.5px] uppercase tracking-[0.12em] truncate", active ? "text-white/85" : "text-emerald-800")}>{w.name}</span>
                  </div>
                  <p className={cn("mt-0.5 font-mono text-[7.5px] sm:text-[8px] leading-[1.25] line-clamp-2", active ? "text-white/65" : "text-emerald-700/80")}>{w.tag}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </li>
  );
}

export function PipelineTrajectory({
  stage,
  progress,
  message,
}: {
  stage: string;
  progress: number;
  message?: string;
}) {
  const stageIndex = NODES.findIndex((n) => n.id === stage);
  const knownStage = stageIndex >= 0;
  const targetIndex = knownStage ? stageIndex : Math.min(TOTAL - 1, Math.floor(Math.min(1, Math.max(0, Number.isFinite(progress) ? progress : 0)) * TOTAL));

  // Paced reading time. Never ahead of the backend; never faster than usable focus.
  // Dwell preserves meaning (Domain → CrossRef → FactChk → LLM → Tavily are difficult labels).
  const DWELL_MS = [1600, 2000, 800, 2200, 1200, 2400, 1600];
  const reduceMotion = React.useRef(
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
  const [revealed, setRevealed] = React.useState(0);
  const [dwellFlash, setDwellFlash] = React.useState(0);

  // Catch-up: required reveal for a given monotonic target (backend stage index).
  // When backend bursts ahead, every node gets its minimum visible moment.
  React.useEffect(() => {
    if (revealed >= TOTAL) return;
    const targetCap = Math.min(Math.max(targetIndex, 0), TOTAL - 1) + 1;
    const capAtThisStage = reduceMotion.current ? targetCap : totalDwell(targetCap);
    // Sequential pacing for each unrevealed node up to cap
    let cancelled = false;
    const order = Array.from({ length: revealCap(revealed, targetCap) - revealed }, (_, i) => revealed + i);
    let timer: number | undefined;
    let elapsed = 0;
    for (const nodeIdx of order) {
      const dwell = reduceMotion.current ? 0 : DWELL_MS[nodeIdx];
      timer = window.setTimeout(() => {
        if (cancelled) return;
        setRevealed((n) => (n <= nodeIdx ? nodeIdx + 1 : n));
      }, elapsed + dwell);
      elapsed += dwell;
    }
    return () => { cancelled = true; if (timer) window.clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetIndex, revealed, dwellFlash]);

  const activeIndex = Math.min(revealed - 1, TOTAL - 1);
  // Progress tracks how far the trajectory has actually spawned, not a raw backend percentage,
  // so the visible bar and the node list can never disagree.
  const fill = revealed / TOTAL;

  function totalDwell(cap: number) {
    return DWELL_MS.slice(0, cap).reduce((a, b) => a + b, 0);
  }
  function revealCap(current: number, target: number) {
    return Math.max(current + 1, target);
  }

  const isFullyRevealed = revealed >= TOTAL;

  // Reset to blank when the run restarts (stage ticks back to index 0 or "start").
  const lastTargetRef = React.useRef(targetIndex);
  React.useEffect(() => {
    if (targetIndex < lastTargetRef.current && revealed > 0) {
      lastTargetRef.current = targetIndex;
      setRevealed(targetIndex >= 0 ? 1 : 0);
    } else {
      lastTargetRef.current = targetIndex;
    }
  }, [targetIndex, revealed]);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="7-node pipeline progress"
      className="relative w-full max-w-md mx-auto mb-2 sm:mb-3 px-0 sm:px-1"
    >
      {/* Eyebrow */}
      <div className="mb-2 flex items-center justify-between border-b border-slate-200 pb-1.5">
        <span className="font-mono text-[9px] sm:text-[10px] tracking-[0.18em] uppercase text-slate-500">
          agent trajectory
        </span>
        <span className="font-mono text-[8px] sm:text-[9px] tracking-[0.16em] tabular-nums text-slate-400">
          07 invariants
        </span>
      </div>

      {/* Spine */}
      <ol className="relative">
        <div aria-hidden="true" className="pointer-events-none absolute left-[13px] sm:left-[16px] top-1 bottom-1 w-px bg-slate-200" />
        {NODES.slice(0, revealed).map((node, i) => {
          const state: NodeState = i < activeIndex ? "done" : "active";
          return <Node key={node.id} def={node} state={state} />;
        })}
      </ol>

      {/* Run pulse — brand vertical gradient, pace-controlled by transform transition */}
      <div className="mt-2.5 flex items-center gap-2">
        <div className="h-[3px] flex-1 rounded-full bg-slate-200/80 overflow-hidden" role="presentation">
          <div
            className="h-full w-full origin-left brand-gradient-y transition-transform duration-500 ease-out motion-reduce:transition-none"
            style={{ transform: `scaleX(${fill})` }}
          />
        </div>
        <span className="font-mono text-[10px] sm:text-[10.5px] tabular-nums tracking-[0.06em] text-slate-500 w-9 text-right">
          <span className="tabular-nums">{Math.round(fill * 100)}</span><span className="text-slate-400">%</span>
        </span>
      </div>
      <p className="mt-2 text-[10px] sm:text-[11px] leading-snug text-slate-600 line-clamp-2">
        {stripProgressGlyphs(message) || "Initializing invariants…"}
      </p>
    </div>
  );
}
