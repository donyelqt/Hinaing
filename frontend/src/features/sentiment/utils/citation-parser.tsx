'use client';

import React from 'react';

/**
 * Parse and render citations with blue styling.
 *
 * Citation format: [Src: domain.com | Sent: SENTIMENT | Verified/Unverified/Contradicted]
 *
 * @param text - The paragraph text potentially containing citations
 * @returns Array of JSX elements (strings and styled citation spans)
 */
export function parseCitations(text: string): (string | React.JSX.Element)[] {
  // Regex to match citation format: [Src: domain.com | Sent: SENTIMENT | Status]
  const citationRegex = /\[Src:\s*([^\]|]+)\s*\|\s*Sent:\s*([^\]|]+)\s*\|\s*([^\]]+)\]/g;

  const parts: (string | React.JSX.Element)[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    // Extract citation parts
    const [, domain, sentiment, status] = match;

    // Create styled citation element with improved responsive styling
    parts.push(
      <span
        key={`citation-${match.index}`}
        className="inline-flex flex-col sm:flex-row sm:flex-wrap items-start gap-x-0.5 sm:gap-x-1 gap-y-0 text-hinaing-blue-600 font-semibold max-w-full align-baseline hover:text-hinaing-blue-700 hover:bg-hinaing-blue-50 rounded px-1 py-0.5 transition-colors cursor-pointer"
        title={`Source: ${domain.trim()} | Sentiment: ${sentiment.trim()} | ${status.trim()}`}
      >
        <span className="text-[8px] sm:text-[10px] leading-tight">[Src:</span>
        <span className="text-[8px] sm:text-[10px] font-medium leading-tight">{domain.trim()}</span>
        <span className="text-[8px] sm:text-[10px] leading-tight">| Sent:</span>
        <span className="text-[8px] sm:text-[10px] font-medium leading-tight">{sentiment.trim()}</span>
        <span className="text-[8px] sm:text-[10px] leading-tight">|</span>
        <span className={`text-[8px] sm:text-[10px] font-semibold leading-tight whitespace-nowrap ${
          status.trim().toLowerCase() === 'verified' ? 'text-emerald-600' :
          status.trim().toLowerCase() === 'contradicted' ? 'text-rose-600' :
          'text-amber-600'
        }`}>
          {status.trim()}
        </span>
        <span className="text-[8px] sm:text-[10px] leading-tight">]</span>
      </span>
    );

    lastIndex = citationRegex.lastIndex;
  }

  // Add remaining text after last citation
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}
