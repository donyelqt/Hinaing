'use client';

import React from 'react';

/**
 * Parse citations into numbered reference chips (e.g. [1], [2]).
 *
 * Backend emits several variants (see backend/app/services/nlp/gemini.py):
 *   [Src: domain | Sent: X | verified]            (canonical)
 *   [Src: domain | X | vsee_bypass]               (label-less sentiment, internal status)
 *   [Src: domain | X | skipped_limit]             (unmapped internal status)
 *   [Src: url | Cred: 0.XX | Sent: X | verified]  (legacy 4-segment)
 *
 * Numbers map to the snapshot's source list by domain. Internal statuses
 * are mapped to user-facing labels (vsee_bypass -> verified,
 * skipped_limit/rate_limited/error -> unverified).
 *
 * @param text - The paragraph text potentially containing citations
 * @param sources - Snapshot sources ({ url }) used to number references
 * @returns Array of JSX elements (strings and reference chips)
 */
type DisplayStatus = 'verified' | 'contradicted' | 'unverified';

export interface CitationSource {
  url?: string | null;
}

function normalizeHost(value: string): string {
  const host = value.includes('://') ? value : `https://${value}`;
  try {
    return new URL(host).hostname.replace(/^www\./, '').toLowerCase();
  } catch {
    return value.trim().replace(/^www\./, '').toLowerCase();
  }
}

function mapStatus(raw: string): DisplayStatus {
  const normalized = raw.trim().toLowerCase();
  if (normalized === 'verified' || normalized === 'vsee_bypass') return 'verified';
  if (normalized === 'contradicted') return 'contradicted';
  return 'unverified';
}

function parseSegments(inner: string): { domain: string; sentiment: string; status: string } | null {
  const segments = inner.split('|').map((s) => s.trim()).filter(Boolean);
  if (segments.length < 3) return null;
  const domain = segments[0];
  const status = segments[segments.length - 1];
  // Sentiment is the segment tagged with Sent:, else the second-to-last.
  const tagged = segments.find((s) => /^sent\s*:/i.test(s));
  const sentiment = (tagged ?? segments[segments.length - 2]).replace(/^sent\s*:/i, '').trim();
  if (!domain || !sentiment || !status) return null;
  return { domain, sentiment, status };
}

const CHIP_CLASS: Record<DisplayStatus, string> = {
  verified: 'bg-emerald-100 text-emerald-700',
  contradicted: 'bg-rose-100 text-rose-700',
  unverified: 'bg-amber-100 text-amber-700',
};

export function parseCitations(
  text: string,
  sources?: CitationSource[],
): (string | React.JSX.Element)[] {
  // Number sources by domain for [n] references.
  const indexByHost = new Map<string, number>();
  (sources ?? []).forEach((source) => {
    if (!source?.url) return;
    const host = normalizeHost(source.url);
    if (host && !indexByHost.has(host)) {
      indexByHost.set(host, indexByHost.size + 1);
    }
  });

  // Match any [Src: ...] block; segments are interpreted leniently.
  const citationRegex = /\[Src:\s*([^\]]+?)\]/g;

  const parts: (string | React.JSX.Element)[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    const parsed = parseSegments(match[1]);
    if (!parsed) {
      continue; // Leave unrecognized blocks as plain text.
    }
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const { domain, sentiment, status } = parsed;
    const display = mapStatus(status);
    const refNumber = indexByHost.get(normalizeHost(domain)) ?? null;
    const label = `Source${refNumber ? ` ${refNumber}` : ''}: ${domain} | Sentiment: ${sentiment} | ${display}`;

    parts.push(
      refNumber !== null ? (
        <sup
          key={`citation-${match.index}`}
          className={`ml-0.5 inline-flex h-4 min-w-4 translate-y-[-2px] items-center justify-center rounded-md px-1 align-baseline text-[10px] font-bold leading-4 ${CHIP_CLASS[display]}`}
          title={label}
          aria-label={`Citation ${label}`}
        >
          {refNumber}
        </sup>
      ) : (
        <sup
          key={`citation-${match.index}`}
          className="ml-0.5 inline-flex h-4 translate-y-[-2px] items-center rounded-md bg-slate-100 px-1 align-baseline text-[10px] font-medium leading-4 text-slate-500"
          title={label}
          aria-label={`Citation ${label}`}
        >
          {domain.length > 18 ? `${domain.slice(0, 17)}…` : domain}
        </sup>
      ),
    );

    lastIndex = citationRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  // No citation found: return original text untouched.
  if (parts.length === 0) {
    parts.push(text);
  }

  return parts;
}

/** Paragraphs containing only punctuation/whitespace (e.g. stray ".") carry no content. */
export function isEmptyParagraph(paragraph: string): boolean {
  return /^[\s.\-–—*_"']*$/.test(paragraph);
}
