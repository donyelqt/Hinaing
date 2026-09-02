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
import { KeyboardButton } from "@/components/ui/keyboard-button";

import { Card } from "@/components/ui/card";
import { apiGet, apiPost } from "@/lib/api";
import { Sidebar } from "../../shared/components";
import type { ActivePage } from "../../shared/types/navigation";
import { useAgenticOrchestrator } from "../hooks/useAgenticOrchestrator";
import { HeroSection } from "./HeroSection";
import { PlatformSelector } from "./PlatformSelector";
import { TimeWindowSelector } from "./TimeWindowSelector";
import { FocusAreaSelector } from "./FocusAreaSelector";
import { MobileFilters } from "./MobileFilters";
import { VerificationBadge } from "./VerificationBadge";
import { parseCitations } from "../utils/citation-parser";
import { PRESET_OPTIONS, GENERATOR_STEPS } from "../constants";

type SentimentGeneratorPageProps = {
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
};

type AnalysisMode = 'full' | 'sentiment' | 'credibility';

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
  verification?: {
    total_claims: number;
    verified_claims: number;
    unverified_claims: number;
    faithfulness_score: number;
    claim_details: Array<{
      claim: string;
      category: string;
      entailment_score: number;
      status: string;
      supporting_sources: string[];
    }>;
    // NEW: Best practice metrics for Row 2 display
    hallucination_analysis?: {
      is_hallucination_free: boolean;
      hallucination_count: number;
      hallucination_types: Record<string, number>;
    };
    misattribution_analysis?: {
      misattribution_count: number;
      misattribution_rate: number;
    };
    numerical_hallucinations?: {
      count: number;
      rate: number;
      details?: Array<{
        claim: string;
        unsupported_numbers: string[];
      }>;
    };
    citation_verification?: {
      total_citations: number;
      valid_citations: number;
      citation_accuracy_rate: number;
    };
  } | null;
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
  highCredibility: number;    // High + Medium tier
  lowCredibility: number;     // Low + Very Low tier
  avgScore: number;           // Average credibility score
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
    return { highCredibility: 0, lowCredibility: 0, avgScore: 0, hasData: false };
  }

  let highCount = 0;  // High + Medium credibility
  let lowCount = 0;   // Low + Very Low credibility
  let totalScore = 0;
  let scoredCount = 0;

  sources.forEach((source) => {
    const metadata = source.metadata ?? {};
    const score = typeof metadata.credibility_score === "number" ? metadata.credibility_score : null;
    const tier = typeof metadata.credibility_tier === "string" ? metadata.credibility_tier.toLowerCase() : null;

    if (score !== null) {
      totalScore += score;
      scoredCount += 1;

      // High/Medium (≥0.55) vs Low/Very Low (<0.55) - matches 6-signal thresholds
      if (score >= 0.55 || tier === "high" || tier === "medium") {
        highCount += 1;
      } else {
        lowCount += 1;
      }
    } else if (tier) {
      // Fallback to tier only
      if (tier === "high" || tier === "medium") {
        highCount += 1;
      } else {
        lowCount += 1;
      }
    }
  });

  const total = highCount + lowCount;
  if (!total) {
    return { highCredibility: 0, lowCredibility: 0, avgScore: 0, hasData: false };
  }

  return {
    highCredibility: Math.round((highCount / total) * 100),
    lowCredibility: Math.round((lowCount / total) * 100),
    avgScore: scoredCount > 0 ? Math.round((totalScore / scoredCount) * 100) : 0,
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
  const { state, actions, computed, validation } = useAgenticOrchestrator();
  const [backendStatus, setBackendStatus] = React.useState<string | null>(null);
  const [backendError, setBackendError] = React.useState<string | null>(null);
  const [snapshot, setSnapshot] = React.useState<SnapshotResponse | null>(null);
  const [snapshotError, setSnapshotError] = React.useState<string | null>(null);
  const [showSources, setShowSources] = React.useState(false);
  const [animatedSummary, setAnimatedSummary] = React.useState("");
  const [isTypingSummary, setIsTypingSummary] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
  const [hoveredCardIndex, setHoveredCardIndex] = React.useState<number | null>(null);
  const [mode, setMode] = React.useState<AnalysisMode>('full');

  // Removed auto-hover effect as requested
  // React.useEffect(() => {
  //   if (!snapshot) return; // Only run when snapshot data is available
  //
  //   const cards = [0, 1, 2, 3, 4, 5]; // Indices for the 6 cards (sentiment + 3 stats + 3 credibility)
  //   let currentIndex = 0;
  //
  //   const interval = setInterval(() => {
  //     setHoveredCardIndex(cards[currentIndex]);
  //     currentIndex = (currentIndex + 1) % cards.length;
  //   }, 3000);
  //
  //   return () => clearInterval(interval);
  // }, [snapshot]);

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

  // Calculate sentiment percentages with rounding that ensures sum to 100%
  let negativePercent = 54;
  let neutralPercent = 31;
  let positivePercent = 15;
  
  if (snapshot?.overall_sentiment?.scores) {
    const { negative, neutral, positive } = snapshot.overall_sentiment.scores;
    const neg = Math.round(negative * 100);
    const neu = Math.round(neutral * 100);
    const pos = Math.round(positive * 100);
    const total = neg + neu + pos;
    
    if (total !== 100) {
      // Adjust the largest percentage to make sum 100%
      const diff = 100 - total;
      const values = [
        { value: neg, key: 'negative' },
        { value: neu, key: 'neutral' },
        { value: pos, key: 'positive' }
      ];
      const largest = values.reduce((a, b) => a.value > b.value ? a : b);
      
      if (largest.key === 'negative') negativePercent = neg + diff;
      else if (largest.key === 'neutral') neutralPercent = neu + diff;
      else positivePercent = pos + diff;
    } else {
      negativePercent = neg;
      neutralPercent = neu;
      positivePercent = pos;
    }
  }

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
    // Check if backend is ready
    if (!backendStatus || backendError) {
      setSnapshotError("System is still initializing. Please wait a moment and try again.");
      return;
    }

    // Validate all steps before generating
    const errors = validation.validate();

    if (Object.keys(errors).length > 0) {
      validation.setErrors(errors);
      return;
    }

    // Clear any previous validation errors
    validation.clearErrors();

    if (state.isGenerating) return;

    actions.setIsGenerating(true);
    setSnapshotError(null);

    const payload = {
      platforms: state.platforms,
      time_window: state.timeWindow,
      focus_areas: state.focusAreas,
      include_alerts: state.includeAlerts,
      mode: mode,
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

      <div className="min-h-screen bg-slate-50 bg-grid-pattern font-sans">
        <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-0 sm:px-6 lg:flex-row lg:gap-8 lg:px-8 lg:py-10 xl:px-12">

          <Sidebar
            onOpenMobileFilters={() => actions.setShowMobileFilters(true)}
            activePage={activePage}
            onNavigate={onNavigate}
            isSidebarOpen={isSidebarOpen}
            onCloseSidebar={() => setIsSidebarOpen(false)}
          />

          {/* Main Content */}
          <main className="order-1 flex w-full min-w-0 flex-col gap-4 lg:order-2 lg:flex-1 lg:gap-6 xl:gap-8">
            <section className="space-y-4">
              <HeroSection
                selectedWindowLabel={computed.selectedWindowLabel}
                platformSummary={computed.platformSummary}
                focusSummary={computed.focusSummary}
                focusSummaryLabel={computed.focusSummaryLabel}
              />
            </section>

            <section className="grid gap-4 xl:grid-cols-[minmax(0,1.65fr)_minmax(360px,420px)] xl:gap-x-6 xl:items-stretch" role="main" aria-label="Sentiment analysis configuration">
              <div className="flex h-full flex-col space-y-4 rounded-xl border border-slate-200/60 bg-white p-6" role="form" aria-labelledby="config-heading">
                <header className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between border-b border-slate-100 pb-6">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm">
                        <Settings className="h-4 w-4" />
                      </div>
                      <h2 id="config-heading" className="text-xl font-bold tracking-tight text-slate-900 md:text-2xl">Configuration</h2>
                    </div>
                    <p className="text-sm text-slate-500 max-w-xl leading-relaxed">
                      Configure data sources and focus areas. The agent will gather the latest public posts, classify sentiment, and surface actionable intelligence.
                    </p>
                  </div>
                </header>

                {/* Premium Timeline — equal spacing p-6, gap-4 */}
                <div className="relative">
                  <div className="absolute left-[15px] top-3 bottom-6 w-px bg-gradient-to-b from-[#3348b8]/20 via-[#5b3cc8]/20 to-slate-200 hidden sm:block" aria-hidden />
                  <div className="space-y-4">
                    <div className="relative flex gap-4 sm:pl-10">
                      <div className="absolute left-0 top-0 hidden h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm sm:flex" aria-hidden><span className="text-xs font-bold">1</span></div>
                      <div className="flex-1"><PlatformSelector platforms={state.platforms} onToggle={actions.toggleSelection} setPlatforms={actions.setPlatforms} error={validation.errors.platforms} /></div>
                    </div>
                    <div className="relative flex gap-4 sm:pl-10">
                      <div className="absolute left-0 top-0 hidden h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm sm:flex" aria-hidden><span className="text-xs font-bold">2</span></div>
                      <div className="flex-1"><TimeWindowSelector timeWindow={state.timeWindow} setTimeWindow={actions.setTimeWindow} error={validation.errors.timeWindow} /></div>
                    </div>
                    <div className="relative flex gap-4 sm:pl-10">
                      <div className="absolute left-0 top-0 hidden h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white shadow-sm sm:flex" aria-hidden><span className="text-xs font-bold">3</span></div>
                      <div className="flex-1"><FocusAreaSelector focusAreas={state.focusAreas} onToggle={actions.toggleSelection} setFocusAreas={actions.setFocusAreas} error={validation.errors.focusAreas} /></div>
                    </div>
                    <div className="relative flex gap-4 sm:pl-10">
                      <div className="absolute left-0 top-0 hidden h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white border-transparent shadow-sm sm:flex" aria-hidden><span className="text-xs font-bold">4</span></div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Analysis mode</span><span className="text-[11px] text-slate-400">Depth</span></div>
                        <div className="grid gap-2 sm:grid-cols-3">
                        {[
                            { value: 'full', label: 'Full', desc: 'Sentiment + Credibility + Themes' },
                            { value: 'sentiment', label: 'Sentiment', desc: 'Only sentiment' },
                            { value: 'credibility', label: 'Credibility', desc: 'Only verification' }
                        ].map((option) => (
                          <label key={option.value} className={`flex cursor-pointer flex-col rounded-xl border p-4 text-left transition focus-within:ring-2 focus-within:ring-violet-500 ${mode===option.value ? 'border-transparent bg-gradient-to-br from-[#3348b8] to-[#5b3cc8] text-white shadow-sm' : 'border-slate-200 bg-white hover:border-violet-200'}`}>
                            <input type="radio" className="sr-only" checked={mode === option.value} onChange={() => setMode(option.value as AnalysisMode)} value={option.value} name="analysis-mode" />
                            <span className={`text-sm font-semibold ${mode===option.value ? 'text-white' : 'text-slate-800'}`}>{option.label}</span>
                            <span className={`text-xs ${mode===option.value ? 'text-white/80' : 'text-slate-500'}`}>{option.desc}</span>
                          </label>
                        ))}
                        </div>
                      </div>
                    </div>

                    <div className="relative flex gap-4 sm:pl-10">
                      <div className="absolute left-0 top-0 hidden h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-white border-transparent shadow-sm sm:flex" aria-hidden><span className="text-xs font-bold">5</span></div>
                      <label className="flex flex-1 cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 hover:bg-white">
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
                <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-end">
                  <div className="flex flex-col items-end gap-2">
                    {Object.keys(validation.errors).length > 0 && (
                      <p className="text-xs text-rose-500 font-medium">
                        Please complete all required steps before generating
                      </p>
                    )}
                    <KeyboardButton
                      variant="primary"
                      size="md"
                      icon={
                        state.isGenerating ? (
                          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        ) : !backendStatus || backendError ? (
                          <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
                        ) : (
                          <BarChart3 className="h-4 w-4" aria-hidden="true" />
                        )
                      }
                      onClick={handleGenerate}
                      disabled={state.isGenerating || !backendStatus || !!backendError}
                    >
                       {state.isGenerating ? 'Generating Report...' : !backendStatus || backendError ? 'Initializing...' : 'Generate Sentiment Report'}
                    </KeyboardButton>
                  </div>
                </div>
              </div>

              {/* Live Preview — equal height, flat premium */}
              <div className="flex h-full min-h-[900px] w-full max-w-md flex-col space-y-6 rounded-xl border border-slate-200/60 bg-white p-6 sm:mx-0 sm:max-w-none md:min-h-[920px] md:rounded-xl xl:sticky xl:top-6 xl:max-h-[calc(100vh-3rem)] xl:overflow-y-auto xl:scrollbar-thin xl:scrollbar-thumb-slate-300 xl:scrollbar-track-transparent" role="region" aria-labelledby="preview-heading">
                <header className="space-y-1">
                  <h2 id="preview-heading" className="text-lg font-semibold text-slate-900">Live Snapshot Preview</h2>
                  <p className="text-xs text-slate-400">
                    {state.timeWindow} • {computed.platformSummary.length} platform{computed.platformSummary.length === 1 ? '' : 's'}
                  </p>
                  {snapshotError ? (
                    <p className="text-xs text-rose-600">{snapshotError}</p>
                  ) : null}
                </header>

                <div className="flex flex-1 flex-col justify-center space-y-5 min-h-0">
                  {snapshot ? (
                    <>
                      <Card className={clsx(
                        "space-y-4 border border-hinaing-blue-200 bg-gradient-to-br from-hinaing-blue-50 to-violet-50 p-5 transition-all duration-300",
                        hoveredCardIndex === 0 && "transform scale-105 shadow-xl ring-2 ring-hinaing-blue-300"
                      )}>
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-gradient-to-r from-hinaing-blue-500/15 via-hinaing-blue-400/15 to-violet-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-hinaing-blue-800">
                            Overall Sentiment
                          </span>
                          <span className="text-xs font-medium text-hinaing-blue-600">Updated moments ago</span>
                        </div>
                        <div className="space-y-3">
                          <h3 className="text-xl font-semibold text-hinaing-blue-900" id="sentiment-summary">
                            {snapshot.overall_sentiment.label}
                          </h3>
                          <div className="text-sm text-slate-600 space-y-4 leading-relaxed">
                            {(animatedSummary || fullSummaryText).split(/\n\n+/).map((paragraph, idx) => {
                              // Handle **Bold:** pattern for topic headers
                              const parts = paragraph.split(/\*\*([^*]+)\*\*/);
                              return (
                                <p key={idx} className="text-justify">
                                  {parts.map((part, partIdx) =>
                                    partIdx % 2 === 1 ? (
                                      <span key={partIdx} className="font-semibold text-hinaing-blue-700">{part}</span>
                                    ) : (
                                      <span key={partIdx}>{parseCitations(part)}</span>
                                    )
                                  )}
                                  {isTypingSummary && idx === (animatedSummary || fullSummaryText).split(/\n\n+/).length - 1 && (
                                    <span className="inline-block w-[0.5ch] animate-pulse align-baseline">▌</span>
                                  )}
                                </p>
                              );
                            })}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-center text-sm">
                          <div className={clsx(
                            "rounded-lg bg-white/70 p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 1 && "transform scale-105 shadow-xl ring-2 ring-rose-300"
                          )}>
                            <strong className="block text-lg font-semibold text-rose-600">{negativePercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Negative</span>
                          </div>
                          <div className={clsx(
                            "rounded-lg bg-white/70 p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 2 && "transform scale-105 shadow-xl ring-2 ring-slate-300"
                          )}>
                            <strong className="block text-lg font-semibold text-slate-700">{neutralPercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Neutral</span>
                          </div>
                          <div className={clsx(
                            "rounded-lg bg-white/70 p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 3 && "transform scale-105 shadow-xl ring-2 ring-emerald-300"
                          )}>
                            <strong className="block text-lg font-semibold text-emerald-600">{positivePercent}%</strong>
                            <span className="text-2xs uppercase tracking-wide text-slate-500">Positive</span>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 sm:gap-3 text-center text-sm">
                          <div className={clsx(
                            "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 4 && "transform scale-105 shadow-xl ring-2 ring-slate-300"
                          )}>
                            <strong className="block text-base sm:text-lg font-semibold text-slate-700">{credibilityBreakdown.avgScore}%</strong>
                            <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Credibility</span>
                            <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                              {credibilityBreakdown.hasData ? '5-signal analysis' : 'No data yet'}
                            </p>
                          </div>
                          <div className={clsx(
                            "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 5 && "transform scale-105 shadow-xl ring-2 ring-emerald-300"
                          )}>
                            <strong className="block text-base sm:text-lg font-semibold text-emerald-600">{credibilityBreakdown.highCredibility}%</strong>
                            <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Verified</span>
                            <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                              {credibilityBreakdown.hasData ? 'Low risk' : 'Score ≥55%'}
                            </p>
                          </div>
                          <div className={clsx(
                            "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                            hoveredCardIndex === 6 && "transform scale-105 shadow-xl ring-2 ring-rose-300"
                          )}>
                            <strong className="block text-base sm:text-lg font-semibold text-rose-600">{credibilityBreakdown.lowCredibility}%</strong>
                            <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Misinfo</span>
                            <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                              {credibilityBreakdown.hasData ? 'Review needed' : 'Score <55%'}
                            </p>
                          </div>
                        </div>

                        {/* Faithfulness Score - Enhanced with Best Practice Metrics */}
                        {snapshot.verification && (
                          <div className="space-y-2">
                            {/* Row 1: Core Metrics */}
                            <div className="grid grid-cols-3 gap-2 sm:gap-3 text-center text-sm">
                              <div className={clsx(
                                "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                                hoveredCardIndex === 7 && "transform scale-105 shadow-xl ring-2 ring-violet-300"
                              )}>
                                <strong className="block text-base sm:text-lg font-semibold text-violet-600">
                                  {Math.round(snapshot.verification.faithfulness_score * 100)}%
                                </strong>
                                <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Faithfulness</span>
                                <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                                  {snapshot.verification.faithfulness_score >= 0.85 ? '✅ SOTA' : '⚠️ Needs improvement'}
                                </p>
                              </div>
                              <div className={clsx(
                                "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                                hoveredCardIndex === 8 && "transform scale-105 shadow-xl ring-2 ring-emerald-300"
                              )}>
                                <strong className="block text-base sm:text-lg font-semibold text-emerald-600">
                                  {snapshot.verification.verified_claims}/{snapshot.verification.total_claims}
                                </strong>
                                <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Claims Verified</span>
                                <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                                  LLM extraction + NLI verification
                                </p>
                              </div>
                              <div className={clsx(
                                "rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner transition-all duration-300",
                                hoveredCardIndex === 9 && "transform scale-105 shadow-xl ring-2 ring-rose-300"
                              )}>
                                <strong className="block text-base sm:text-lg font-semibold text-rose-600">
                                  {snapshot.verification.unverified_claims}
                                </strong>
                                <span className="text-[9px] sm:text-2xs uppercase tracking-wide text-slate-500 leading-tight block">Unverified</span>
                                <p className="mt-0.5 sm:mt-1 text-[9px] sm:text-[11px] text-slate-500 leading-tight hidden sm:block">
                                  Requires review
                                </p>
                              </div>
                            </div>

                            {/* Row 2: NEW Best Practice Metrics */}
                            {snapshot.verification.hallucination_analysis && (
                              <div className="grid grid-cols-3 gap-2 sm:gap-3 text-center text-sm">
                                {/* Hallucination Count */}
                                <div className="rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner">
                                  <strong className={clsx(
                                    "block text-base sm:text-lg font-semibold",
                                    snapshot.verification.hallucination_analysis.is_hallucination_free
                                      ? "text-emerald-600"
                                      : "text-amber-600"
                                  )}>
                                    {snapshot.verification.hallucination_analysis.hallucination_count}
                                  </strong>
                                  <span className="text-[9px] sm:text-2xs uppercase text-slate-500 block">Halluc.</span>
                                </div>

                                {/* Citation Accuracy */}
                                {snapshot.verification.citation_verification && (
                                  <div className="rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner">
                                    <strong className="block text-base sm:text-lg font-semibold text-blue-600">
                                      {Math.round(snapshot.verification.citation_verification.citation_accuracy_rate * 100)}%
                                    </strong>
                                    <span className="text-[9px] sm:text-2xs uppercase text-slate-500 block">Citation</span>
                                  </div>
                                )}

                                {/* Misattribution Count */}
                                {snapshot.verification.misattribution_analysis && (
                                  <div className="rounded-lg bg-white/80 p-2 sm:p-3 shadow-inner">
                                    <strong className="block text-base sm:text-lg font-semibold text-indigo-600">
                                      {snapshot.verification.misattribution_analysis.misattribution_count}
                                    </strong>
                                    <span className="text-[9px] sm:text-2xs uppercase text-slate-500 block">Misattri.</span>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Hallucination Type Breakdown (if any detected) */}
                            {snapshot.verification.hallucination_analysis &&
                             snapshot.verification.hallucination_analysis.hallucination_count > 0 && (
                              <div className="bg-amber-50/50 border border-amber-200 rounded-lg p-2">
                                <p className="text-[9px] sm:text-[10px] font-semibold uppercase text-amber-700 mb-1.5">
                                  Hallucination Breakdown
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(snapshot.verification.hallucination_analysis.hallucination_types)
                                    .filter(([_, count]) => count > 0)
                                    .map(([type, count]) => (
                                      <span
                                        key={type}
                                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] sm:text-[10px] font-medium"
                                      >
                                        {type === "fabricated_claim" && "🎭"}
                                        {type === "contradicted_claim" && "❌"}
                                        {type === "numerical_hallucination" && "🔢"}
                                        {type.replace("_", " ")}: {count}
                                      </span>
                                    ))}
                                </div>
                              </div>
                            )}

                            {/* Numerical Hallucinations */}
                            {snapshot.verification.numerical_hallucinations &&
                             snapshot.verification.numerical_hallucinations.count > 0 && (
                              <div className="bg-rose-50/50 border border-rose-200 rounded-lg p-2">
                                <p className="text-[9px] sm:text-[10px] font-semibold uppercase text-rose-700 mb-1.5">
                                  ⚠ Numerical Hallucinations Detected
                                </p>
                                <div className="space-y-1">
                                  {snapshot.verification.numerical_hallucinations.details?.slice(0, 3).map((detail, idx) => (
                                    <div key={idx} className="text-[10px] text-rose-700">
                                      <span className="font-medium">Claim:</span> {detail.claim}
                                      <br />
                                      <span className="font-medium">Unsupported numbers:</span> {detail.unsupported_numbers.join(", ")}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

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
                            <div className="space-y-4 max-h-[600px] overflow-y-auto">
                              {snapshot.sources.map((source, index) => {
                                const meta = source.metadata ?? {};
                                return (
                                  <div key={index} className="border border-slate-100 rounded-lg bg-white p-4 shadow-sm">
                                    <div className="space-y-2">
                                      <div className="flex items-start justify-between gap-2">
                                        <h4 className="font-medium text-slate-900 leading-tight flex-1">
                                          {source.title}
                                        </h4>
                                        {source.url && (
                                          <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1 text-hinaing-blue-600 hover:text-hinaing-blue-500 font-medium text-xs flex-shrink-0"
                                          >
                                            View Source
                                            <ExternalLink className="h-3 w-3" />
                                          </a>
                                        )}
                                      </div>
                                      <p className="text-sm text-slate-600 leading-relaxed">
                                        {source.snippet}
                                      </p>
                                      <div className="flex items-center gap-2 flex-wrap text-xs">
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

                                      {/* Verification Badge Component */}
                                      <VerificationBadge
                                        credibilityScore={typeof meta.credibility_score === 'number' ? meta.credibility_score : null}
                                        credibilityTier={typeof meta.credibility_tier === 'string' ? meta.credibility_tier : null}
                                        misinfoRisk={typeof meta.misinfo_risk === 'string' ? meta.misinfo_risk : null}
                                        corroboratingSources={typeof meta.corroborating_sources === 'number' ? meta.corroborating_sources : 0}
                                        tavilyVerifiedSources={Array.isArray(meta.tavily_verified_sources) ? meta.tavily_verified_sources : []}
                                        tavilyVerificationStatus={typeof meta.tavily_verification_status === 'string' ? meta.tavily_verification_status : null}
                                        redFlags={Array.isArray(meta.red_flags) ? meta.red_flags as string[] : []}
                                        factCheckRating={typeof meta.fact_check_rating === 'string' ? meta.fact_check_rating : null}
                                        llmReasoning={typeof meta.llm_reasoning === 'string' ? meta.llm_reasoning : ''}
                                        credibilityBreakdown={typeof meta.credibility_breakdown === 'object' && meta.credibility_breakdown !== null ? meta.credibility_breakdown as Record<string, number> : {}}
                                      />
                                    </div>
                                  </div>
                                );
                              })}
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
                    <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center" role="status" aria-live="polite">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)]">
                        <span className="text-sm font-bold tracking-tight text-white">H</span>
                      </div>
                      <div className="mt-3 flex items-center gap-1.5">
                        <span className="text-sm font-bold tracking-tight text-slate-900">Hinaing</span>
                        <span className="rounded-full border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-slate-500">Baguio</span>
                      </div>
                      <h3 className="mt-2 text-sm font-semibold text-slate-900">No briefing yet</h3>
                      <p className="mt-1 max-w-[28ch] text-xs leading-relaxed text-slate-500">
                        {state.isGenerating ? "Analyzing fresh chatter — this will populate once calculations finish." : "Select channels, window & focus above, then Generate."}
                      </p>
                      <p className="mt-1 text-[11px] text-slate-400">Example: Web · 48 hours · Infrastructure</p>
                      {state.isGenerating ? (
                        <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 border border-slate-200">
                          <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" /> Generating…
                        </span>
                      ) : (
                        <span className="mt-3 inline-flex items-center gap-1 text-[11px] text-slate-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" /> 19 agents idle</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
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
        mode={mode}
        setMode={setMode}
        onToggleSelection={actions.toggleSelection}
        setPlatforms={actions.setPlatforms}
        setTimeWindow={actions.setTimeWindow}
        setFocusAreas={actions.setFocusAreas}
        setIncludeAlerts={actions.setIncludeAlerts}
      />
    </>
  );
}

