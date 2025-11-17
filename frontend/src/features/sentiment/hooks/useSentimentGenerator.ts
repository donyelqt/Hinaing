import { useState, useMemo } from 'react';
import { PLATFORM_OPTIONS, TIME_WINDOW_OPTIONS, FOCUS_OPTIONS, PRESET_OPTIONS } from '../constants';
import type { SentimentState, SentimentActions } from '../types';

export function useSentimentGenerator() {
  // State
  const [platforms, setPlatforms] = useState<string[]>(
    PLATFORM_OPTIONS.map((option) => option.value)
  );
  const [timeWindow, setTimeWindow] = useState<string>(TIME_WINDOW_OPTIONS[1].value);
  const [focusAreas, setFocusAreas] = useState<string[]>([
    FOCUS_OPTIONS[0].value,
    FOCUS_OPTIONS[1].value,
  ]);
  const [includeAlerts, setIncludeAlerts] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showMobileFilters, setShowMobileFilters] = useState<boolean>(false);

  // Computed values
  const platformSummary = useMemo(
    () => PLATFORM_OPTIONS.filter((option) => platforms.includes(option.value)),
    [platforms]
  );

  const focusSummary = useMemo(
    () => FOCUS_OPTIONS.filter((option) => focusAreas.includes(option.value)),
    [focusAreas]
  );

  const selectedWindowLabel = useMemo(
    () => TIME_WINDOW_OPTIONS.find((option) => option.value === timeWindow)?.label ?? "Custom range",
    [timeWindow]
  );

  const focusSummaryLabel = useMemo(() => {
    const labels = focusSummary.map((item) => item.label);
    if (labels.length === 0) {
      return "Select focus areas to prioritize city responses.";
    }
    if (labels.length <= 3) {
      return labels.join(", ");
    }
    return `${labels.slice(0, 3).join(", ")} +${labels.length - 3} more`;
  }, [focusSummary]);

  const platformSummaryLabel = useMemo(() => {
    const labels = platformSummary.map((item) => item.label);
    if (labels.length === 0) {
      return "Enable at least one platform to gather sentiment.";
    }
    if (labels.length === 1) {
      return labels[0];
    }
    return labels.join(" • ");
  }, [platformSummary]);

  // Actions
  const toggleSelection = (
    value: string,
    setState: (updater: (prev: string[]) => string[]) => void
  ) => {
    setState((prev) => {
      if (prev.includes(value)) {
        return prev.filter((item) => item !== value);
      }
      return [...prev, value];
    });
  };

  const applyPreset = (presetId: string) => {
    const preset = PRESET_OPTIONS.find((option) => option.id === presetId);
    if (!preset) return;
    setPlatforms(preset.platforms);
    setFocusAreas(preset.focusAreas);
    setTimeWindow(preset.window);
    setIncludeAlerts(true);
  };

  const state: SentimentState = {
    platforms,
    timeWindow,
    focusAreas,
    includeAlerts,
    isGenerating,
    isRefreshing,
    showMobileFilters,
  };

  const actions: SentimentActions = {
    setPlatforms,
    setTimeWindow,
    setFocusAreas,
    setIncludeAlerts,
    setIsGenerating,
    setIsRefreshing,
    setShowMobileFilters,
    toggleSelection,
    applyPreset,
  };

  const computed = {
    platformSummary,
    focusSummary,
    selectedWindowLabel,
    focusSummaryLabel,
    platformSummaryLabel,
  };

  return {
    state,
    actions,
    computed,
  };
}
