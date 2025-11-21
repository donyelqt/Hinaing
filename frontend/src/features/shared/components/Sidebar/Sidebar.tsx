import { BarChart3, Settings, Save, PieChart, LogOut } from "lucide-react";
import type { ActivePage } from "../../types/navigation";

type SidebarProps = {
  onOpenMobileFilters: () => void;
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
};

export function Sidebar({ onOpenMobileFilters, activePage = 'sentiment', onNavigate, onLogout }: SidebarProps & { onLogout?: () => void }) {
  console.log('🔍 Sidebar Debug - activePage:', activePage, 'onNavigate:', !!onNavigate);

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      return;
    }

    if (typeof window !== "undefined") {
      window.location.href = "/landing";
    }
  };
  
  return (
    <aside 
      className="order-2 flex flex-col rounded-2xl bg-white/80 backdrop-blur-sm border border-slate-200/50 p-6 shadow-sm lg:order-1 lg:w-[20rem] lg:flex-shrink-0 lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:sticky lg:top-8" 
      role="complementary" 
      aria-label="Navigation sidebar"
    >
      <div className="flex items-center justify-between lg:block">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Hinaing
          </span>
          <h1 className="mt-1 text-lg font-semibold text-slate-900 lg:mt-2 lg:text-2xl">
            Public Sentiment Suite
          </h1>
        </div>
        <button
          type="button"
          onClick={onOpenMobileFilters}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-500 transition hover:border-hinaing-blue-500 hover:text-hinaing-blue-600 lg:hidden"
          aria-label="Open filters"
        >
          <Settings className="h-4 w-4" />
          Filters
        </button>
      </div>

      <nav 
        className="mt-6 grid gap-2 sm:grid-cols-2 lg:mt-8 lg:grid-cols-1" 
        aria-label="Workspace navigation" 
        role="navigation"
      >
        <button
          type="button"
          onClick={() => onNavigate?.('sentiment')}
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${
            activePage === 'sentiment'
              ? 'bg-hinaing-blue-600 text-white border-2 border-hinaing-blue-700 shadow-lg'
              : 'text-slate-600 hover:bg-slate-100 border-2 border-transparent'
          }`}
          aria-current={activePage === 'sentiment' ? 'page' : undefined}
        >
          <BarChart3 className="h-5 w-5" aria-hidden="true" />
          <div>
            <p>Sentiment Generator</p>
            <p className={`text-xs ${activePage === 'sentiment' ? 'text-white/80' : 'text-slate-500'}`}>
              Live monitoring for Baguio City
            </p>
          </div>
        </button>
        
        <button
          type="button"
          onClick={() => onNavigate?.('dashboard')}
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${
            activePage === 'dashboard'
              ? 'bg-hinaing-blue-600 text-white border-2 border-hinaing-blue-700 shadow-lg'
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
          onClick={() => onNavigate?.('reports')}
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-colors ${
            activePage === 'reports'
              ? 'bg-hinaing-blue-600 text-white border-2 border-hinaing-blue-700 shadow-lg'
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

      <div className="mt-6 space-y-3 lg:mt-auto">
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
          className="rounded-xl bg-hinaing-blue-500/10 p-4 text-xs text-hinaing-blue-700 sm:text-sm" 
          role="note"
        >
          Keep track of emerging concerns from Facebook and Reddit to support rapid response planning for Baguio communities.
        </div>
      </div>
    </aside>
  );
}
