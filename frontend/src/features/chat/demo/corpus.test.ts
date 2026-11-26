import { describe, it, expect } from 'vitest';

import {
  DEMO_PROMPT,
  DEMO_THEMES,
  DEMO_THEME_IDS,
  buildDemoResult,
  buildDemoSweep,
  getDemoTheme,
  isDemoThemeId,
} from './corpus';

describe('frozen demo corpus', () => {
  it('covers all six themes exactly once', () => {
    expect(DEMO_THEMES).toHaveLength(6);
    expect(new Set(DEMO_THEMES.map((theme) => theme.id)).size).toBe(6);
  });
  it('sweeps all six themes into one result with every source kept', () => {
    const sweep = buildDemoSweep();
    const categories = new Set(sweep.insights.map((insight) => insight.category));
    expect(categories.size).toBe(6);
    expect(sweep.sources).toHaveLength(
      DEMO_THEMES.reduce((total, theme) => total + theme.sources.length, 0),
    );
    expect(sweep.document_count).toBeGreaterThan(0);
  });

  it('reports scores that sum to 100 so the card cannot show a broken bar', () => {
    const { scores } = buildDemoSweep().overall_sentiment;
    expect(scores.positive + scores.negative + scores.neutral).toBe(100);
  });

  it('names every theme the demo prompt promises', () => {
    for (const theme of DEMO_THEMES) {
      expect(DEMO_PROMPT).toContain(theme.label.toLowerCase());
    }
  });

  it('names all three platforms in the prompt', () => {
    expect(DEMO_PROMPT).toContain('web');
    expect(DEMO_PROMPT).toContain('Facebook');
    expect(DEMO_PROMPT).toContain('Reddit');
  });

  it('carries real retrieved sources for every theme', () => {
    for (const theme of DEMO_THEMES) {
      expect(theme.sources.length).toBeGreaterThan(0);
      for (const source of theme.sources) {
        expect(source.title.length).toBeGreaterThan(0);
      }
    }
  });

  it('ships no prompt injection text in any frozen field', () => {
    const serialized = JSON.stringify(DEMO_THEMES).toUpperCase();
    expect(serialized).not.toContain('IGNORE PRIOR');
    expect(serialized).not.toContain('SYSTEM PROMPT');
    expect(serialized).not.toContain('EVACUAT');
  });

  it('builds a result the existing card can render without a special case', () => {
    const result = buildDemoResult('safety');
    expect(result.mode).toBe('analyze');
    expect(result.overall_sentiment.label.length).toBeGreaterThan(0);
    expect(result.insights.length).toBeGreaterThan(0);
    expect(result.sources.length).toBeGreaterThan(0);
    expect(result.insights[0]).toHaveProperty('category');
    expect(result.insights[0]).toHaveProperty('evidence');
  });

  it('rejects an unknown theme rather than rendering an empty card', () => {
    expect(() => getDemoTheme('traffic' as never)).toThrow(/Unknown demo theme/);
  });

  it('guards the theme id at the boundary', () => {
    expect(isDemoThemeId('health')).toBe(true);
    expect(isDemoThemeId('traffic')).toBe(false);
    expect(DEMO_THEME_IDS).toHaveLength(6);
  });
});