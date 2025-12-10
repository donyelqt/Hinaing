"use client";

import * as React from "react";
import clsx from "clsx";
import { Shield, ShieldAlert, ShieldCheck, ShieldX, ExternalLink, ChevronDown, ChevronUp, CheckCircle, XCircle, AlertCircle } from "lucide-react";

type TavilySource = {
  url: string;
  domain: string;
  title: string;
};

type VerificationBadgeProps = {
  credibilityScore: number | null;
  credibilityTier: string | null;
  misinfoRisk: string | null;
  corroboratingSources: number;
  tavilyVerifiedSources: (string | TavilySource)[]; // Support both old (string) and new (object) format
  tavilyVerificationStatus?: string | null; // "verified", "contradicted", "disputed", "partial", "unverified"
  redFlags: string[];
  factCheckRating: string | null;
  llmReasoning: string;
  credibilityBreakdown: {
    domain?: number;
    cross_reference?: number;
    fact_check?: number;
    llm?: number;
    content_signals?: number;
    recency?: number;
    tavily?: number;
  };
};

export function VerificationBadge({
  credibilityScore,
  credibilityTier,
  misinfoRisk,
  corroboratingSources,
  tavilyVerifiedSources,
  tavilyVerificationStatus,
  redFlags,
  factCheckRating,
  llmReasoning,
  credibilityBreakdown,
}: VerificationBadgeProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const displayScore = credibilityScore !== null ? Math.round(credibilityScore * 100) : null;
  const tier = credibilityTier || (credibilityScore !== null
    ? (credibilityScore >= 0.75 ? 'high' : credibilityScore >= 0.55 ? 'medium' : credibilityScore >= 0.35 ? 'low' : 'very_low')
    : null);

  const hasTavilyVerification = tavilyVerifiedSources.length > 0;
  const hasRedFlags = redFlags.length > 0;

  // Determine claim verification status
  const getVerificationStatus = () => {
    // CONTRADICTED - Tavily found contradicting sources (highest priority)
    if (tavilyVerificationStatus === 'contradicted' || tavilyVerificationStatus === 'disputed') {
      return {
        status: 'contradicted',
        icon: ShieldX,
        label: 'Claim Disputed',
        description: 'This claim has been contradicted or disputed by trusted sources.',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-300',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
        badgeColor: 'bg-red-100 text-red-700',
      };
    }

    // MISINFORMATION - High risk or very low credibility with red flags
    if (misinfoRisk === 'high' || (tier === 'very_low' && hasRedFlags)) {
      return {
        status: 'misinfo',
        icon: ShieldX,
        label: 'Potential Misinformation',
        description: 'This source shows signs of misinformation. Verify before sharing.',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-300',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
        badgeColor: 'bg-red-100 text-red-700',
      };
    }

    // VERIFIED - Tavily confirmed OR high credibility with external verification
    if (tavilyVerificationStatus === 'verified' || (tier === 'high' && (hasTavilyVerification || corroboratingSources >= 2))) {
      return {
        status: 'verified',
        icon: ShieldCheck,
        label: 'Verified Claim',
        description: 'This claim has been corroborated by multiple trusted sources.',
        bgColor: 'bg-emerald-50',
        borderColor: 'border-emerald-300',
        textColor: 'text-emerald-800',
        iconColor: 'text-emerald-600',
        badgeColor: 'bg-emerald-100 text-emerald-700',
      };
    }

    // LIKELY ACCURATE - Medium-high credibility with some verification
    if ((tier === 'high' || tier === 'medium') && (hasTavilyVerification || corroboratingSources >= 1 || tavilyVerificationStatus === 'partial')) {
      return {
        status: 'likely_accurate',
        icon: CheckCircle,
        label: 'Likely Accurate',
        description: 'This claim appears credible based on source reputation and corroboration.',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-300',
        textColor: 'text-blue-800',
        iconColor: 'text-blue-600',
        badgeColor: 'bg-blue-100 text-blue-700',
      };
    }

    // NEEDS VERIFICATION - Low credibility or no corroboration
    if (tier === 'low' || hasRedFlags) {
      return {
        status: 'needs_verification',
        icon: AlertCircle,
        label: 'Needs Verification',
        description: 'This claim lacks sufficient corroboration. Verify with additional sources.',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-300',
        textColor: 'text-amber-800',
        iconColor: 'text-amber-600',
        badgeColor: 'bg-amber-100 text-amber-700',
      };
    }

    // UNVERIFIED - Default state
    return {
      status: 'unverified',
      icon: Shield,
      label: 'Unverified',
      description: 'No verification data available for this claim.',
      bgColor: 'bg-slate-50',
      borderColor: 'border-slate-200',
      textColor: 'text-slate-700',
      iconColor: 'text-slate-500',
      badgeColor: 'bg-slate-100 text-slate-600',
    };
  };

  const verification = getVerificationStatus();
  const StatusIcon = verification.icon;

  if (displayScore === null) return null;

  return (
    <div className={clsx(
      "mt-3 rounded-lg border p-3",
      verification.bgColor,
      verification.borderColor
    )}>
      {/* Header - Always visible */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-start justify-between text-left gap-2"
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <StatusIcon className={clsx("h-5 w-5", verification.iconColor)} />
            <span className={clsx("text-sm font-semibold", verification.textColor)}>
              {verification.label}
            </span>
            <span className={clsx("px-2 py-0.5 rounded-full text-[10px] font-medium", verification.badgeColor)}>
              {displayScore}% credibility
            </span>
          </div>
          <p className={clsx("mt-1 text-xs", verification.textColor, "opacity-80")}>
            {verification.description}
          </p>
          {/* Quick stats */}
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            {hasTavilyVerification && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-medium">
                <CheckCircle className="h-3 w-3" />
                {tavilyVerifiedSources.length} external sources verified
              </span>
            )}
            {corroboratingSources > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-medium">
                +{corroboratingSources} corroborating sources
              </span>
            )}
            {hasRedFlags && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-medium">
                <XCircle className="h-3 w-3" />
                {redFlags.length} red flag{redFlags.length > 1 ? 's' : ''} detected
              </span>
            )}
          </div>
        </div>
        <div className="flex-shrink-0">
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-slate-200 space-y-4">
          {/* Signal Breakdown */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
              7-Signal Analysis
            </p>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-2">
              {Object.entries(credibilityBreakdown).map(([signal, score]) => {
                // Full signal name mapping
                const signalNames: Record<string, string> = {
                  domain: 'Domain Trust',
                  cross_reference: 'Internal Cross-Ref',
                  fact_check: 'Fact Check API',
                  llm: 'AI Analysis',
                  content_signals: 'Content Signals',
                  recency: 'Recency',
                  tavily: 'External Cross-Ref',
                };
                const displayName = signalNames[signal] || signal.replace(/_/g, ' ');
                const percentage = Math.round((score || 0) * 100);

                // Determine color based on score
                let colorClass = "bg-slate-500";
                let textClass = "text-slate-700";

                if ((score || 0) >= 0.7) {
                  colorClass = "bg-emerald-500";
                  textClass = "text-emerald-700";
                } else if ((score || 0) >= 0.45) {
                  colorClass = "bg-amber-500";
                  textClass = "text-amber-700";
                } else {
                  colorClass = "bg-rose-500";
                  textClass = "text-rose-700";
                }

                return (
                  <div key={signal} className="group flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-all hover:border-slate-300 hover:shadow-md">
                    <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
                      <span className="text-xs sm:text-sm font-bold text-slate-900 leading-tight" title={displayName}>
                        {displayName}
                      </span>
                      <span className={clsx("text-xs font-black tabular-nums flex-shrink-0", textClass)}>
                        {percentage}%
                      </span>
                    </div>

                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-slate-200/50">
                      <div
                        className={clsx("h-full rounded-full transition-all duration-500 ease-out", colorClass)}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* External Cross-Reference (Tavily) */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
              External Cross-Reference (Tavily)
            </p>
            {/* Verification Status Badge */}
            <div className="mb-2">
              {tavilyVerificationStatus === 'verified' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-semibold">
                  <CheckCircle className="h-4 w-4" />
                  Claim Verified by Trusted Sources
                </span>
              )}
              {tavilyVerificationStatus === 'contradicted' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-100 text-red-700 text-xs font-semibold">
                  <XCircle className="h-4 w-4" />
                  Claim Contradicted by Sources
                </span>
              )}
              {tavilyVerificationStatus === 'disputed' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-100 text-orange-700 text-xs font-semibold">
                  <AlertCircle className="h-4 w-4" />
                  Claim Disputed
                </span>
              )}
              {tavilyVerificationStatus === 'partial' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-100 text-blue-700 text-xs font-semibold">
                  <Shield className="h-4 w-4" />
                  Partially Verified
                </span>
              )}
              {(!tavilyVerificationStatus || tavilyVerificationStatus === 'unverified' || tavilyVerificationStatus === 'no_claims') && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold">
                  <Shield className="h-4 w-4" />
                  No External Verification Found
                </span>
              )}
              {tavilyVerificationStatus === 'disabled' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 text-slate-500 text-xs font-semibold">
                  <Shield className="h-4 w-4" />
                  Tavily API Not Configured
                </span>
              )}
            </div>
            
            {/* Verified Sources List */}
            {hasTavilyVerification && (
              <div className="space-y-1.5">
                <p className="text-[10px] text-slate-500 mb-1">Corroborating sources found:</p>
                {tavilyVerifiedSources.map((source, idx) => {
                  // Handle both old format (string) and new format (object with url, domain, title)
                  const isObject = typeof source === 'object' && source !== null;
                  const url = isObject ? (source as TavilySource).url : `https://www.google.com/search?q=site:${encodeURIComponent(source as string)}`;
                  const domain = isObject ? (source as TavilySource).domain : (source as string);
                  const title = isObject ? (source as TavilySource).title : (source as string);
                  
                  return (
                    <a
                      key={idx}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-emerald-100 hover:bg-emerald-200 text-emerald-700 text-xs transition-colors group"
                    >
                      <CheckCircle className="h-3.5 w-3.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <span className="block truncate font-medium">{title}</span>
                        <span className="block truncate text-[10px] text-emerald-600 opacity-75">{domain}</span>
                      </div>
                      <ExternalLink className="h-3 w-3 flex-shrink-0 opacity-50 group-hover:opacity-100" />
                    </a>
                  );
                })}
                <p className="mt-1.5 text-[9px] text-slate-400">
                  Click to view the original articles
                </p>
              </div>
            )}
          </div>

          {/* Fact Check Rating */}
          {factCheckRating && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Fact Check Rating (Google Fact Check API)
              </p>
              <span className={clsx(
                "inline-block px-2.5 py-1 rounded text-xs font-medium",
                factCheckRating.toLowerCase().includes('true') ? "bg-emerald-100 text-emerald-700" :
                  factCheckRating.toLowerCase().includes('false') ? "bg-red-100 text-red-700" :
                    "bg-amber-100 text-amber-700"
              )}>
                {factCheckRating}
              </span>
            </div>
          )}

          {/* LLM Reasoning */}
          {llmReasoning && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
                AI Analysis (Gemini)
              </p>
              <p className="text-[11px] sm:text-xs text-slate-600 leading-relaxed bg-white/50 rounded-lg p-2">
                {llmReasoning}
              </p>
            </div>
          )}

          {/* Red Flags */}
          {hasRedFlags && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-red-600 mb-2">
                ⚠ Red Flags Detected
              </p>
              <div className="flex flex-wrap gap-1.5">
                {redFlags.map((flag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 rounded-lg bg-red-100 text-red-700 text-[10px] sm:text-xs font-medium"
                  >
                    {flag.replace(/_/g, ' ').toLowerCase()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Verification Info Footer */}
          <div className="pt-2 border-t border-slate-200">
            <p className="text-[9px] text-slate-400 leading-relaxed">
              Verification powered by 7-signal ensemble: Domain Trust, Semantic Cross-Reference,
              Google Fact Check API, Gemini AI Analysis, Content Signals, Recency, and Tavily Web Search.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
