import clsx from "clsx";
import { TIME_WINDOW_OPTIONS } from '../constants';

type TimeWindowSelectorProps = {
  timeWindow: string;
  setTimeWindow: (value: string) => void;
  error?: string;
};

export function TimeWindowSelector({ timeWindow, setTimeWindow, error }: TimeWindowSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className={clsx(
          "text-xs font-semibold uppercase tracking-wide",
          error ? "text-rose-500" : "text-slate-400"
        )}>Step 2 · Monitoring window</span>
        <span className="text-[11px] text-slate-400">Align with your reporting cadence</span>
      </div>
      {error && (
        <p className="text-xs text-rose-500 font-medium">{error}</p>
      )}
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
                "rounded-xl border px-4 py-3 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5b3cc8] focus-visible:ring-offset-2 touch-manipulation",
                isActive
                  ? "border-transparent bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-600 hover:border-[#5b3cc8]/40 hover:bg-[linear-gradient(135deg,rgba(51,72,184,0.04)_0%,rgba(91,60,200,0.06)_100%)] hover:shadow-[0_4px_12px_-4px_rgba(51,72,184,0.12)]",
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
