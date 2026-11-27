import { describe, expect, it } from 'vitest';

import { computeCredibilityBreakdown, sentimentPercents } from './sentiment-numbers';

describe('sentimentPercents', () => {
    it('returns null when the snapshot carries no scores', () => {
        expect(sentimentPercents(undefined)).toBeNull();
        expect(sentimentPercents({})).toBeNull();
    });

    it('rounds the three scores so they sum to 100', () => {
        const result = sentimentPercents({ negative: 0.372, neutral: 0.561, positive: 0.067 });

        expect(result).toEqual({ negative: 37, neutral: 56, positive: 7 });
        expect(result!.negative + result!.neutral + result!.positive).toBe(100);
    });
});

describe('computeCredibilityBreakdown', () => {
    it('returns hasData false when the snapshot has no credibility object', () => {
        expect(computeCredibilityBreakdown(null, undefined)).toEqual({
            avgScore: 0,
            verifiedPercent: 0,
            reviewPercent: 0,
            hasData: false,
        });
    });

    it('reads the server object instead of recomputing from sources', () => {
        const sources = [{ metadata: { credibility_score: 0.1, tavily_verification_status: 'unverified' } }];
        const credibility = { avg_score: 72, high_percent: 85, review_percent: 15 };

        const result = computeCredibilityBreakdown(credibility, sources);

        expect(result).toEqual({ avgScore: 72, verifiedPercent: 85, reviewPercent: 15, hasData: true });
    });
});