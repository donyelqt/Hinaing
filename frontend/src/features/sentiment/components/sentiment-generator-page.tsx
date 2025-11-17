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

export function SentimentGeneratorPage({ activePage = 'sentiment', onNavigate }: SentimentGeneratorPageProps = {}) {
  const { state, actions, computed } = useSentimentGenerator();

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

                {/* Workflow Overview */}
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4" role="region" aria-labelledby="workflow-heading">
                  <h3 id="workflow-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-400">Workflow overview</h3>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    {GENERATOR_STEPS.map((step, index) => (
                      <div key={step.title} className="flex items-start gap-3">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-hinaing-blue-500/10 text-sm font-semibold text-hinaing-blue-600" aria-hidden="true">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-slate-700">{step.title}</p>
                          <p className="text-xs text-slate-500">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
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

                  <div className="grid gap-5 md:grid-cols-2">
                    {/* Geographic Coverage */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Step 1 · Review coverage</span>
                        <span className="text-[11px] text-slate-400">Barangay & keyword context</span>
                      </div>
                      <Card className="space-y-4 p-4">
                        <div className="flex items-start gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-hinaing-blue-500/10" aria-hidden="true">
                            <MapPin className="h-5 w-5 text-hinaing-blue-600" />
                          </div>
                          <div className="space-y-1">
                            <h3 className="text-lg font-semibold text-slate-900">Baguio City, Philippines</h3>
                            <p className="text-sm text-slate-500">
                              Adjust geographic filters in settings to include nearby municipalities when needed.
                            </p>
                          </div>
                        </div>
                        <dl className="grid gap-3 text-sm text-slate-500 lg:grid-cols-2">
                          <div>
                            <dt className="font-medium text-slate-600">Population</dt>
                            <dd>~366k residents</dd>
                          </div>
                          <div>
                            <dt className="font-medium text-slate-600">Priority Barangays</dt>
                            <dd>Session Road, Aurora Hill, Irisan</dd>
                          </div>
                          <div>
                            <dt className="font-medium text-slate-600">Languages</dt>
                            <dd>Ilocano, Ibaloi, Filipino, English</dd>
                          </div>
                          <div>
                            <dt className="font-medium text-slate-600">Monitoring Tags</dt>
                            <dd>#traffic, #water, #safety, #tourism</dd>
                          </div>
                        </dl>
                      </Card>
                    </div>

                    {/* Platform & Time Selectors */}
                    <div className="space-y-5">
                      <PlatformSelector
                        platforms={state.platforms}
                        onToggle={actions.toggleSelection}
                        setPlatforms={actions.setPlatforms}
                      />
                      <TimeWindowSelector
                        timeWindow={state.timeWindow}
                        setTimeWindow={actions.setTimeWindow}
                      />
                    </div>
                  </div>

                  <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,320px)]">
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
                    onClick={() => {
                      actions.setIsGenerating(true);
                      setTimeout(() => actions.setIsGenerating(false), 5000);
                    }}
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
                </header>

                <div className="space-y-5">
                  <Card className="space-y-4 border border-hinaing-blue-200 bg-gradient-to-br from-hinaing-blue-50 to-white p-5">
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-hinaing-blue-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-hinaing-blue-700">
                        Overall Sentiment
                      </span>
                      <span className="text-xs font-medium text-hinaing-blue-600">Updated moments ago</span>
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-xl font-semibold text-hinaing-blue-900" id="sentiment-summary">Moderately Concerned</h3>
                      <p className="text-sm text-slate-600">
                        Transportation and water service interruptions remain top-of-mind. Residents
                        request quicker coordination with barangay officials and clearer advisories.
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-center text-sm">
                      <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                        <strong className="block text-lg font-semibold text-rose-600">54%</strong>
                        <span className="text-2xs uppercase tracking-wide text-slate-500">Negative</span>
                      </div>
                      <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                        <strong className="block text-lg font-semibold text-slate-700">31%</strong>
                        <span className="text-2xs uppercase tracking-wide text-slate-500">Neutral</span>
                      </div>
                      <div className="rounded-lg bg-white/70 p-3 shadow-inner">
                        <strong className="block text-lg font-semibold text-emerald-600">15%</strong>
                        <span className="text-2xs uppercase tracking-wide text-slate-500">Positive</span>
                      </div>
                    </div>
                    <button type="button" className="inline-flex items-center gap-1 text-sm font-medium text-hinaing-blue-600 hover:text-hinaing-blue-500 focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500 focus:ring-offset-2 rounded" aria-label="View detailed conversation data">
                      View supporting conversations
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </button>
                  </Card>

                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                        Actionable Insights
                      </h3>
                      <ul className="mt-3 space-y-3 text-sm text-slate-600">
                        <li className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                          <span className="mb-1 inline-block rounded-xl bg-hinaing-blue-500/10 px-3 py-1 text-xs font-semibold text-hinaing-blue-600">
                            Infrastructure
                          </span>
                          <strong>Deploy traffic marshals</strong> on Session Road and issue clearer digital signage for rerouting. 120+ negative posts indicate urgent need for improved traffic management.
                        </li>
                        <li className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                          <span className="mb-1 inline-block rounded-xl bg-hinaing-blue-500/10 px-3 py-1 text-xs font-semibold text-hinaing-blue-600">
                            Health
                          </span>
                          <strong>Coordinate emergency supply delivery</strong> to Irisan barangay health center within 48 hours. Public posts show growing concern over vaccine availability affecting community trust.
                        </li>
                        <li className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
                          <span className="mb-1 inline-block rounded-xl bg-hinaing-blue-500/10 px-3 py-1 text-xs font-semibold text-hinaing-blue-600">
                            Environment
                          </span>
                          <strong>Scale successful waste segregation program</strong> city-wide based on positive Burnham Park feedback. Leverage high community satisfaction to expand to other barangays.
                        </li>
                      </ul>
                    </div>

                    {state.includeAlerts ? (
                      <div className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50 p-5" role="alert">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="h-6 w-6 text-amber-600 mt-1" aria-hidden="true" />
                          <div>
                            <h3 className="text-base font-semibold text-amber-800">Urgent Alerts</h3>
                            <p className="text-sm text-amber-700">Flagged for rapid response escalation.</p>
                          </div>
                        </div>
                        <ul className="space-y-3 text-sm text-amber-800">
                          <li>
                            <strong>Water outage</strong> — La Trinidad border communities report 8-hour interruption and request tanker deployment.
                          </li>
                          <li>
                            <strong>Landslide risk</strong> — Heavy rains near Kennon Road triggered elevated concern; residents sharing erosion photos.
                          </li>
                        </ul>
                      </div>
                    ) : null}
                  </div>
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
