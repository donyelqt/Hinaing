export type SentimentScores = Record<string, number>;

export type CredibilitySummary = {
    avg_score: number;
    high_percent: number;
    review_percent: number;
};

export type CredibilityBreakdown = {
    /** Share of documents the system cleared without external corroboration. */
    verifiedPercent: number;
    /** Complement of verifiedPercent over the same denominator. */
    reviewPercent: number;
    /** Mean 5-signal credibility score. */
    avgScore: number;
    hasData: boolean;
};

/**
 * Round the three sentiment scores so they sum to 100, matching the chat
 * analyze page. Returns null when the snapshot carries no scores, so the
 * caller hides the card instead of showing a default split.
 */
export function sentimentPercents(scores?: SentimentScores | null): { negative: number; neutral: number; positive: number } | null {
    if (!scores || typeof scores.negative !== 'number' || typeof scores.neutral !== 'number' || typeof scores.positive !== 'number') {
        return null;
    }

    let negative = Math.round((scores.negative ?? 0) * 100);
    let neutral = Math.round((scores.neutral ?? 0) * 100);
    let positive = Math.round((scores.positive ?? 0) * 100);
    const total = negative + neutral + positive;

    if (total === 100) return { negative, neutral, positive };

    const diff = 100 - total;
    const largest = [
        { value: negative, key: 'negative' as const },
        { value: neutral, key: 'neutral' as const },
        { value: positive, key: 'positive' as const },
    ].reduce((a, b) => (a.value > b.value ? a : b));

    if (largest.key === 'negative') negative += diff;
    else if (largest.key === 'neutral') neutral += diff;
    else positive += diff;

    return { negative, neutral, positive };
}

/**
 * Read the credibility numbers the backend already computed, the same object
 * the chat analyze page reads. Recomputing from sources divided by a different
 * denominator, so the two pages disagreed.
 */
export function computeCredibilityBreakdown(
    credibility?: CredibilitySummary | null,
    sources?: unknown,
): CredibilityBreakdown {
    void sources;
    if (!credibility) {
        return { verifiedPercent: 0, reviewPercent: 0, avgScore: 0, hasData: false };
    }

    return {
        verifiedPercent: Math.round(credibility.high_percent),
        reviewPercent: Math.round(credibility.review_percent),
        avgScore: Math.round(credibility.avg_score),
        hasData: true,
    };
}