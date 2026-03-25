import { useState } from "react";
import { BarChart3, Settings, Save, PieChart, LogOut, Menu, X, Sparkles, Cpu, HelpCircle } from "lucide-react";
import type { ActivePage } from "../../types/navigation";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

type SidebarProps = {
  onOpenMobileFilters: () => void;
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
  isSidebarOpen?: boolean;
  onCloseSidebar?: () => void;
};

export function Sidebar({
  onOpenMobileFilters,
  activePage = 'sentiment',
  onNavigate,
  onLogout,
  isSidebarOpen = false,
  onCloseSidebar
}: SidebarProps & { onLogout?: () => void }) {
  console.log('🔍 Sidebar Debug - activePage:', activePage, 'onNavigate:', !!onNavigate);

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      return;
    }

    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  const handleNavClick = (page: ActivePage) => {
    onNavigate?.(page);
    onCloseSidebar?.();
  };

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
          flex flex-col bg-white border-r border-slate-200 p-6 shadow-xl
          transform transition-transform duration-300 ease-in-out
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:relative lg:z-auto lg:w-[20rem] lg:flex-shrink-0
          lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:overflow-x-hidden lg:sticky lg:top-8
          lg:rounded-2xl lg:bg-white/80 lg:backdrop-blur-sm lg:border lg:border-slate-200/50 lg:shadow-sm
        `}
        role="complementary"
        aria-label="Navigation sidebar"
      >
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Hinaing
            </span>
            <h1 className="mt-1 text-lg font-semibold text-slate-900 lg:mt-2 lg:text-2xl">
              Public Sentiment Suite
            </h1>
          </div>

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

        <nav
          className="mt-6 grid gap-2 sm:grid-cols-1 lg:mt-8 isolate"
          aria-label="Workspace navigation"
          role="navigation"
        >
          <TooltipProvider>
          <button
            type="button"
            onClick={() => handleNavClick('sentiment')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'sentiment'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'sentiment' ? 'page' : undefined}
          >
            <Cpu className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="truncate">Agentic Orchestrator</p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="p-0.5 rounded hover:bg-white/10 transition-colors"
                      aria-label="Show pipeline help"
                    >
                      <HelpCircle className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" align="start" className="w-72 bg-white">
                    <div className="font-bold mb-2 text-slate-900 text-sm">7-Node Multi-Agent Pipeline</div>
                    <div className="space-y-1.5 text-slate-700">
                      <div className="flex items-center gap-2">
                        <span className="text-base">📡</span>
                        <div>
                          <div className="font-medium">Node 1: Query Orchestrator</div>
                          <div className="text-slate-500 text-[10px]">ReAct Planning</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">🔍</span>
                        <div>
                          <div className="font-medium">Node 2: Document Retrieval</div>
                          <div className="text-slate-500 text-[10px]">Multi-Source</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">🔗</span>
                        <div>
                          <div className="font-medium">Node 3: RAG Memory Recall</div>
                          <div className="text-slate-500 text-[10px]">Qdrant Vector DB</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">⚡</span>
                        <div>
                          <div className="font-medium">Node 4: Parallel Analysis</div>
                          <div className="text-slate-500 text-[10px]">Sentiment + Credibility + Theme</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">💾</span>
                        <div>
                          <div className="font-medium">Node 5: Memory Consolidation</div>
                          <div className="text-slate-500 text-[10px]">Self-Learning Loop</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">🎯</span>
                        <div>
                          <div className="font-medium">Node 6: 6 Theme Agents</div>
                          <div className="text-slate-500 text-[10px]">Domain Specialists</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-base">✅</span>
                        <div>
                          <div className="font-medium">Node 7: NLI Verification</div>
                          <div className="text-slate-500 text-[10px]">100% Faithfulness</div>
                        </div>
                      </div>
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
              </div>
              <p className={`text-xs mt-0.5 truncate ${activePage === 'sentiment' ? 'text-white/80' : 'text-slate-500'}`}>
                Live monitoring • 7-Node Multi-Agent Pipeline
              </p>
            </div>
          </button>
          </TooltipProvider>

          <button
            type="button"
            onClick={() => handleNavClick('dashboard')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'dashboard'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'dashboard' ? 'page' : undefined}
          >
            <PieChart className="h-5 w-5" aria-hidden="true" />
            <div>
              <p>Dashboard</p>
              <p className={`text-xs mt-0.5 ${activePage === 'dashboard' ? 'text-white/80' : 'text-slate-500'}`}>
                Real-time insights & trends
              </p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('chat')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'chat'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'chat' ? 'page' : undefined}
          >
            <Sparkles className="h-5 w-5" aria-hidden="true" />
            <div>
              <p>Agentic RAG</p>
              <p className={`text-xs mt-0.5 ${activePage === 'chat' ? 'text-white/80' : 'text-slate-500'}`}>
                Quick Q&A
              </p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('analyze')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'analyze'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'analyze' ? 'page' : undefined}
          >
            <BarChart3 className="h-5 w-5" aria-hidden="true" />
            <div>
              <p>AgenticHinaing</p>
              <p className={`text-xs mt-0.5 ${activePage === 'analyze' ? 'text-white/80' : 'text-slate-500'}`}>
                7-Node & 19 Agents + Agentic RAG
              </p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleNavClick('reports')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'reports'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'reports' ? 'page' : undefined}
          >
            <Save className="h-5 w-5" aria-hidden="true" />
            <div>
              <p>Saved Reports</p>
              <p className={`text-xs mt-0.5 ${activePage === 'reports' ? 'text-white/80' : 'text-slate-500'}`}>
                Access generated reports
              </p>
            </div>
          </button>
        </nav>

        <div className="mt-auto space-y-3 pt-6">
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex w-full items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700"
            aria-label="Log out"
          >
            <span className="flex items-center gap-2">
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span>Log out</span>
            </span>
            <span className="text-[11px] text-slate-400">End session</span>
          </button>

          <div
            className="rounded-xl bg-gradient-to-r from-hinaing-blue-500/10 via-hinaing-blue-400/10 to-violet-500/10 p-4 text-xs text-hinaing-blue-800 sm:text-sm"
            role="note"
          >
            Keep track of emerging concerns from Web, Facebook, and Reddit to support rapid response planning for Baguio communities.
          </div>
        </div>
      </aside>
    </>
  );
}
