"use client";

import * as React from "react";
import { Radar, FileSearch, Brain, Zap, Database, Target, ClipboardCheck, CheckCircle2 } from "lucide-react";
import clsx from "clsx";

/**
 * PipelineTrajectory — vertical diagram of the 7-node AgenticHinaing pipeline.
 *
 * Mirrors the actual stages the backend emits via /chat/analyze/status:
 *   Node 1 Query Orchestrator  (ReAct · Gemini 2.5 Flash Lite)
 *   Node 2 Retrieval Agent     (LangSearch primary · Tavily backfill)
 *   Node 3 RAG Recall          (Qdrant internal memory · BGE-large)
 *   Node 4 Analysis            (Sentiment ensemble ∥ Credibility 5-signal)
 *   Node 5 Memory Consolidation (ContextAugmentation · writes Qdrant)
 *   Node 6 Theme Agents        (6 specialists + router)
 *   Node 7 Verification        (NLI claim check · FaithfulnessAgent)
 *
 * Top→down reading matches the narrative: gossip enters at the top, verified
 * briefing leaves at the bottom. Parallel workers render as fan-out lanes
 * sharing one rail segment.
 */

type NodeDef = {
  id: string;          // matches backend `stage` token
  index: number;       // 1-based node number
  label: string;
  detail: string;
  icon: React.ReactNode;
  workers?: string[];
};

const NODES: NodeDef[] = [
  { id: "query_orchestrator", index: 1, label: "Node 1 · Query Orchestrator", detail: "ReAct planner · Gemini 2.5 Flash Lite", icon: <Radar className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" /> },
  { id: "retrieval",          index: 2, label: "Node 2 · Retrieval Agent",     detail: "LangSearch web · Tavily backfill",       icon: <FileSearch className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />, workers: ["LangSearch", "Tavily"] },
  { id: "recall",             index: 3, label: "Node 3 · RAG Recall",          detail: "Qdrant internal memory · BGE-large",      icon: <Brain className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" /> },
  { id: "analyze",            index: 4, label: "Node 4 · Analysis",            detail: "Sentiment ensemble ∥ Credibility 5-signal", icon: <Zap className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />, workers: ["Sentiment", "Credibility"] },
  { id: "memory",             index: 5, label: "Node 5 · Memory Consolidation",detail: "Context Augmentation · writes RAG",       icon: <Database className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" /> },
  { id: "themes",             index: 6, label: "Node 6 · Theme Agents",        detail: "Router + 6 domain specialists",           icon: <Target className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />, workers: ["Infrastructure", "Health", "Safety", "Tourism", "Economy", "Environment"] },
  { id: "snapshot",           index: 7, label: "Node 7 · Verification",        detail: "NLI claim check · FaithfulnessAgent",     icon: <ClipboardCheck className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" /> },
];

const TOTAL = NODES.length;

type NodeState = "done" | "active" | "pending";

function RailNode({ def, state }: { def: NodeDef; state: NodeState }) {
  const Icon = def.icon;
  return (
    <div className={clsx(
      "relative z-10 flex items-center gap-3 rounded-xl border p-2 sm:p-2.5 transition-all duration-300 motion-reduce:transition-none",
      state === "done"    && "border-emerald-200 bg-emerald-50/70",
      state === "active"  && "border-slate-900 bg-slate-900 text-white shadow-lg",
      state === "pending" && "border-slate-200 bg-white text-slate-400",
    )}>
      <div aria-hidden="true" className={clsx(
        "flex h-8 w-8 sm:h-9 sm:w-9 shrink-0 items-center justify-center rounded-lg transition-colors duration-300 motion-reduce:transition-none",
        state === "done"    && "bg-emerald-100 text-emerald-700",
        state === "active"  && "bg-white/10 text-white",
        state === "pending" && "bg-slate-100 text-slate-400",
      )}>
        {state === "done" ? <CheckCircle2 className="h-5 w-5" aria-hidden="true" /> : Icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className={clsx(
            "text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider",
            state === "active"  && "text-white/70",
            state === "done"    && "text-emerald-800",
            state === "pending" && "text-slate-400",
          )}>
            Node {def.index}
          </p>
          {state === "active" && (
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75 motion-reduce:hidden" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-400" />
            </span>
          )}
        </div>
        <p className={clsx(
          "text-[11px] sm:text-xs font-semibold leading-tight",
          state === "active"  && "text-white",
          state === "done"    && "text-emerald-900",
          state === "pending" && "text-slate-500",
        )}>
          {def.label.replace(/^Node \d+ · /, "")}
        </p>
        <p className={clsx(
          "mt-0.5 text-[9px] sm:text-[10px] leading-tight",
          state === "active"  && "text-white/70",
          state === "done"    && "text-emerald-800/80",
          state === "pending" && "text-slate-400",
        )}>
          {def.detail}
        </p>
      </div>
    </div>
  );
}

function FanOut({ workers, state }: { workers: string[]; state: NodeState }) {
  if (state === "pending") return null;
  return (
    <div className="ml-9 sm:ml-11 mt-1.5 flex flex-wrap gap-1" aria-hidden="true">
      {workers.map((w) => (
        <span key={w} className={clsx(
          "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[8px] sm:text-[9px] font-medium transition-colors duration-300 motion-reduce:transition-none",
          state === "active" && "border-slate-300 bg-slate-50 text-slate-800",
          state === "done"   && "border-emerald-200 bg-emerald-50 text-emerald-800",
        )}>
          <span className={clsx(
            "h-1.5 w-1.5 rounded-full",
            state === "active" && "animate-pulse bg-amber-400",
            state === "done"   && "bg-emerald-500",
          )} />
          {w}
        </span>
      ))}
    </div>
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
  const fill = Math.min(1, Math.max(0, Number.isFinite(progress) ? progress : 0));
  const stageIndex = NODES.findIndex((n) => n.id === stage);
  // Fallback: derive active node from fill when the stage token is unknown.
  const derivedIndex = stageIndex >= 0 ? stageIndex : Math.min(TOTAL - 1, Math.floor(fill * TOTAL));

  return (
    <div role="status" aria-live="polite" aria-label="7-node pipeline progress" className="relative w-full max-w-md mx-auto mb-3 sm:mb-4 px-0 sm:px-2">
      <ol className="relative pl-0">
        <div aria-hidden="true" className="pointer-events-none absolute left-[15px] sm:left-[19px] top-4 bottom-4 w-px bg-slate-200">
          <div className="absolute left-0 top-0 w-px origin-top bg-emerald-500 transition-transform duration-500 ease-out motion-reduce:transition-none" style={{ height: "100%", transform: `scaleY(${fill})` }} />
        </div>

        {NODES.map((node, i) => {
          const state: NodeState = i < derivedIndex ? "done" : i === derivedIndex ? "active" : "pending";
          return (
            <li key={node.id} className="relative mb-2 last:mb-0">
              <RailNode def={node} state={state} />
              {node.workers && <FanOut workers={node.workers} state={state} />}
            </li>
          );
        })}
      </ol>

      <div className="mt-3 h-1 sm:h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full w-full origin-left bg-gradient-to-r from-emerald-500 via-slate-900 to-slate-900 transition-transform duration-500 ease-out motion-reduce:transition-none" style={{ transform: `scaleX(${fill})` }} />
      </div>
      <p className="mt-2 text-[10px] sm:text-[11px] text-slate-600 text-center font-medium line-clamp-2 leading-snug">
        {message || "Initializing pipeline…"}
      </p>
    </div>
  );
}
