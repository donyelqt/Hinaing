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
    <fieldset className="space-y-3 border-0 p-0 m-0">
      <div className="flex items-center justify-between">
        <legend className={clsx(
          "text-xs font-semibold uppercase tracking-wide",
          error ? "text-rose-500" : "text-slate-400"
        )}>Step 1 · Select channels</legend>
        <span id="channels-hint" className="text-[11px] text-slate-400">Choose where the agent listens</span>
      </div>
      {error && (
        <p id="channels-error" role="alert" aria-live="polite" className="text-xs text-rose-500 font-medium">{error}</p>
      )}
      <div role="group" aria-labelledby="channels-hint" aria-describedby={error ? "channels-error" : undefined} className="grid gap-3 sm:grid-cols-2">
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
              aria-describedby={isDisabled ? `${option.value}-coming-soon` : undefined}
              className={clsx(
                "flex flex-col rounded-xl border min-h-[44px] px-4 py-3 text-left touch-manipulation transition-[transform,box-shadow,border-color] focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2",
                isDisabled
                  ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 opacity-60"
                  : isActive
                    ? "border-transparent bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 text-white shadow-sm hover:brightness-[1.03] active:scale-[0.99]"
                    : "border-slate-200 bg-white text-slate-600 hover:border-violet-300 hover:shadow-sm active:scale-[0.99]",
              )}
              aria-label={`${isDisabled ? 'Unavailable' : isActive ? 'Disable' : 'Enable'} ${option.label} platform`}
            >
              <span className="font-medium">{option.label}</span>
              {option.hint || isDisabled ? (
                <small
                  id={isDisabled ? `${option.value}-coming-soon` : undefined}
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
    </fieldset>
  );
}

