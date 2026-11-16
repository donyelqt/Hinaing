"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { type LucideIcon, BarChart3, Settings, Save, PieChart, LogOut, Sparkles, Cpu, HelpCircle, Radar, FileSearch, Database, Zap, BrainCircuit, Target, ShieldCheck, ChevronsLeft, ChevronsRight } from "lucide-react";
import type { ActivePage } from "../../types/navigation";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HinaingLogo } from "@/components/ui/hinaing-logo";

const PIPELINE_NODES = [
  { icon: Radar, label: "Node 1: Query Orchestrator", sub: "ReAct Planning" },
  { icon: FileSearch, label: "Node 2: Document Retrieval", sub: "Multi-Source" },
  { icon: Database, label: "Node 3: RAG Memory Recall", sub: "Qdrant Vector DB" },
  { icon: Zap, label: "Node 4: Parallel Analysis", sub: "Sentiment + Credibility + Theme" },
  { icon: BrainCircuit, label: "Node 5: Memory Consolidation", sub: "Self-Learning Loop" },
  { icon: Target, label: "Node 6: 6 Theme Agents", sub: "Domain Specialists" },
  { icon: ShieldCheck, label: "Node 7: NLI Verification", sub: "100% Faithfulness" },
] satisfies { icon: LucideIcon; label: string; sub: string }[];

type SidebarProps = {
  onOpenMobileFilters: () => void;
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
  isSidebarOpen?: boolean;
  onCloseSidebar?: () => void;
};

// Module-level pill position cache so remounts (page → page) animate
// from the last known position instead of teleporting to the target slot.
let lastPillState: { top: number; height: number } | null = null;
// Survives page remounts within the session — prevents the rail snapping shut on every navigation.
let moduleCollapsedHint: boolean | null = null;

export function Sidebar({
  onOpenMobileFilters,
  activePage = 'sentiment',
  onNavigate,
  onLogout,
  isSidebarOpen = false,
  onCloseSidebar
}: SidebarProps & { onLogout?: () => void }) {
  const reduceMotion = useReducedMotion();
  const navRef = useRef<HTMLDivElement | null>(null);
  const [indicator, setIndicator] = useState({ top: 0, height: 0, ready: false });
  const [collapsed, setCollapsed] = useState<boolean>(() => (moduleCollapsedHint !== null ? moduleCollapsedHint : false));

  useLayoutEffect(() => {
    document.documentElement.dataset.sidebarCollapsed = collapsed ? 'true' : 'false';
  }, [collapsed]);

  useLayoutEffect(() => {
    try {
      const stored = window.localStorage.getItem('hinaing.sidebar.collapsed') === '1';
      if (moduleCollapsedHint === null) {
        moduleCollapsedHint = stored;
        setCollapsed(stored);
      }
    } catch { /* keep default expanded */ }
  }, []);
  useLayoutEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    const update = () => {
      const active = nav.querySelector<HTMLElement>('[data-active="true"]');
      if (!active) return;
      setIndicator({ top: active.offsetTop, height: active.offsetHeight, ready: true });
      lastPillState = { top: active.offsetTop, height: active.offsetHeight };
    };
    update();
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(update) : null;
    if (ro) ro.observe(nav);
    window.addEventListener("resize", update);
    return () => {
      ro?.disconnect();
      window.removeEventListener("resize", update);
    };
  }, [activePage, collapsed]);

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      return;
    }

    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };
  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      moduleCollapsedHint = next;
      try {
        window.localStorage.setItem('hinaing.sidebar.collapsed', next ? '1' : '0');
      } catch { /* storage unavailable */ }
      return next;
    });
  };
  const handleNavClick = (page: ActivePage) => {
    onNavigate?.(page);
    onCloseSidebar?.();
  };

  const buttonBase = collapsed
    ? "relative flex items-center justify-center rounded-xl border-2 border-transparent px-1 py-4 text-left text-sm font-medium transition-colors"
    : "relative flex items-center gap-3 rounded-xl border-2 border-transparent px-3 py-3 text-left text-sm font-medium transition-colors";

  return (
    <>
      {/* Mobile Overlay Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden animate-in fade-in duration-200"
          onClick={onCloseSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 bottom-0 z-40 w-[85%] max-w-sm
          flex flex-col bg-white border-r border-slate-200 p-6
          transform transition-[transform,width] duration-300 ease-in-out motion-reduce:transition-none
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:relative lg:z-auto lg:flex-shrink-0
          lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:overflow-x-hidden lg:sticky lg:top-8
          lg:rounded-2xl lg:bg-white lg:border lg:border-slate-200/60
          lg:transition-[width,padding] lg:duration-[350ms] lg:ease-[cubic-bezier(0.32,0.72,0,1)] lg:motion-reduce:transition-none
          ${collapsed ? 'lg:w-[5.5rem] lg:p-4 lg:items-center' : 'lg:w-[20rem]'}
        `}
        role="complementary"
        aria-label="Navigation sidebar"
      >
        <div className={`flex w-full items-center ${collapsed ? 'lg:flex-col lg:gap-4 lg:items-center lg:px-3' : 'justify-between'}`}>
          {collapsed && (
            <HinaingLogo className="hidden h-5 w-auto sm:h-6 lg:block" alt="Hinaing" priority />
          )}
          <div className={collapsed ? 'lg:hidden' : 'block'}>
            <HinaingLogo className="h-5 w-auto sm:h-6" alt="Hinaing" priority />
            <h1 className="mt-1 whitespace-nowrap text-lg font-semibold tracking-tight text-slate-900 lg:mt-1.5 sm:text-xl">
              Public Sentiment Suite
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Live monitoring
            </p>
          </div>

          {/* Collapse toggle (desktop rail) */}
          <button
            type="button"
            onClick={toggleCollapsed}
            className="hidden lg:inline-flex items-center justify-center rounded-xl border border-slate-200 p-2 text-slate-500 transition hover:border-violet-300 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
          >
            {collapsed ? (
              <ChevronsRight className="h-4 w-4" aria-hidden="true" />
            ) : (
              <ChevronsLeft className="h-4 w-4" aria-hidden="true" />
            )}
          </button>

          {/* Mobile Filters Button */}
          <button
            type="button"
            onClick={onOpenMobileFilters}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-500 transition hover:border-violet-300 hover:text-slate-900 lg:hidden"
            aria-label="Open filters"
          >
            <Settings className="h-4 w-4" aria-hidden="true" />
            Filters
          </button>
        </div>

        <div
          ref={navRef}
          className={`relative mt-6 grid gap-2 sm:grid-cols-1 lg:mt-8 isolate ${collapsed ? 'lg:px-3' : ''}`}
          aria-label="Workspace navigation"
          role="navigation"
        >
          <motion.span
            aria-hidden="true"
            className={`pointer-events-none absolute z-0 rounded-xl border-2 border-hinaing-blue-700 brand-gradient-y will-change-transform ${collapsed ? 'left-3 right-3' : 'left-0 right-0'}`}
            initial={{
              opacity: lastPillState ? 1 : 0,
              y: lastPillState ? lastPillState.top : 0,
            }}
            style={{ height: indicator.height || (lastPillState ? lastPillState.height : 0) }}
            animate={{ opacity: indicator.ready ? 1 : 0, y: indicator.top }}
            transition={reduceMotion ? { duration: 0 } : { type: "spring", bounce: 0.1, duration: 0.5 }}
          />

          <TooltipProvider>
          <button
            type="button"
            onClick={() => handleNavClick('sentiment')}
            data-active={activePage === 'sentiment' ? 'true' : 'false'}
            className={`${buttonBase} group ${activePage === 'sentiment' ? 'text-white' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-800'}`}
            aria-current={activePage === 'sentiment' ? 'page' : undefined}
          >
            <Cpu className={`${collapsed ? 'h-6 w-6' : 'h-5 w-5'} flex-shrink-0`} aria-hidden="true" />
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="truncate max-w-[180px]">Agentic Orchestrator</p>
                </div>
                <p className={`text-xs mt-0.5 ${activePage === 'sentiment' ? 'text-white/80' : 'text-slate-500'}`}>
                  7-Node & 19 Agents
                </p>
              </div>
            )}
            {!collapsed && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    className="p-1 rounded hover:bg-white/20 transition-colors flex-shrink-0"
                    onClick={(e) => e.stopPropagation()}
                    tabIndex={0}
                    role="button"
                    aria-label="Show pipeline help"
                  >
                    <HelpCircle className={`h-3.5 w-3.5 ${activePage === 'sentiment' ? 'text-white' : 'text-slate-500'}`} aria-hidden="true" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="right" align="start" className="w-72 bg-white z-[9999]">
                  <div className="font-bold mb-2 text-slate-900 text-sm">7-Node Multi-Agent Pipeline</div>
                  <div className="space-y-1.5 text-slate-700">
                    {PIPELINE_NODES.map(({ icon: Icon, label, sub }) => (
                      <div key={label} className="flex items-center gap-2">
                        <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                          <Icon className="h-4 w-4" aria-hidden="true" />
                        </span>
                        <div>
                          <div className="font-medium">{label}</div>
                          <div className="text-slate-500 text-[10px]">{sub}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-200 text-slate-600 text-[10px] font-medium">
                    <div className="flex items-center justify-between">
                      <span>19 Agents</span>
                      <span>•</span>
                      <span>100% Faithfulness</span>
                      <span>•</span>
                      <span>81% API Savings</span>
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            )}
          </button>
          </TooltipProvider>

          <button
            type="button"
            onClick={() => handleNavClick('dashboard')}
            data-active={activePage === 'dashboard' ? 'true' : 'false'}
            className={`${buttonBase} ${activePage === 'dashboard' ? 'text-white' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-800'}`}
            aria-current={activePage === 'dashboard' ? 'page' : undefined}
          >
            <PieChart className={`${collapsed ? 'h-6 w-6' : 'h-5 w-5'}`} aria-hidden="true" />
            {!collapsed && (
              <div>
                <p>Dashboard</p>
                <p className={`text-xs mt-0.5 ${activePage === 'dashboard' ? 'text-white/80' : 'text-slate-500'}`}>
                  Real-time insights & trends
                </p>
              </div>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('chat')}
            data-active={activePage === 'chat' ? 'true' : 'false'}
            className={`${buttonBase} ${activePage === 'chat' ? 'text-white' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-800'}`}
            aria-current={activePage === 'chat' ? 'page' : undefined}
          >
            <Sparkles className={`${collapsed ? 'h-6 w-6' : 'h-5 w-5'}`} aria-hidden="true" />
            {!collapsed && (
              <div>
                <p>Agentic RAG</p>
                <p className={`text-xs mt-0.5 ${activePage === 'chat' ? 'text-white/80' : 'text-slate-500'}`}>
                  Quick Q&A
                </p>
              </div>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('analyze')}
            data-active={activePage === 'analyze' ? 'true' : 'false'}
            className={`${buttonBase} ${activePage === 'analyze' ? 'text-white' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-800'}`}
            aria-current={activePage === 'analyze' ? 'page' : undefined}
          >
            <BarChart3 className={`${collapsed ? 'h-6 w-6' : 'h-5 w-5'}`} aria-hidden="true" />
            {!collapsed && (
              <div>
                <p>AgenticHinaing</p>
                <p className={`text-xs mt-0.5 ${activePage === 'analyze' ? 'text-white/80' : 'text-slate-500'}`}>
                  7-Node & 19 Agents + Agentic RAG
                </p>
              </div>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('reports')}
            data-active={activePage === 'reports' ? 'true' : 'false'}
            className={`${buttonBase} ${activePage === 'reports' ? 'text-white' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-800'}`}
            aria-current={activePage === 'reports' ? 'page' : undefined}
          >
            <Save className={`${collapsed ? 'h-6 w-6' : 'h-5 w-5'}`} aria-hidden="true" />
            {!collapsed && (
              <div>
                <p>Saved Reports</p>
                <p className={`text-xs mt-0.5 ${activePage === 'reports' ? 'text-white/80' : 'text-slate-500'}`}>
                  Access generated reports
                </p>
              </div>
            )}
          </button>
        </div>

        <div className="mt-auto space-y-3 pt-6">
          <button
            type="button"
            onClick={handleLogout}
            className={`inline-flex w-full items-center ${collapsed ? 'justify-center px-2' : 'justify-between px-3'} rounded-xl border border-slate-200 py-2 text-xs font-medium text-slate-600 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700`}
            aria-label="Log out"
          >
            {collapsed ? (
              <LogOut className={`${collapsed ? 'h-6 w-6' : 'h-4 w-4'}`} aria-hidden="true" />
            ) : (
              <>
                <span className="flex items-center gap-2">
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  <span>Log out</span>
                </span>
                <span className="text-[11px] text-slate-500">End session</span>
              </>
            )}
          </button>

          {!collapsed && (
          <div
            className="rounded-xl bg-[linear-gradient(135deg,rgb(var(--brand-from-rgb)_/_0.08)_0%,rgb(var(--brand-to-rgb)_/_0.08)_100%)] border border-slate-200/60 p-4 text-xs text-slate-700 sm:text-sm"
            role="note"
          >
            Keep track of emerging concerns from Web, Facebook, and Reddit to support rapid response planning for Baguio communities.
          </div>
          )}
        </div>
      </aside>
    </>
  );
}
