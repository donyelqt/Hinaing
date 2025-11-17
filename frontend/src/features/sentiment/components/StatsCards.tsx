import type { ToggleOption } from '../types';

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
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Current window</span>
        <p className="mt-2 text-lg font-semibold text-slate-900">{selectedWindowLabel}</p>
        <p className="text-sm text-slate-500">Last refreshed 5 mins ago</p>
      </div>
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Platforms tracked</span>
        <p className="mt-2 text-lg font-semibold text-slate-900">{platformSummary.length}</p>
        <p className="text-sm text-slate-500">{platformSummaryLabel}</p>
      </div>
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Focus coverage</span>
        <p className="mt-2 text-lg font-semibold text-slate-900">{focusSummary.length} priorit{focusSummary.length === 1 ? "y" : "ies"}</p>
        <p className="text-sm text-slate-500">{focusSummaryLabel}</p>
      </div>
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Alert summary</span>
        <p className="mt-2 text-lg font-semibold text-slate-900">{includeAlerts ? "Active" : "Disabled"}</p>
        <p className="text-sm text-slate-500">Urgent notifications {includeAlerts ? "included" : "excluded"} in report</p>
      </div>
    </div>
  );
}
