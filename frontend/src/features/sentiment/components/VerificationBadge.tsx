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
  // Priority: External verification > Internal signals > Red flags
  const getVerificationStatus = () => {
    // 1. CONTRADICTED - Tavily found contradicting sources (highest priority)
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

    // 2. VERIFIED - External verification takes priority over red flags
    // If Tavily verified the claim with trusted sources, it's verified regardless of source bias
    if (tavilyVerificationStatus === 'verified' || (hasTavilyVerification && corroboratingSources >= 2)) {
      return {
        status: 'verified',
        icon: ShieldCheck,
        label: 'Verified Event',
        description: 'This event has been corroborated by trusted news sources.',
        bgColor: 'bg-emerald-50',
        borderColor: 'border-emerald-300',
        textColor: 'text-emerald-800',
        iconColor: 'text-emerald-600',
        badgeColor: 'bg-emerald-100 text-emerald-700',
      };
    }

    // 3. LIKELY ACCURATE - Good corroboration even with some red flags
    if ((hasTavilyVerification || corroboratingSources >= 1) && tier !== 'very_low') {
      return {
        status: 'likely_accurate',
        icon: CheckCircle,
        label: 'Likely Accurate',
        description: hasRedFlags 
          ? 'Event verified, but source may have bias. Cross-reference recommended.'
          : 'This claim appears credible based on source reputation and corroboration.',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-300',
        textColor: 'text-blue-800',
        iconColor: 'text-blue-600',
        badgeColor: 'bg-blue-100 text-blue-700',
      };
    }

    // 4. POTENTIAL MISINFORMATION - Only if NO external verification AND high risk
    if ((misinfoRisk === 'high' || tier === 'very_low') && !hasTavilyVerification && corroboratingSources === 0) {
      return {
        status: 'misinfo',
        icon: ShieldX,
        label: 'Potential Misinformation',
        description: 'This source shows signs of misinformation and lacks external verification.',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-300',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
        badgeColor: 'bg-red-100 text-red-700',
      };
    }

    // 5. NEEDS VERIFICATION - Low credibility or red flags without corroboration
    if (tier === 'low' || (hasRedFlags && !hasTavilyVerification)) {
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
          {/* Signal Breakdown - Compact */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
              5-Signal Analysis
            </p>
            <div className="space-y-1.5">
              {Object.entries(credibilityBreakdown)
                .filter(([signal]) => !['content_signals', 'recency'].includes(signal))
                .map(([signal, score]) => {
                  const signalNames: Record<string, string> = {
                    domain: 'Domain Trust',
                    cross_reference: 'Internal Cross-Ref',
                    fact_check: 'Fact Check API',
                    llm: 'AI Analysis',
                    tavily: 'External Cross-Ref',
                  };
                  const displayName = signalNames[signal] || signal.replace(/_/g, ' ');
                  const percentage = Math.round((score || 0) * 100);

                  let barColor = "bg-slate-400";
                  if ((score || 0) >= 0.7) barColor = "bg-emerald-500";
                  else if ((score || 0) >= 0.45) barColor = "bg-amber-500";
                  else barColor = "bg-rose-500";

                  return (
                    <div key={signal} className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-600 w-24 truncate" title={displayName}>
                        {displayName}
                      </span>
                      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className={clsx("h-full rounded-full", barColor)}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-semibold text-slate-700 w-8 text-right">
                        {percentage}%
                      </span>
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
              Verification powered by 5-signal ensemble: Domain Trust, Internal Cross-Reference,
              Google Fact Check API, Gemini AI Analysis, and Tavily External Cross-Reference.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
