import clsx from "clsx";
import { X } from "lucide-react";
import { PLATFORM_OPTIONS, TIME_WINDOW_OPTIONS, FOCUS_OPTIONS } from '../constants';

type MobileFiltersProps = {
  showMobileFilters: boolean;
  setShowMobileFilters: (value: boolean) => void;
  platforms: string[];
  timeWindow: string;
  focusAreas: string[];
  includeAlerts: boolean;
  onToggleSelection: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  setPlatforms: (updater: (prev: string[]) => string[]) => void;
  setTimeWindow: (value: string) => void;
  setFocusAreas: (updater: (prev: string[]) => string[]) => void;
  setIncludeAlerts: (value: boolean) => void;
};

export function MobileFilters({
  showMobileFilters,
  setShowMobileFilters,
  platforms,
  timeWindow,
  focusAreas,
  includeAlerts,
  onToggleSelection,
  setPlatforms,
  setTimeWindow,
  setFocusAreas,
  setIncludeAlerts,
}: MobileFiltersProps) {
  if (!showMobileFilters) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div className="absolute inset-0 bg-black/50" onClick={() => setShowMobileFilters(false)} />
      <div className="absolute bottom-0 left-0 right-0 max-h-[85vh] overflow-y-auto rounded-t-2xl bg-white">
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4">
          <h2 className="text-lg font-semibold text-slate-900">Filter Options</h2>
          <button
            type="button"
            onClick={() => setShowMobileFilters(false)}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close filters"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4 space-y-6">
          {/* Platforms */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-900">Data Sources</h3>
            <div className="grid gap-3">
              {PLATFORM_OPTIONS.map((option) => {
                const isActive = platforms.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => onToggleSelection(option.value, setPlatforms)}
                    className={clsx(
                      "flex flex-col rounded-xl border px-4 py-3 text-left transition",
                      isActive
                        ? "border-hinaing-blue-500 bg-hinaing-blue-500/10 text-hinaing-blue-700"
                        : "border-slate-200 bg-white text-slate-600",
                    )}
                  >
                    <span className="font-medium">{option.label}</span>
                    {option.hint && <small className="text-xs text-slate-500">{option.hint}</small>}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Time Window */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-900">Time Window</h3>
            <div className="grid grid-cols-2 gap-3">
              {TIME_WINDOW_OPTIONS.map((option) => {
                const isActive = timeWindow === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setTimeWindow(option.value)}
                    className={clsx(
                      "rounded-xl border px-4 py-3 text-sm font-medium transition",
                      isActive
                        ? "border-hinaing-blue-500 bg-hinaing-blue-500/10 text-hinaing-blue-700"
                        : "border-slate-200 bg-white text-slate-600",
                    )}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Focus Areas */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-900">Focus Areas</h3>
            <div className="flex flex-wrap gap-2">
              {FOCUS_OPTIONS.map((option) => {
                const isActive = focusAreas.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => onToggleSelection(option.value, setFocusAreas)}
                    className={clsx(
                      "rounded-xl border px-3 py-2 text-sm font-medium transition",
                      isActive
                        ? "border-hinaing-blue-500 bg-hinaing-blue-500/10 text-hinaing-blue-600"
                        : "border-slate-200 bg-white text-slate-500",
                    )}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Alerts */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-900">Alert Preferences</h3>
            <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-slate-300 text-hinaing-blue-500 focus:ring-hinaing-blue-500"
                checked={includeAlerts}
                onChange={(event) => setIncludeAlerts(event.target.checked)}
              />
              <span>
                Include urgent alert summary
                <span className="mt-1 block text-xs text-slate-400">Alerts surface in the briefing header and notification digest.</span>
              </span>
            </label>
          </div>
          
          <div className="pt-4">
            <button
              type="button"
              onClick={() => setShowMobileFilters(false)}
              className="w-full rounded-xl bg-hinaing-blue-600 px-6 py-3 text-sm font-semibold text-white"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
