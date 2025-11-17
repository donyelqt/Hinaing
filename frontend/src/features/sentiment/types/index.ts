export type ToggleOption = {
  value: string;
  label: string;
  hint?: string;
};

export type PresetOption = {
  id: string;
  name: string;
  description: string;
  platforms: string[];
  focusAreas: string[];
  window: string;
};

export type GeneratorStep = {
  title: string;
  description: string;
};

export type SentimentState = {
  platforms: string[];
  timeWindow: string;
  focusAreas: string[];
  includeAlerts: boolean;
  isGenerating: boolean;
  isRefreshing: boolean;
  showMobileFilters: boolean;
};

export type SentimentActions = {
  setPlatforms: (updater: (prev: string[]) => string[]) => void;
  setTimeWindow: (value: string) => void;
  setFocusAreas: (updater: (prev: string[]) => string[]) => void;
  setIncludeAlerts: (value: boolean) => void;
  setIsGenerating: (value: boolean) => void;
  setIsRefreshing: (value: boolean) => void;
  setShowMobileFilters: (value: boolean) => void;
  toggleSelection: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  applyPreset: (presetId: string) => void;
};
