import { useState, useMemo, useCallback } from 'react';
import { PLATFORM_OPTIONS, TIME_WINDOW_OPTIONS, FOCUS_OPTIONS, PRESET_OPTIONS } from '../constants';
import type { SentimentState, SentimentActions } from '../types';

export type ValidationErrors = {
  platforms?: string;
  timeWindow?: string;
  focusAreas?: string;
};

export type GenerationProgress = {
  stage: string;
  message: string;
  progress: number; // 0.0 to 1.0
};

// Backend workflow stages for progress display (aligned with graph.py)
export const WORKFLOW_STAGES = [
  { id: 'query_orchestrator', label: 'Query Orchestrator', icon: '📡', description: 'Generating diverse search queries...' },
  { id: 'retrieval', label: 'Document Retrieval', icon: '🔍', description: 'Searching across platforms...' },
  { id: 'analyze', label: 'Analysis', icon: '⚡', description: 'Sentiment + Credibility + Themes (parallel)...' },
  { id: 'context', label: 'Context Augmentation', icon: '🔗', description: 'Augmenting with RAG...' },
  { id: 'themes', label: 'Theme Insights', icon: '🎯', description: 'Generating insights...' },
] as const;

export function useSentimentGenerator() {
  // State
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [timeWindow, setTimeWindow] = useState<string>("");
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [includeAlerts, setIncludeAlerts] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showMobileFilters, setShowMobileFilters] = useState<boolean>(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

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

  // Validation
  const validate = useCallback((): ValidationErrors => {
    const errors: ValidationErrors = {};
    
    // Step 1: Platform validation
    if (platforms.length === 0) {
      errors.platforms = "Please select at least one data source";
    }
    
    // Step 2: Time window validation
    if (!timeWindow) {
      errors.timeWindow = "Please select a time window";
    }
    
    // Step 3: Focus areas validation
    if (focusAreas.length === 0) {
      errors.focusAreas = "Please select at least one focus area";
    }
    
    return errors;
  }, [platforms, timeWindow, focusAreas]);

  const isValid = useMemo(() => {
    return platforms.length > 0 && timeWindow !== "" && focusAreas.length > 0;
  }, [platforms, timeWindow, focusAreas]);

  const clearValidationErrors = useCallback(() => {
    setValidationErrors({});
  }, []);

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

  const validation = {
    errors: validationErrors,
    setErrors: setValidationErrors,
    validate,
    isValid,
    clearErrors: clearValidationErrors,
  };

  return {
    state,
    actions,
    computed,
    validation,
  };
}
