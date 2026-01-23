import clsx from "clsx";
import { PLATFORM_OPTIONS } from '../constants';

type PlatformSelectorProps = {
  platforms: string[];
  onToggle: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  setPlatforms: (updater: (prev: string[]) => string[]) => void;
  error?: string;
};

export function PlatformSelector({ platforms, onToggle, setPlatforms, error }: PlatformSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className={clsx(
          "text-xs font-semibold uppercase tracking-wide",
          error ? "text-rose-500" : "text-slate-400"
        )}>Step 1 · Select channels</span>
        <span className="text-[11px] text-slate-400">Choose where the agent listens</span>
      </div>
      {error && (
        <p className="text-xs text-rose-500 font-medium">{error}</p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {PLATFORM_OPTIONS.map((option) => {
          const isActive = platforms.includes(option.value);
          const isDisabled = option.value === "facebook" || option.value === "reddit";
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => !isDisabled && onToggle(option.value, setPlatforms)}
              disabled={isDisabled}
              aria-pressed={isActive}
              aria-disabled={isDisabled}
              className={clsx(
                "flex flex-col rounded-xl border px-4 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2",
                isDisabled
                  ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 opacity-60"
                  : isActive
                    ? "border-transparent bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white shadow-sm"
                    : "border-slate-200 bg-white text-slate-600 hover:border-violet-300",
              )}
              aria-label={`${isDisabled ? 'Unavailable' : isActive ? 'Disable' : 'Enable'} ${option.label} platform`}
            >
              <span className="font-medium">{option.label}</span>
              {option.hint ? (
                <small
                  className={clsx(
                    "text-xs",
                    isDisabled ? "text-slate-400" : isActive ? "text-white/80" : "text-slate-500",
                  )}
                >
                  {isDisabled ? "Coming soon" : option.hint}
                </small>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}
