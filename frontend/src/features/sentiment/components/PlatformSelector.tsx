import clsx from "clsx";
import { PLATFORM_OPTIONS } from '../constants';

type PlatformSelectorProps = {
  platforms: string[];
  onToggle: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  setPlatforms: (updater: (prev: string[]) => string[]) => void;
};

export function PlatformSelector({ platforms, onToggle, setPlatforms }: PlatformSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Step 1 · Select channels</span>
        <span className="text-[11px] text-slate-400">Choose where the agent listens</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {PLATFORM_OPTIONS.map((option) => {
          const isActive = platforms.includes(option.value);
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onToggle(option.value, setPlatforms)}
              aria-pressed={isActive}
              className={clsx(
                "flex flex-col rounded-xl border px-4 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2",
                isActive
                  ? "border-transparent bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-600 hover:border-violet-300",
              )}
              aria-label={`${isActive ? 'Disable' : 'Enable'} ${option.label} platform`}
            >
              <span className="font-medium">{option.label}</span>
              {option.hint ? (
                <small
                  className={clsx(
                    "text-xs",
                    isActive ? "text-white/80" : "text-slate-500",
                  )}
                >
                  {option.hint}
                </small>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}
