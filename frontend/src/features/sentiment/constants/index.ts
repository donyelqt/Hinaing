import type { ToggleOption, PresetOption, GeneratorStep } from '../types';

export const PLATFORM_OPTIONS: ToggleOption[] = [
  { value: "facebook", label: "Facebook", hint: "Pages & public groups" },
  { value: "reddit", label: "Reddit", hint: "Local subreddits" },
];

export const TIME_WINDOW_OPTIONS: ToggleOption[] = [
  { value: "6h", label: "Past 6 hours" },
  { value: "24h", label: "Past 24 hours" },
  { value: "3d", label: "Past 3 days" },
  { value: "7d", label: "Past 7 days" },
];

export const FOCUS_OPTIONS: ToggleOption[] = [
  { value: "infrastructure", label: "Infrastructure" },
  { value: "health", label: "Health & Wellness" },
  { value: "safety", label: "Public Safety" },
  { value: "tourism", label: "Tourism & Events" },
  { value: "economy", label: "Business & Economy" },
  { value: "environment", label: "Environment" },
];

export const PRESET_OPTIONS: PresetOption[] = [
  {
    id: "daily-ops",
    name: "Daily Operations",
    description: "Traffic, utilities, and safety updates",
    platforms: ["facebook", "reddit"],
    focusAreas: ["infrastructure", "safety", "environment"],
    window: "24h",
  },
  {
    id: "health-watch",
    name: "Health Watch",
    description: "Hospitals, clinics, and wellness concerns",
    platforms: ["facebook"],
    focusAreas: ["health", "environment"],
    window: "3d",
  },
  {
    id: "tourism-pulse",
    name: "Tourism Pulse",
    description: "Visitor sentiment and events",
    platforms: ["facebook", "reddit"],
    focusAreas: ["tourism", "economy"],
    window: "7d",
  },
];

export const GENERATOR_STEPS: GeneratorStep[] = [
  {
    title: "Review coverage",
    description: "Confirm barangays and hashtags you want the agent to monitor.",
  },
  {
    title: "Select channels",
    description: "Pick the data sources and time window for this run.",
  },
  {
    title: "Prioritize themes",
    description: "Highlight the topics that need immediate attention.",
  },
  {
    title: "Set outputs",
    description: "Choose alerts and delivery preferences for your briefing.",
  },
];
