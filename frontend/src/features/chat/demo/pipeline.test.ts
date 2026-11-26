import { describe, it, expect } from 'vitest';

import { DEMO_DOCUMENTS, DEMO_THEME_LABELS, documentsForTheme } from './corpus-data';
import { DEMO_NODES, DEMO_PROMPT, DEMO_SIGNALS, buildDemoResult } from './pipeline';

describe('frozen pipeline corpus', () => {
  it('holds more than 100 real documents', () => {
    expect(DEMO_DOCUMENTS.length).toBeGreaterThan(100);
  });

  it('gives every document a source url and a sentiment', () => {
    for (const doc of DEMO_DOCUMENTS) {
      expect(doc.url).toMatch(/^https?:\/\//);
      expect(['positive', 'neutral', 'negative']).toContain(doc.sentiment);
      expect(doc.title.length).toBeGreaterThan(0);
    }
  });

  it('covers all six civic themes with documents in each', () => {
    const themes = Object.keys(DEMO_THEME_LABELS);
    expect(themes).toHaveLength(6);
    for (const theme of themes) {
      expect(documentsForTheme(theme as never).length).toBeGreaterThan(0);
    }
  });

  it('names every theme and platform in the demo prompt', () => {
    for (const label of Object.values(DEMO_THEME_LABELS)) {
      expect(DEMO_PROMPT.toLowerCase()).toContain(label.toLowerCase());
    }
    expect(DEMO_PROMPT).toContain('Facebook');
    expect(DEMO_PROMPT).toContain('Reddit');
  });
});

describe('frozen pipeline replay', () => {
  it('walks the seven nodes in the same order as the live graph', () => {
    expect(DEMO_NODES.map((node) => node.id)).toEqual([
      'query_orchestrator',
      'retrieval',
      'recall',
      'analyze',
      'memory',
      'themes',
      'snapshot',
    ]);
  });

  it('names the five credibility signals the live agent runs', () => {
    expect(DEMO_SIGNALS).toEqual(['Domain', 'CrossRef', 'FactChk', 'LLM', 'Tavily']);
  });

  it('derives every number from the corpus rather than hardcoding it', () => {
    const result = buildDemoResult();
    expect(result.document_count).toBe(DEMO_DOCUMENTS.length);
    expect(result.sources).toHaveLength(DEMO_DOCUMENTS.length);
    const total =
      result.overall_sentiment.scores.positive +
      result.overall_sentiment.scores.negative +
      result.overall_sentiment.scores.neutral;
    expect(total).toBe(100);
  });

  it('reports one insight per theme with evidence urls', () => {
    const result = buildDemoResult();
    expect(result.insights).toHaveLength(6);
    for (const insight of result.insights) {
      expect(insight.evidence.length).toBeGreaterThan(0);
      expect(insight.detail).toContain('documents retrieved');
    }
  });

  it('derives faithfulness from claims that cite a verifiable source', () => {
    const result = buildDemoResult();
    const { verified_claims: verified, total_claims: total, unverified_claims: unverified } =
      result.verification;
    expect(verified + unverified).toBe(total);
    expect(result.verification.faithfulness_score).toBeCloseTo(verified / total, 3);
    expect(result.verification.faithfulness_rate).toBe(result.verification.faithfulness_score);
    expect(result.verification.hallucination_analysis.hallucination_count).toBe(0);
    expect(unverified).toBeGreaterThan(0);
  });

  it('derives Verified Hinaing from VSEE bypass, not a domain bucket', () => {
    const result = buildDemoResult();
    const highShare = result.credibility.high_percent;
    expect(highShare).toBeGreaterThan(90);
    expect(highShare).toBeLessThanOrEqual(100);
    // The external share is the complement: documents sent to Tavily.
    expect(result.credibility.low_percent).toBeGreaterThanOrEqual(0);
    expect(highShare + result.credibility.low_percent).toBe(100);
  });
});