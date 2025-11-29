import type { ToggleOption } from '../types';
import { Clock, Layers, Target, Bell } from 'lucide-react';

type StatsCardsProps = {
  selectedWindowLabel: string;
  platformSummary: ToggleOption[];
  platformSummaryLabel: string;
  focusSummary: ToggleOption[];
  focusSummaryLabel: string;
  includeAlerts: boolean;
};

export function StatsCards({
  selectedWindowLabel,
  platformSummary,
  platformSummaryLabel,
  focusSummary,
  focusSummaryLabel,
  includeAlerts,
}: StatsCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div className="group rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md hover:border-violet-100">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-violet-500 transition-colors">Current window</span>
            <p className="mt-2 text-xl font-bold text-slate-900">{selectedWindowLabel}</p>
          </div>
          <div className="rounded-full bg-violet-50 p-2 text-violet-500 group-hover:bg-violet-100 transition-colors">
            <Clock className="h-4 w-4" />
          </div>
        </div>
        <p className="mt-2 text-xs font-medium text-slate-500">Last refreshed 5 mins ago</p>
      </div>

      <div className="group rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md hover:border-blue-100">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-blue-500 transition-colors">Platforms</span>
            <p className="mt-2 text-xl font-bold text-slate-900">{platformSummary.length}</p>
          </div>
          <div className="rounded-full bg-blue-50 p-2 text-blue-500 group-hover:bg-blue-100 transition-colors">
            <Layers className="h-4 w-4" />
          </div>
        </div>
        <p className="mt-2 text-xs font-medium text-slate-500 truncate">{platformSummaryLabel}</p>
      </div>

      <div className="group rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md hover:border-emerald-100">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-emerald-500 transition-colors">Focus Areas</span>
            <p className="mt-2 text-xl font-bold text-slate-900">{focusSummary.length}</p>
          </div>
          <div className="rounded-full bg-emerald-50 p-2 text-emerald-500 group-hover:bg-emerald-100 transition-colors">
            <Target className="h-4 w-4" />
          </div>
        </div>
        <p className="mt-2 text-xs font-medium text-slate-500 truncate">{focusSummaryLabel}</p>
      </div>

      <div className="group rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md hover:border-amber-100">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 group-hover:text-amber-500 transition-colors">Alerts</span>
            <p className="mt-2 text-xl font-bold text-slate-900">{includeAlerts ? "Active" : "Off"}</p>
          </div>
          <div className={`rounded-full p-2 transition-colors ${includeAlerts ? 'bg-amber-50 text-amber-500 group-hover:bg-amber-100' : 'bg-slate-50 text-slate-400'}`}>
            <Bell className="h-4 w-4" />
          </div>
        </div>
        <p className="mt-2 text-xs font-medium text-slate-500">
          {includeAlerts ? "Urgent notifications on" : "Notifications disabled"}
        </p>
      </div>
    </div>
  );
}
