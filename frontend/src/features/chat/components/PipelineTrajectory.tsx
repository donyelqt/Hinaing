"use client";

import * as React from "react";
import { Radar, FileSearch, Brain, Zap, Database, Target, ClipboardCheck, CheckCircle2, Loader2 } from "lucide-react";
import clsx from "clsx";

/**
 * PipelineTrajectory — vertical diagram of the 7-node AgenticHinaing pipeline.
 *
 * Nodes appear as the run reaches them. The rail itself is the log:
 * pending → running → done, top to bottom, nothing disappears.
 *
 * Stage tokens published by the backend via /chat/analyze/status:
 *   query_orchestrator · retrieval · recall · analyze · memory · themes · snapshot
 *
 * Node 4 fans out into Sentiment (RoBERTa∥LLM) ∥ Credibility (5 signals).
 * Node 6 fans out into the Theme Router + the 6 domain specialists.
 * Those fan-out lanes are the sub-agents the system actually spawns.
 */

type NodeDef = {
    id: string;
    index: number;
    label: string;
    detail: string;
    icon: React.ReactNode;
    workers?: { name: string; detail: string }[];
};

const NODES: NodeDef[] = [
    { id: "query_orchestrator", index: 1, label: "Query Orchestrator", detail: "ReAct planner · Gemini 2.5 Flash Lite", icon: <Radar className="h-4 w-4" aria-hidden="true" /> },
    { id: "retrieval", index: 2, label: "Retrieval Agent", detail: "LangSearch web · Tavily backfill", icon: <FileSearch className="h-4 w-4" aria-hidden="true" />, workers: [{ name: "LangSearch", detail: "primary search" }, { name: "Tavily", detail: "backfill + verify" }] },
    { id: "recall", index: 3, label: "RAG Recall", detail: "Qdrant internal memory · BGE-large", icon: <Brain className="h-4 w-4" aria-hidden="true" /> },
    { id: "analyze", index: 4, label: "Analysis", detail: "Ensemble sentiment ∥ 5-signal credibility", icon: <Zap className="h-4 w-4" aria-hidden="true" />, workers: [{ name: "Sentiment", detail: "RoBERTa ∥ Groq 5.4x" }, { name: "Credibility", detail: "Domain ∥ CrossRef ∥ FactChk ∥ LLM ∥ Tavily" }] },
    { id: "memory", index: 5, label: "Memory Consolidation", detail: "ContextAugmentation · writes RAG chunks", icon: <Database className="h-4 w-4" aria-hidden="true" /> },
    { id: "themes", index: 6, label: "Theme Agents", detail: "Router + 6 domain specialists", icon: <Target className="h-4 w-4" aria-hidden="true" />, workers: [{ name: "Infrastructure", detail: "roads, water, grid" }, { name: "Health", detail: "hospitals, dengue" }, { name: "Safety", detail: "crime, disaster" }, { name: "Tourism", detail: "visitors, events" }, { name: "Economy", detail: "markets, livelihood" }, { name: "Environment", detail: "waste, air, flood" }] },
    { id: "snapshot", index: 7, label: "Verification", detail: "NLI entailment · FaithfulnessAgent", icon: <ClipboardCheck className="h-4 w-4" aria-hidden="true" /> },
];

const TOTAL = NODES.length;

type NodeState = "done" | "active" | "pending";

function RailNode({ def, state }: { def: NodeDef; state: NodeState }) {
    const Icon = def.icon;
    const shown = state !== "pending";
    return (
        <div className={clsx(
            "relative z-10 flex items-start gap-3 rounded-xl border p-2 sm:p-2.5",
            "transition-all duration-300 ease-out motion-reduce:transition-none",
            state === "done" && "border-emerald-200/80 bg-white",
            state === "active" && "border-slate-900 bg-slate-900 text-white",
            !shown && "border-transparent bg-transparent",
        )}>
            <div aria-hidden="true" className={clsx(
                "flex h-8 w-8 sm:h-9 sm:w-9 shrink-0 items-center justify-center rounded-lg",
                "transition-colors duration-300 motion-reduce:transition-none",
                state === "done" && "bg-emerald-50 text-emerald-700",
                state === "active" && "bg-white/10 text-white",
                !shown && "text-slate-300",
            )}>
                {state === "done"
                    ? <CheckCircle2 className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />
                    : state === "active"
                        ? <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 motion-safe:animate-spin" aria-hidden="true" />
                        : Icon}
            </div>
            <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                    <p className={clsx(
                        "text-[9px] sm:text-[10px] font-semibold uppercase tracking-widest leading-none",
                        state === "active" && "text-white/60",
                        state === "done" && "text-emerald-700",
                        !shown && "text-slate-300",
                    )}>
                        Node {def.index}
                    </p>
                    {state === "active" && (
                        <span className="text-[8px] sm:text-[9px] font-medium uppercase tracking-widest text-sky-200">
                            running
                        </span>
                    )}
                </div>
                <p className={clsx(
                    "mt-1 text-[11px] sm:text-[12px] font-semibold leading-tight",
                    state === "active" && "text-white",
                    state === "done" && "text-slate-900",
                    !shown && "text-slate-400",
                )}>
                    {def.label}
                </p>
                <p className={clsx(
                    "mt-0.5 text-[8.5px] sm:text-[9.5px] leading-snug",
                    state === "active" && "text-white/65",
                    state === "done" && "text-slate-500",
                    !shown && "text-slate-300",
                )}>
                    {def.detail}
                </p>
            </div>
        </div>
    );
}

function FanOut({ def, state }: { def: NodeDef; state: NodeState }) {
    if (!def.workers || (state !== "active" && state !== "done")) return null;
    return (
        <div className="ml-9 sm:ml-11 mt-1.5 flex flex-wrap gap-1" aria-label={`Agents spawned by Node ${def.index}`}>
            {def.workers.map((w) => (
                <span key={w.name} className={clsx(
                    "inline-flex items-center gap-1.5 rounded-md border px-1.5 py-0.5",
                    "text-[8px] sm:text-[9px] font-medium transition-colors duration-300 motion-reduce:transition-none",
                    state === "active" && "border-slate-200 bg-slate-50 text-slate-700",
                    state === "done" && "border-emerald-200/70 bg-emerald-50/60 text-emerald-800",
                )}>
                    <span className={clsx(
                        "h-1.5 w-1.5 rounded-full",
                        state === "active" && "motion-safe:animate-pulse bg-amber-400",
                        state === "done" && "bg-emerald-500",
                    )} aria-hidden="true" />
                    <span className="leading-tight">{w.name}</span>
                    <span className="hidden sm:inline text-[7px] sm:text-[8px] font-normal opacity-70 leading-tight border-l pl-1.5 border-current/10">{w.detail}</span>
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
    const activeIndex = stageIndex >= 0 ? stageIndex : Math.min(TOTAL - 1, Math.floor(fill * TOTAL));

    const nodesVisible = NODES.slice(0, activeIndex + 1);

    return (
        <div role="status" aria-live="polite" aria-label="7-node pipeline progress" className="relative w-full max-w-md mx-auto mb-2 sm:mb-3 px-0 sm:px-1">
            <ol className="relative">
                <div aria-hidden="true" className="pointer-events-none absolute left-[15px] sm:left-[19px] top-4 bottom-4 w-px bg-slate-200">
                    <div className="absolute left-0 top-0 w-px origin-top bg-emerald-500 transition-transform duration-500 ease-out motion-reduce:transition-none" style={{ height: "100%", transform: `scaleY(${fill})` }} />
                </div>

                {nodesVisible.map((node, i) => {
                    const state: NodeState = i < activeIndex ? "done" : "active";
                    return (
                        <li key={node.id} className="relative mb-1.5 last:mb-0">
                            <RailNode def={node} state={state} />
                            <FanOut def={node} state={state} />
                        </li>
                    );
                })}

            </ol>

            {/* Trajectory progress */}
            <div className="mt-2.5 flex items-center gap-2">
                <div className="h-1 flex-1 bg-slate-100 rounded-full overflow-hidden" role="presentation">
                    <div className="h-full w-full origin-left bg-emerald-500 transition-transform duration-500 ease-out motion-reduce:transition-none" style={{ transform: `scaleX(${fill})` }} />
                </div>
                <span className="text-[9px] sm:text-[10px] font-mono font-semibold tabular-nums text-slate-500 w-8 text-right">{Math.round(fill * 100)}%</span>
            </div>
            <p className="mt-1.5 text-[9px] sm:text-[10px] text-slate-500 font-medium line-clamp-2 leading-snug">
                {message || "Initializing pipeline…"}
            </p>
        </div>
    );
}
