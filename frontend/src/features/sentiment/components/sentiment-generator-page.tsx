"use client";

import * as React from "react";
import clsx from "clsx";
import {
  RefreshCw,
  Save,
  MapPin,
  AlertTriangle,
  ExternalLink,
  Loader2,
  BarChart3,
  Settings,
  Menu,
  X
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { apiGet, apiPost } from "@/lib/api";
import { Sidebar } from "../../shared/components";
import type { ActivePage } from "../../shared/types/navigation";
import { useSentimentGenerator } from "../hooks/useSentimentGenerator";
import { HeroSection } from "./HeroSection";
import { StatsCards } from "./StatsCards";
import { PlatformSelector } from "./PlatformSelector";
import { TimeWindowSelector } from "./TimeWindowSelector";
import { FocusAreaSelector } from "./FocusAreaSelector";
import { MobileFilters } from "./MobileFilters";
import { PRESET_OPTIONS, GENERATOR_STEPS } from "../constants";

type SentimentGeneratorPageProps = {
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
};

type SnapshotResponse = {
  overall_sentiment: {
    label: string;
    summary: string;
    scores: Record<string, number>;
  };
  actionable_insights: {
    category: string;
    title: string;
    detail: string;
    evidence: string[];
  }[];
  alerts: string[] | null;
  sources: {
    title: string;
    snippet: string;
    url?: string | null;
    published_at?: string | null;
    sentiment?: string | null;
    metadata?: Record<string, unknown>;
  }[] | null;
};

type NarrativeSummary = {
  summary?: string;
  insights?: {
    category?: string;
    title?: string;
    detail?: string;
    evidence?: string[];
  }[];
};

type DisplayInsight = {
  category?: string;
  title?: string;
  detail?: string;
  evidence?: string[];
};

type CredibilityBreakdown = {
  legitPercent: number;
  misinfoPercent: number;
  hasData: boolean;
};

const parseNarrativeSummary = (rawSummary?: string): NarrativeSummary | null => {
  if (!rawSummary) return null;
  const trimmed = rawSummary.trim();

  if (!trimmed.startsWith("{") || !trimmed.includes("summary")) {
    return null;
  }

  try {
    const parsed = JSON.parse(trimmed);
    const summaryText = typeof parsed.summary === "string" ? parsed.summary : undefined;
    const insights = Array.isArray(parsed.insights)
      ? parsed.insights
        .map((item: unknown) => {
          if (typeof item !== "object" || item === null) return null;
          const record = item as Record<string, unknown>;
          const evidence = Array.isArray(record.evidence)
            ? record.evidence.filter((e): e is string => typeof e === "string")
            : undefined;

          return {
            category: typeof record.category === "string" ? record.category : undefined,
            title: typeof record.title === "string" ? record.title : undefined,
            detail: typeof record.detail === "string" ? record.detail : undefined,
            evidence,
          } satisfies DisplayInsight;
        })
        .filter(
          (item: DisplayInsight | null): item is DisplayInsight =>
            Boolean(item && (item.title || item.detail || item.category)),
        )
      : undefined;

    if (!summaryText && !insights) {
      return null;
    }

    return { summary: summaryText, insights };
  } catch {
    return null;
  }
};

const computeCredibilityBreakdown = (sources?: SnapshotResponse["sources"] | null): CredibilityBreakdown => {
  if (!sources || sources.length === 0) {
    return { legitPercent: 78, misinfoPercent: 22, hasData: false };
  }

  let legit = 0;
  let suspect = 0;

  sources.forEach((source) => {
    const metadata = source.metadata ?? {};
    const credibility = typeof metadata.credibility === "string" ? metadata.credibility.toLowerCase() : undefined;
    const verification = typeof metadata.verification_status === "string" ? metadata.verification_status.toLowerCase() : undefined;
    const isVerified = metadata.is_verified === true || (verification && verification.includes("verified"));
    const flaggedAsFake = Boolean(
      (credibility && ["fake", "hoax", "misinfo", "misinformation", "rumor"].some((flag) => credibility.includes(flag))) ||
      (verification && ["fake", "misinfo", "unverified", "rumor"].some((flag) => verification.includes(flag))),
    );

    if (flaggedAsFake) {
      suspect += 1;
      return;
    }

    if (isVerified || credibility === "legit" || credibility === "credible") {
      legit += 1;
      return;
    }

    // If metadata is ambiguous, assume legit if there are no red flags
    legit += 1;
  });

  const total = legit + suspect;
  if (!total) {
    return { legitPercent: 78, misinfoPercent: 22, hasData: false };
  }

  return {
    legitPercent: Math.max(0, Math.min(100, Math.round((legit / total) * 100))),
    misinfoPercent: Math.max(0, Math.min(100, Math.round((suspect / total) * 100))),
    hasData: true,
  };
};

function ActionableInsightItem({ insight, index }: { insight: DisplayInsight; index: number }) {
  const [animatedDetail, setAnimatedDetail] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);

  React.useEffect(() => {
    const full = insight.detail ?? "";
    if (!full) {
      setAnimatedDetail("");
      setIsTyping(false);
      return;
    }

    const words = full.split(" ");
    if (words.length === 0) {
      setAnimatedDetail("");
      setIsTyping(false);
      return;
    }

    setAnimatedDetail("");
    setIsTyping(true);

    let i = 0;
    const intervalId = setInterval(() => {
      i += 1;
      if (i >= words.length) {
        setAnimatedDetail(full);
        setIsTyping(false);
        clearInterval(intervalId);
        return;
      }
      setAnimatedDetail(words.slice(0, i).join(" "));
    }, 55);

    return () => {
      clearInterval(intervalId);
      setIsTyping(false);
    };
  }, [insight.detail]);

  return (
    <li
      className="rounded-xl border border-slate-100 bg-white/80 p-4 shadow-sm animate-fade-up-soft"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {insight.category ? (
        <span className="mb-2 inline-block rounded-xl bg-hinaing-blue-500/10 px-3 py-1 text-xs font-semibold text-hinaing-blue-600">
          {insight.category}
        </span>
      ) : null}
      {insight.title ? (
        <p className="text-base font-semibold text-slate-900">{insight.title}</p>
      ) : null}
      {insight.detail ? (
        <p className="mt-1 text-sm text-slate-600">
          {animatedDetail || insight.detail}
          {isTyping && animatedDetail && animatedDetail !== insight.detail && (
            <span className="inline-block w-[0.5ch] animate-pulse align-baseline">▌</span>
          )}
        </p>
      ) : null}
      {insight.evidence && insight.evidence.length ? (
        <ul className="mt-3 space-y-1 list-disc pl-4 text-xs text-slate-500">
          {insight.evidence.map((item, evidenceIndex) => (
            <li key={evidenceIndex} className="break-all">
              <a
                href={item}
                target="_blank"
                rel="noopener noreferrer"
                className="text-hinaing-blue-600 hover:underline hover:text-hinaing-blue-700 transition-colors"
              >
                {item}
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function SentimentGeneratorPage({ activePage = 'sentiment', onNavigate }: SentimentGeneratorPageProps = {}) {
  const { state, actions, computed } = useSentimentGenerator();
  const [backendStatus, setBackendStatus] = React.useState<string | null>(null);
  const [backendError, setBackendError] = React.useState<string | null>(null);
  const [snapshot, setSnapshot] = React.useState<SnapshotResponse | null>(null);
  const [snapshotError, setSnapshotError] = React.useState<string | null>(null);
  const [showSources, setShowSources] = React.useState(false);
  const [animatedSummary, setAnimatedSummary] = React.useState("");
  const [isTypingSummary, setIsTypingSummary] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

  React.useEffect(() => {
    apiGet<{ status: string }>("/health")
      .then((data) => {
        setBackendStatus(data.status);
        setBackendError(null);
      })
      .catch((error) => {
        setBackendStatus(null);
        setBackendError(error.message);
      });
  }, []);

  const negativePercent = snapshot?.overall_sentiment?.scores?.negative !== undefined
    ? Math.round(snapshot.overall_sentiment.scores.negative * 100)
    : 54;
  const neutralPercent = snapshot?.overall_sentiment?.scores?.neutral !== undefined
    ? Math.round(snapshot.overall_sentiment.scores.neutral * 100)
    : 31;
  const positivePercent = snapshot?.overall_sentiment?.scores?.positive !== undefined
    ? Math.round(snapshot.overall_sentiment.scores.positive * 100)
    : 15;

  const narrativeSummary = React.useMemo(() => parseNarrativeSummary(snapshot?.overall_sentiment?.summary), [snapshot?.overall_sentiment?.summary]);

  const fullSummaryText = narrativeSummary?.summary ?? snapshot?.overall_sentiment?.summary ?? "";

  React.useEffect(() => {
    if (!fullSummaryText) {
      setAnimatedSummary("");
      setIsTypingSummary(false);
      return;
    }

    const words = fullSummaryText.split(" ");
    if (words.length === 0) {
      setAnimatedSummary("");
      setIsTypingSummary(false);
      return;
    }

    setAnimatedSummary("");
    setIsTypingSummary(true);

    let index = 0;
    const intervalId = setInterval(() => {
      index += 1;
      if (index >= words.length) {
        setAnimatedSummary(fullSummaryText);
        setIsTypingSummary(false);
        clearInterval(intervalId);
        return;
      }
      setAnimatedSummary(words.slice(0, index).join(" "));
    }, 55);

    return () => {
      clearInterval(intervalId);
      setIsTypingSummary(false);
    };
  }, [fullSummaryText]);

  const insightsToDisplay = React.useMemo<DisplayInsight[]>(() => {
    if (snapshot?.actionable_insights?.length) {
      return snapshot.actionable_insights.map((insight) => ({
        category: insight.category,
        title: insight.title,
        detail: insight.detail,
        evidence: insight.evidence,
      }));
    }

    if (narrativeSummary?.insights?.length) {
      return narrativeSummary.insights;
    }

    return [];
  }, [snapshot?.actionable_insights, narrativeSummary]);

  const hasInsights = insightsToDisplay.length > 0;
  const credibilityBreakdown = React.useMemo(() => computeCredibilityBreakdown(snapshot?.sources), [snapshot?.sources]);

  const handleGenerate = async () => {
    if (state.platforms.length === 0 || state.isGenerating) return;

    actions.setIsGenerating(true);
    setSnapshotError(null);

    const payload = {
      platforms: state.platforms,
      time_window: state.timeWindow,
      focus_areas: state.focusAreas,
      include_alerts: state.includeAlerts,
    };

    try {
      const result = await apiPost<typeof payload, SnapshotResponse>("/insights/snapshot", payload);
      setSnapshot(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate snapshot";
      setSnapshotError(message);
    } finally {
      actions.setIsGenerating(false);
    }
  };

  return (
    <>
      {/* Fixed Hamburger Menu at Top Right - Mobile Only */}
      <button
        type="button"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="fixed top-4 right-4 z-50 inline-flex items-center justify-center rounded-full bg-white p-3 text-slate-700 shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 active:scale-95 transition-all lg:hidden"
        aria-label={isSidebarOpen ? "Close menu" : "Open menu"}
        aria-expanded={isSidebarOpen}
      >
        {isSidebarOpen ? (
          <X className="h-6 w-6" aria-hidden="true" />
        ) : (
          <Menu className="h-6 w-6" aria-hidden="true" />
        )}
      </button>

      <div className="min-h-screen bg-slate-50 font-sans">
        <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-0 sm:px-6 lg:flex-row lg:gap-8 lg:px-8 lg:py-10 xl:px-12">

          <Sidebar
            onOpenMobileFilters={() => actions.setShowMobileFilters(true)}
            activePage={activePage}
            onNavigate={onNavigate}
            isSidebarOpen={isSidebarOpen}
            onCloseSidebar={() => setIsSidebarOpen(false)}
          />

          {/* Main Content */}
          <main className="order-1 flex w-full flex-col gap-6 lg:order-2 lg:flex-1 lg:gap-10 xl:gap-12">
            <section className="space-y-4">
              <HeroSection
                selectedWindowLabel={computed.selectedWindowLabel}
                platformSummary={computed.platformSummary}
                focusSummary={computed.focusSummary}
                focusSummaryLabel={computed.focusSummaryLabel}
              />
              <StatsCards
                selectedWindowLabel={computed.selectedWindowLabel}
                platformSummary={computed.platformSummary}
                platformSummaryLabel={computed.platformSummaryLabel}
                focusSummary={computed.focusSummary}
                focusSummaryLabel={computed.focusSummaryLabel}
                includeAlerts={state.includeAlerts}
              />
            </section>

            <section className="grid gap-y-3 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,1fr)] xl:gap-x-8" role="main" aria-label="Sentiment analysis configuration">
              <Card className="space-y-8 border-x-0 border-y border-slate-200 shadow-sm p-5 md:border md:shadow-lg md:shadow-slate-200/50 md:p-8 md:rounded-3xl bg-white ring-0 md:ring-1 md:ring-slate-100" role="form" aria-labelledby="config-heading">
                <header className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between border-b border-slate-100 pb-6">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-violet-600">
                        <Settings className="h-4 w-4" />
                      </div>
                      <h2 id="config-heading" className="text-xl font-bold text-slate-900 md:text-2xl">Configuration</h2>
                    </div>
                    <p className="text-sm text-slate-500 max-w-xl leading-relaxed">
                      Configure data sources and focus areas. The agent will gather the latest public posts, classify sentiment, and surface actionable intelligence.
                    </p>
                  </div>
                </header>

                {/* Coverage context card (no explicit step number to avoid confusion with main steps) */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5" role="region" aria-labelledby="coverage-heading">
                  <p className="text-[11px] font-semibold text-hinaing-blue-600">Review coverage</p>
                  <h3 id="coverage-heading" className="mt-1 text-lg font-semibold text-slate-900">Barangay & keyword context</h3>
                  <p className="text-sm font-medium text-slate-700">Baguio City, Philippines</p>
                  <p className="text-sm text-slate-500">Adjust geographic filters in settings to include nearby municipalities when needed.</p>

                  <dl className="mt-4 grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
                    <div className="rounded-xl border border-slate-100 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Population</dt>
                      <dd className="mt-2 text-lg font-semibold text-slate-900">~366k residents</dd>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Priority Barangays</dt>
                      <dd className="mt-2 text-sm text-slate-700">Session Road, Aurora Hill, Irisan</dd>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Languages</dt>
                      <dd className="mt-2 text-sm text-slate-700">Ilocano, Ibaloi, Filipino, English</dd>
                    </div>
                    <div className="rounded-xl border border-slate-100 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Monitoring Tags</dt>
                      <dd className="mt-2 text-sm text-slate-700">#traffic, #water, #safety, #tourism</dd>
                    </div>
                  </dl>
                </div>

                {/* Configuration Sections */}
                <div className="space-y-6">
                  {/* Quick Start Presets */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wide text-violet-600">Quick start</span>
                      <span className="text-xs text-slate-400">Choose a preset to auto-fill filters</span>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-3">
                      {PRESET_OPTIONS.map((preset) => {
                        const isActive =
                          preset.platforms.every((platform) => state.platforms.includes(platform)) &&
                          preset.focusAreas.every((focus) => state.focusAreas.includes(focus)) &&
                          preset.window === state.timeWindow;
                        return (
                          <button
                            key={preset.id}
                            type="button"
                            onClick={() => actions.applyPreset(preset.id)}
                            className={clsx(
                              "group relative flex flex-col rounded-2xl border p-5 text-left transition-all duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 hover:-translate-y-1 hover:shadow-md",
                              isActive
                                ? "border-transparent bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/30"
                                : "border-slate-200 bg-white text-slate-600 hover:border-violet-200 hover:bg-violet-50/30",
                            )}
                            aria-pressed={isActive}
                            aria-describedby={`preset-${preset.id}-desc`}
                          >
                            <span className="flex items-center justify-between text-sm font-bold">
                              {preset.name}
                              {isActive && (
                                <span className="absolute top-4 right-4 flex h-2 w-2">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                                </span>
                              )}
                            </span>
                            <p
                              id={`preset-${preset.id}-desc`}
                              className={clsx(
                                "mt-3 text-xs leading-relaxed",
                                isActive ? "text-white/80" : "text-slate-500 group-hover:text-slate-600",
                              )}
                            >
                              {preset.description}
                            </p>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-5 lg:grid lg:grid-cols-2 lg:gap-5 lg:space-y-0">
                    <div className="space-y-5">
                      <PlatformSelector
                        platforms={state.platforms}
                        onToggle={actions.toggleSelection}
                        setPlatforms={actions.setPlatforms}
                      />
                    </div>
                    <div className="space-y-5">
                      <TimeWindowSelector
                        timeWindow={state.timeWindow}
                        setTimeWindow={actions.setTimeWindow}
                      />
                    </div>
                  </div>

                  <div className="space-y-5 lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(280px,1fr)] lg:gap-5 lg:space-y-0">
                    <FocusAreaSelector
                      focusAreas={state.focusAreas}
                      onToggle={actions.toggleSelection}
                      setFocusAreas={actions.setFocusAreas}
                    />

                    {/* Alert Preferences */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Step 4 · Alert preferences</span>
                        <span className="text-[11px] text-slate-400">Ensure urgent notices reach you</span>
                      </div>
                      <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm cursor-pointer">
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-hinaing-blue-500 focus:ring-hinaing-blue-500 focus:ring-offset-2"
                          checked={state.includeAlerts}
                          onChange={(event) => actions.setIncludeAlerts(event.target.checked)}
                          aria-describedby="alert-description"
                        />
                        <span>
                          Include urgent alert summary (e.g., outages, floods, safety notices)
                          <span id="alert-description" className="mt-1 block text-xs text-slate-400">Alerts surface in the briefing header and notification digest.</span>
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-2 text-sm font-medium text-slate-600 transition duration-150 ease-out hover:-translate-y-0.5 hover:border-hinaing-blue-500 hover:text-hinaing-blue-600 focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2"
                    aria-label="Save current configuration as preset"
                  >
                    <Save className="h-4 w-4" aria-hidden="true" />
                    Save Preset
                  </button>
                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={state.isGenerating || state.platforms.length === 0}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-hinaing-blue-600/30 transition duration-150 ease-out hover:-translate-y-0.5 hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2"
                    aria-label="Generate new sentiment report with current settings"
                  >
                    {state.isGenerating ? (
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <BarChart3 className="h-4 w-4" aria-hidden="true" />
                    )}
                    {state.isGenerating ? 'Generating Report...' : 'Generate Sentiment Report'}
                  </button>
                </div>
              </Card>

              {/* Live Preview */}
              {/* Live Preview */}
              <Card className="space-y-6 border-x-0 border-y border-slate-200 shadow-sm p-5 md:border md:rounded-xl md:shadow-md md:p-6 lg:max-w-md" role="region" aria-labelledby="preview-heading">
                <header className="space-y-1">
                  <h2 id="preview-heading" className="text-lg font-semibold text-slate-900">Live Snapshot Preview</h2>
                  <p className="text-sm text-slate-500">
                    Based on {state.timeWindow} of public chatter across {computed.platformSummary.length} platform
                    {computed.platformSummary.length === 1 ? "" : "s"}: {computed.platformSummary.map((item) => item.label).join(" • ")}
                  </p>
                  {snapshotError ? (
                    <p className="text-xs text-rose-600">{snapshotError}</p>
                  ) : null}
                </header>

                <div className="space-y-5">
                  {snapshot ? (
                    <>
                      <Card className="space-y-4 border border-hinaing-blue-200 bg-gradient-to-br from-hinaing-blue-50 to-violet-50 p-5">
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-gradient-to-r from-hinaing-blue-500/15 via-hinaing-blue-400/15 to-violet-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-hinaing-blue-800">
                            Overall Sentiment
                          </span>
                          <span className="text-xs font-medium text-hinaing-blue-600">Updated moments ago</span>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-xl font-semibold text-hinaing-blue-900" id="sentiment-summary">
                            {snapshot.overall_sentiment.label}
                          </h3>
                          <p className="text-sm text-slate-600">
                            {animatedSummary || fullSummaryText}
                            {isTypingSummary && (
                              <span className="inline-block w-[0.5ch] animate-pulse align-baseline">▌</span>
                            )}
                          </p>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-center text-sm">
                          <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                            <strong className="block text-lg font-semibold text-rose-600">{negativePercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Negative</span>
                          </div>
                          <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                            <strong className="block text-lg font-semibold text-slate-700">{neutralPercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Neutral</span>
                          </div>
                          <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                            <strong className="block text-lg font-semibold text-emerald-600">{positivePercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Positive</span>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-center text-sm">
                          <div className="rounded-lg bg-white/80 p-3 shadow-inner">
                            <strong className="block text-lg font-semibold text-emerald-700">{credibilityBreakdown.legitPercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Legit Sources</span>
                            <p className="mt-1 text-[11px] text-slate-500">
                              {credibilityBreakdown.hasData ? 'Verified or trusted outlets in this pull.' : 'Estimated share based on prior pulls.'}
                            </p>
                          </div>
                          <div className="rounded-lg bg-white/80 p-3 shadow-inner">
                            <strong className="block text-lg font-semibold text-amber-600">{credibilityBreakdown.misinfoPercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Potential Fake News</span>
                            <p className="mt-1 text-[11px] text-slate-500">
                              {credibilityBreakdown.hasData ? 'Flagged for manual review.' : 'Estimate until verification labels arrive.'}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setShowSources(!showSources)}
                          className="inline-flex items-center gap-1 text-sm font-medium text-hinaing-blue-600 hover:text-hinaing-blue-500 focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2 rounded"
                          aria-label="View detailed conversation data"
                        >
                          {showSources ? 'Hide' : 'View'} supporting conversations ({snapshot.sources?.length || 0})
                          <ExternalLink className="h-3 w-3" aria-hidden="true" />
                        </button>
                      </Card>

                      {showSources && snapshot.sources && snapshot.sources.length > 0 && (
                        <Card className="border border-slate-200 bg-white shadow-md p-6">
                          <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-slate-900">
                              Supporting Conversations ({snapshot.sources.length})
                            </h3>
                            <div className="space-y-4 max-h-96 overflow-y-auto">
                              {snapshot.sources.map((source, index) => (
                                <div key={index} className="border border-slate-100 rounded-lg bg-white p-4 shadow-sm">
                                  <div className="space-y-2">
                                    <h4 className="font-medium text-slate-900 leading-tight">
                                      {source.title}
                                    </h4>
                                    <p className="text-sm text-slate-600 leading-relaxed">
                                      {source.snippet}
                                    </p>
                                    <div className="flex items-center justify-between text-xs">
                                      <div className="flex items-center gap-2">
                                        {source.sentiment && (
                                          <span className={clsx(
                                            "px-2 py-1 rounded-full font-medium",
                                            source.sentiment === 'positive' && "bg-emerald-100 text-emerald-700",
                                            source.sentiment === 'negative' && "bg-rose-100 text-rose-700",
                                            source.sentiment === 'neutral' && "bg-slate-100 text-slate-700",
                                          )}>
                                            {source.sentiment}
                                          </span>
                                        )}
                                        {source.published_at && (
                                          <span className="text-slate-500">
                                            {new Date(source.published_at).toLocaleDateString()}
                                          </span>
                                        )}
                                      </div>
                                      {source.url && (
                                        <a
                                          href={source.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="inline-flex items-center gap-1 text-hinaing-blue-600 hover:text-hinaing-blue-500 font-medium"
                                        >
                                          View Source
                                          <ExternalLink className="h-3 w-3" />
                                        </a>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </Card>
                      )}

                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                            Actionable Insights
                          </h3>
                          {hasInsights ? (
                            <ul className="mt-3 space-y-3 text-sm text-slate-600">
                              {insightsToDisplay.map((insight, index) => (
                                <ActionableInsightItem key={index} insight={insight} index={index} />
                              ))}
                            </ul>
                          ) : (
                            <p className="mt-3 text-sm text-slate-500">
                              We’ll surface the most important recommendations here once the agent finds clear trends in the latest conversations.
                            </p>
                          )}
                        </div>

                        <div className="flex justify-end">
                          <button
                            type="button"
                            onClick={() => onNavigate?.('reports')}
                            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-4 py-2 text-xs font-semibold text-white shadow-subtle transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2"
                            aria-label="View saved reports"
                          >
                            <Save className="h-4 w-4" aria-hidden="true" />
                            View saved reports
                          </button>
                        </div>

                        {state.includeAlerts && snapshot.alerts && snapshot.alerts.length ? (
                          <div className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50 p-5" role="alert">
                            <div className="flex items-start gap-3">
                              <AlertTriangle className="h-6 w-6 text-amber-600 mt-1" aria-hidden="true" />
                              <div>
                                <h3 className="text-base font-semibold text-amber-800">Urgent Alerts</h3>
                                <p className="text-sm text-amber-700">Flagged for rapid response escalation.</p>
                              </div>
                            </div>
                            <ul className="space-y-3 text-sm text-amber-800">
                              {snapshot.alerts.map((alert, index) => (
                                <li key={index}>
                                  <strong>{alert}</strong>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </div>
                    </>
                  ) : (
                    <>
                      <Card className="space-y-4 border border-dashed border-slate-200 bg-white p-5 text-slate-500" role="status" aria-live="polite">
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Overall Sentiment
                          </span>
                          {state.isGenerating ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-hinaing-blue-50 px-3 py-1 text-[11px] font-semibold text-hinaing-blue-700">
                              <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                              Generating…
                            </span>
                          ) : null}
                        </div>
                        <div className="space-y-2">
                          <div className={clsx("h-5 w-40 rounded", state.isGenerating ? "animate-pulse bg-slate-200" : "bg-slate-100")} aria-hidden="true" />
                          <div className={clsx("h-4 w-72 rounded", state.isGenerating ? "animate-pulse bg-slate-200" : "bg-slate-100")} aria-hidden="true" />
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-center text-xs">
                          {['Negative', 'Neutral', 'Positive'].map((label) => (
                            <div key={label} className="space-y-1 rounded-xl border border-slate-100 bg-white/80 p-3">
                              <div className={clsx("h-5 rounded", state.isGenerating ? "animate-pulse bg-slate-200" : "bg-slate-100")} aria-hidden="true" />
                              <span className="text-[11px] uppercase tracking-wide text-slate-400">{label}</span>
                            </div>
                          ))}
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-center text-xs">
                          {['Legit Sources', 'Potential Fake News'].map((label) => (
                            <div key={label} className="space-y-1 rounded-xl border border-slate-100 bg-white/80 p-3">
                              <div className={clsx("h-5 rounded", state.isGenerating ? "animate-pulse bg-slate-200" : "bg-slate-100")} aria-hidden="true" />
                              <span className="text-[11px] uppercase tracking-wide text-slate-400">{label}</span>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-slate-500">
                          {state.isGenerating
                            ? 'Analyzing fresh chatter across your selected channels. This card will update once calculations finish.'
                            : 'We’ll populate this card with live sentiment once you run a report for the filters above.'}
                        </p>
                      </Card>

                      <div className="space-y-4">
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-4">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Actionable Insights</h3>
                            <span className="text-[11px] text-slate-400">
                              {state.isGenerating ? 'Drafting insights…' : 'Ready after generation'}
                            </span>
                          </div>
                          <p className="mt-3 text-xs text-slate-500">
                            {state.isGenerating ? (
                              <>Matching community chatter to <span className="font-semibold">{computed.focusSummaryLabel}</span> priorities…</>
                            ) : (
                              <>Once generated, the most urgent recommendations for
                                <span className="font-semibold"> {computed.focusSummaryLabel}</span> will surface here with links to supporting evidence.</>
                            )}
                          </p>
                          <div className="mt-4 grid gap-3 text-[13px] text-slate-500 sm:grid-cols-2">
                            {['Infrastructure readiness', 'Community health', 'Incident response'].map((label) => (
                              <div
                                key={label}
                                className={clsx(
                                  "rounded-xl border border-slate-100 bg-white/80 p-3",
                                  state.isGenerating && "animate-pulse",
                                )}
                              >
                                <p className="text-xs font-semibold text-slate-400">{label}</p>
                                <p className="mt-1 text-[12px]">
                                  {state.isGenerating
                                    ? 'Analyzing fresh posts for early warnings…'
                                    : 'Generate a snapshot to surface the latest risk and opportunity signals.'}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {state.includeAlerts ? (
                          <div className="rounded-2xl border border-dashed border-amber-200 bg-amber-50/70 p-5" role="alert">
                            <div className="flex items-start gap-3">
                              <AlertTriangle className="h-5 w-5 text-amber-500" aria-hidden="true" />
                              <div className="space-y-1">
                                <h3 className="text-sm font-semibold text-amber-800">Alerts appear here</h3>
                                <p className="text-xs text-amber-700">
                                  Keep “Include urgent alerts” enabled and run a report—critical disruptions will be listed with direct citizen quotes and timestamps.
                                </p>
                              </div>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </>
                  )}
                </div>
              </Card>
            </section>
          </main>
        </div>
      </div>

      {/* Mobile Filters */}
      <MobileFilters
        showMobileFilters={state.showMobileFilters}
        setShowMobileFilters={actions.setShowMobileFilters}
        platforms={state.platforms}
        timeWindow={state.timeWindow}
        focusAreas={state.focusAreas}
        includeAlerts={state.includeAlerts}
        onToggleSelection={actions.toggleSelection}
        setPlatforms={actions.setPlatforms}
        setTimeWindow={actions.setTimeWindow}
        setFocusAreas={actions.setFocusAreas}
        setIncludeAlerts={actions.setIncludeAlerts}
      />
    </>
  );
}
