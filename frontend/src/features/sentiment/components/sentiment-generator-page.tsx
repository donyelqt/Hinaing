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
  Settings
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

export function SentimentGeneratorPage({ activePage = 'sentiment', onNavigate }: SentimentGeneratorPageProps = {}) {
  const { state, actions, computed } = useSentimentGenerator();
  const [backendStatus, setBackendStatus] = React.useState<string | null>(null);
  const [backendError, setBackendError] = React.useState<string | null>(null);
  const [snapshot, setSnapshot] = React.useState<SnapshotResponse | null>(null);
  const [snapshotError, setSnapshotError] = React.useState<string | null>(null);
  const [showSources, setShowSources] = React.useState(false);

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
      <div className="min-h-screen bg-slate-100">
        <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 py-8 sm:px-6 lg:flex-row lg:gap-8 lg:px-10 lg:py-12 xl:px-16">
          
          <Sidebar 
            onOpenMobileFilters={() => actions.setShowMobileFilters(true)} 
            activePage={activePage}
            onNavigate={onNavigate}
          />

          {/* Main Content */}
          <main className="order-1 flex w-full flex-col gap-6 lg:order-2 lg:gap-10 xl:gap-12">
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

            <section className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,1fr)] xl:gap-8" role="main" aria-label="Sentiment analysis configuration">
              <Card className="space-y-6 p-5 md:p-6 lg:p-8" role="form" aria-labelledby="config-heading">
                <header className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <h2 id="config-heading" className="text-xl font-semibold text-slate-900 md:text-2xl">Generate Public Sentiment Snapshot</h2>
                    <p className="text-sm text-slate-500">
                      Configure data sources and focus areas. The agent will gather the latest public posts, classify sentiment, and surface actionable intelligence for decision-makers.
                    </p>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="rounded-full bg-slate-200 px-2 py-1 font-medium text-slate-600">Backend</span>
                      {backendStatus ? (
                        <span className="rounded-full bg-emerald-100 px-2 py-1 font-medium text-emerald-700">{backendStatus}</span>
                      ) : backendError ? (
                        <span className="rounded-full bg-rose-100 px-2 py-1 font-medium text-rose-700">{backendError}</span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-500">Checking…</span>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      actions.setIsRefreshing(true);
                      setTimeout(() => actions.setIsRefreshing(false), 2000);
                    }}
                    disabled={state.isRefreshing}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-hinaing-blue-500 hover:text-hinaing-blue-600 disabled:opacity-50"
                    aria-label="Refresh current data"
                  >
                    {state.isRefreshing ? (
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    ) : (
                      <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    )}
                    {state.isRefreshing ? 'Refreshing...' : 'Quick Refresh'}
                  </button>
                </header>

                {/* Step 1 Coverage Card */}
                <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-slate-50 to-slate-100 p-5" role="region" aria-labelledby="coverage-heading">
                  <p className="text-xs font-semibold uppercase tracking-wide text-hinaing-blue-600">Step 1 · Review coverage</p>
                  <h3 id="coverage-heading" className="mt-1 text-lg font-semibold text-slate-900">Barangay & keyword context</h3>
                  <p className="text-sm font-medium text-slate-700">Baguio City, Philippines</p>
                  <p className="text-sm text-slate-500">Adjust geographic filters in settings to include nearby municipalities when needed.</p>

                  <dl className="mt-4 grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
                    <div className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Population</dt>
                      <dd className="mt-2 text-lg font-semibold text-slate-900">~366k residents</dd>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Priority Barangays</dt>
                      <dd className="mt-2 text-sm text-slate-700">Session Road, Aurora Hill, Irisan</dd>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Languages</dt>
                      <dd className="mt-2 text-sm text-slate-700">Ilocano, Ibaloi, Filipino, English</dd>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Monitoring Tags</dt>
                      <dd className="mt-2 text-sm text-slate-700">#traffic, #water, #safety, #tourism</dd>
                    </div>
                  </dl>
                </div>

                {/* Configuration Sections */}
                <div className="space-y-6">
                  {/* Quick Start Presets */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wide text-hinaing-blue-600">Quick start</span>
                      <span className="text-xs text-slate-400">Choose a preset to auto-fill filters</span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
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
                              "group flex flex-col rounded-2xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2",
                              isActive
                                ? "border-hinaing-blue-500 bg-hinaing-blue-500/10 text-hinaing-blue-700"
                                : "border-slate-200 bg-white text-slate-600 hover:border-hinaing-blue-300",
                            )}
                            aria-pressed={isActive}
                            aria-describedby={`preset-${preset.id}-desc`}
                          >
                            <span className="flex items-center justify-between text-sm font-semibold">
                              {preset.name}
                              <span
                                className={clsx(
                                  "rounded-full border px-2 py-0.5 text-xs",
                                  isActive ? "border-hinaing-blue-500 text-hinaing-blue-600" : "border-slate-200 text-slate-400",
                                )}
                              >
                                Apply
                              </span>
                            </span>
                            <p id={`preset-${preset.id}-desc`} className="mt-2 text-xs text-slate-500 group-hover:text-slate-400">{preset.description}</p>
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
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-2 text-sm font-medium text-slate-600 transition hover:border-hinaing-blue-500 hover:text-hinaing-blue-600 focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2"
                    aria-label="Save current configuration as preset"
                  >
                    <Save className="h-4 w-4" aria-hidden="true" />
                    Save Preset
                  </button>
                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={state.isGenerating || state.platforms.length === 0}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-hinaing-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-hinaing-blue-600/30 transition hover:bg-hinaing-blue-500 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2"
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
              <Card className="order-first space-y-6 p-5 md:order-none md:p-6 lg:max-w-md" role="region" aria-labelledby="preview-heading">
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
                      <Card className="space-y-4 border border-hinaing-blue-200 bg-gradient-to-br from-hinaing-blue-50 to-white p-5">
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-hinaing-blue-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-hinaing-blue-700">
                            Overall Sentiment
                          </span>
                          <span className="text-xs font-medium text-hinaing-blue-600">Updated moments ago</span>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-xl font-semibold text-hinaing-blue-900" id="sentiment-summary">
                            {snapshot.overall_sentiment.label}
                          </h3>
                          <p className="text-sm text-slate-600">
                            {snapshot.overall_sentiment.summary}
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
                        <Card className="border-hinaing-blue-200 bg-gradient-to-br from-slate-50 to-white p-6">
                          <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-slate-900">
                              Supporting Conversations ({snapshot.sources.length})
                            </h3>
                            <div className="space-y-4 max-h-96 overflow-y-auto">
                              {snapshot.sources.map((source, index) => (
                                <div key={index} className="border border-slate-200 rounded-lg bg-white p-4 shadow-sm">
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
                          <ul className="mt-3 space-y-3 text-sm text-slate-600">
                            {snapshot.actionable_insights.map((insight, index) => (
                              <li key={index} className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                                <span className="mb-1 inline-block rounded-xl bg-hinaing-blue-500/10 px-3 py-1 text-xs font-semibold text-hinaing-blue-600">
                                  {insight.category}
                                </span>
                                <strong>{insight.title}</strong> {insight.detail}
                              </li>
                            ))}
                          </ul>
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
                      <Card className="space-y-4 border border-dashed border-slate-200 bg-white/70 p-5 text-slate-500">
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Overall Sentiment
                          </span>
                          <button
                            type="button"
                            onClick={handleGenerate}
                            className="text-xs font-medium text-hinaing-blue-600 hover:text-hinaing-blue-500"
                          >
                            Generate snapshot ↗
                          </button>
                        </div>
                        <div className="space-y-2">
                          <div className="h-5 w-40 rounded bg-slate-100" aria-hidden="true" />
                          <div className="h-4 w-72 rounded bg-slate-100" aria-hidden="true" />
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-center text-xs">
                          {['Negative','Neutral','Positive'].map((label) => (
                            <div key={label} className="space-y-1 rounded-xl border border-slate-100 bg-white/80 p-3">
                              <div className="h-5 rounded bg-slate-100" aria-hidden="true" />
                              <span className="text-[11px] uppercase tracking-wide text-slate-400">{label}</span>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-slate-500">
                          We’ll populate this card with live sentiment once you run a report for the filters above.
                        </p>
                      </Card>

                      <div className="space-y-4">
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-4">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Actionable Insights</h3>
                            <span className="text-[11px] text-slate-400">Ready after generation</span>
                          </div>
                          <p className="mt-3 text-xs text-slate-500">
                            Once generated, the most urgent recommendations for
                            <span className="font-semibold"> {computed.focusSummaryLabel}</span> will surface here with links to supporting evidence.
                          </p>
                          <div className="mt-4 grid gap-3 text-[13px] text-slate-500 sm:grid-cols-2">
                            {['Infrastructure readiness','Community health','Incident response'].map((label) => (
                              <div key={label} className="rounded-xl border border-slate-100 bg-white/80 p-3">
                                <p className="text-xs font-semibold text-slate-400">{label}</p>
                                <p className="mt-1 text-[12px]">Generate a snapshot to surface the latest risk and opportunity signals.</p>
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
