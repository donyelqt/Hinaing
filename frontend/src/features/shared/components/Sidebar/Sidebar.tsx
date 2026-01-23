import { useState } from "react";
import { BarChart3, Settings, Save, PieChart, LogOut, Menu, X, Sparkles } from "lucide-react";
import type { ActivePage } from "../../types/navigation";

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
          lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:sticky lg:top-8
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
          <button
            type="button"
            onClick={() => handleNavClick('sentiment')}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${activePage === 'sentiment'
              ? 'bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
              }`}
            aria-current={activePage === 'sentiment' ? 'page' : undefined}
          >
            <BarChart3 className="h-5 w-5" aria-hidden="true" />
            <div>
              <p>Sentiment Generator</p>
              <p className={`text-xs ${activePage === 'sentiment' ? 'text-white/80' : 'text-slate-500'}`}>
                Live monitoring (Hinaing Multi-Agent System)
              </p>
            </div>
          </button>

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
              <p className={`text-xs ${activePage === 'dashboard' ? 'text-white/80' : 'text-slate-500'}`}>
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
              <p>AI Assistant</p>
              <p className={`text-xs ${activePage === 'chat' ? 'text-white/80' : 'text-slate-500'}`}>
                Quick Q&A (Agentic RAG)
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
              <p>Chat Analyzer</p>
              <p className={`text-xs ${activePage === 'analyze' ? 'text-white/80' : 'text-slate-500'}`}>
                Multi-agent analysis in chat (Thesis Novelty)
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
              <p className={`text-xs ${activePage === 'reports' ? 'text-white/80' : 'text-slate-500'}`}>
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
