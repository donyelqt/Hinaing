'use client';

import React from 'react';

/**
 * Parse and render citations as compact superscript footnote chips.
 *
 * Backend emits several variants (see backend/app/services/nlp/gemini.py):
 *   [Src: domain | Sent: X | verified]            (canonical)
 *   [Src: domain | X | vsee_bypass]               (label-less sentiment, internal status)
 *   [Src: domain | X | skipped_limit]             (unmapped internal status)
 *   [Src: url | Cred: 0.XX | Sent: X | verified]  (legacy 4-segment)
 *
 * Internal statuses are mapped to user-facing labels:
 *   vsee_bypass -> verified, skipped_limit/rate_limited/error -> unverified
 *
 * @param text - The paragraph text potentially containing citations
 * @returns Array of JSX elements (strings and citation chips)
 */
type DisplayStatus = 'verified' | 'contradicted' | 'unverified';

function mapStatus(raw: string): { display: DisplayStatus; wasMapped: boolean } {
  const normalized = raw.trim().toLowerCase();
  if (normalized === 'verified' || normalized === 'vsee_bypass') {
    return { display: 'verified', wasMapped: normalized === 'vsee_bypass' };
  }
  if (normalized === 'contradicted') {
    return { display: 'contradicted', wasMapped: false };
  }
  return { display: 'unverified', wasMapped: normalized !== 'unverified' };
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

const DOT_CLASS: Record<DisplayStatus, string> = {
  verified: 'bg-emerald-500',
  contradicted: 'bg-rose-500',
  unverified: 'bg-amber-500',
};

export function parseCitations(text: string): (string | React.JSX.Element)[] {
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
    const { display } = mapStatus(status);

    parts.push(
      <sup
        key={`citation-${match.index}`}
        className="ml-1 inline-flex translate-y-[-1px] items-center gap-1.5 whitespace-nowrap rounded-full border border-slate-200 bg-white px-2 py-0.5 align-baseline text-[10px] font-medium leading-5 text-slate-500 shadow-sm"
        title={`Source: ${domain} | Sentiment: ${sentiment} | ${display}`}
        aria-label={`Citation: ${domain}, sentiment ${sentiment}, ${display}`}
      >
        <span aria-hidden="true" className={`inline-block h-1.5 w-1.5 rounded-full ${DOT_CLASS[display]}`} />
        <span className="max-w-[10rem] truncate">{domain}</span>
        <span className="text-slate-400">{display}</span>
      </sup>
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
