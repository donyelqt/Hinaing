import clsx from "clsx";
import { TIME_WINDOW_OPTIONS } from '../constants';

type TimeWindowSelectorProps = {
  timeWindow: string;
  setTimeWindow: (value: string) => void;
};

export function TimeWindowSelector({ timeWindow, setTimeWindow }: TimeWindowSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Step 2 · Monitoring window</span>
        <span className="text-[11px] text-slate-400">Align with your reporting cadence</span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {TIME_WINDOW_OPTIONS.map((option) => {
          const isActive = timeWindow === option.value;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => setTimeWindow(option.value)}
              aria-pressed={isActive}
              className={clsx(
                "rounded-xl border px-4 py-3 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2",
                isActive
                  ? "border-transparent bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-600 hover:border-violet-300",
              )}
              aria-label={`Set time window to ${option.label}`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
