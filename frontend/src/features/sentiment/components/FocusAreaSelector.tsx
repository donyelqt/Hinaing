import clsx from "clsx";
import { FOCUS_OPTIONS } from '../constants';

type FocusAreaSelectorProps = {
  focusAreas: string[];
  onToggle: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  setFocusAreas: (updater: (prev: string[]) => string[]) => void;
  error?: string;
};

export function FocusAreaSelector({ focusAreas, onToggle, setFocusAreas, error }: FocusAreaSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className={clsx(
          "text-xs font-semibold uppercase tracking-wide",
          error ? "text-rose-500" : "text-slate-400"
        )}>Step 3 · Prioritize themes</span>
        <span className="text-[11px] text-slate-400">Highlight topics for summarization</span>
      </div>
      {error && (
        <p className="text-xs text-rose-500 font-medium">{error}</p>
      )}
      <div className="flex flex-wrap gap-2 sm:gap-3">
        {FOCUS_OPTIONS.map((option) => {
          const isActive = focusAreas.includes(option.value);
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onToggle(option.value, setFocusAreas)}
              aria-pressed={isActive}
              className={clsx(
                "rounded-xl border px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5b3cc8] focus-visible:ring-offset-2 touch-manipulation",
                isActive
                  ? "border-transparent bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-500 hover:border-[#5b3cc8]/40 hover:bg-[linear-gradient(135deg,rgba(51,72,184,0.04)_0%,rgba(91,60,200,0.06)_100%)] hover:shadow-[0_4px_12px_-4px_rgba(51,72,184,0.12)]",
              )}
              aria-label={`${isActive ? 'Remove' : 'Add'} ${option.label} focus area`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
