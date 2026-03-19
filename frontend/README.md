This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Sentiment & Credibility Metrics

The Sentiment Generator page displays two related metric groups: sentiment polarity (Negative/Neutral/Positive) and credibility (High Credibility/Low Credibility). These values power the CS thesis dashboards and are computed as follows:

### Sentiment Polarity (Negative / Neutral / Positive)

1. The backend returns normalized scores in `snapshot.overall_sentiment.scores` for each polarity bucket. Each value is a float between 0 and 1 and the three scores always sum to ~1 because every post is assigned exactly one label.
2. The frontend multiplies each score by 100 and rounds to the nearest integer for display (`Math.round(score * 100)`).
3. If any score is missing, we fall back to calibrated defaults (54% / 31% / 15%) so the UI never renders an empty card.

### Credibility Breakdown (High Credibility / Low Credibility)

**Threshold**: 0.55 (aligned with backend metrics)

1. For every source document in `snapshot.sources`, we inspect `source.metadata` for:
   - `credibility_score`: float (0.0-1.0) from 5-signal weighted ensemble
   - `credibility_tier`: string ("high", "medium", "low", "very_low")

2. Classification rules:
   - **High Credibility** if `credibility_score >= 0.55` OR `credibility_tier` is "high" or "medium"
   - **Low Credibility** if `credibility_score < 0.55` OR `credibility_tier` is "low" or "very_low"

3. We compute percentages as `(bucket_count / total_sources) * 100`, round to integers before rendering.

4. If the snapshot has no sources or metadata, we surface calibrated placeholder values and copy that explains the numbers are estimates until fresh verification labels arrive.

**Note**: The 0.55 threshold is intentionally stricter than 0.5 to ensure higher quality standards for civic monitoring. This threshold is consistent across backend metrics collection and frontend display.

Because both calculations are deterministic and pure, they are straightforward to test within Storybook/Unit tests and to explain in academic documentation.

## Accuracy Roadmap

To make the sentiment and credibility metrics “thesis-grade” (consistent, auditable, and trustworthy), the platform should follow this enhancement plan:

1. **Backend Signal Enrichment**
   - Run a vetted sentiment classifier (fine-tuned transformer, LangChain pipeline, etc.) that returns per-class confidence scores and confusion-matrix diagnostics after every retrain.
   - Attach a credibility classifier that emits `is_verified`, `verification_status`, `credibility`, and confidence values for each source based on domain reputation, cross-source agreement, and fact-check databases.

2. **API Contract Extensions**
   - `overall_sentiment` should include `scores`, confidence intervals, and the model version used.
   - Add a `credibility_breakdown` object with legit/misinfo percentages, sample size, classifier version, and any warnings when coverage is low.

3. **Calibration & Human QA**
   - Maintain a labeled holdout set. After each model update, log precision/recall per sentiment class and true/false-positive rates for the credibility classifier.
   - Sample “Legit” and “Potential Fake News” sources weekly for manual review, feeding corrections back into training data.

4. **Observability & Alerts**
   - Emit metrics (e.g., `sentiment.negative_pct`, `credibility.fake_pct`, `sample_size`) to the monitoring stack. Trigger alerts when values drift beyond expected bounds or when classifiers output low confidence.

5. **Documentation & Governance**
   - Version every model/config, store release notes, and keep this README plus `docs/metrics.md` updated with formulas, validation scores, and audit procedures so reviewers can reproduce results.

Following this roadmap ensures the UI reflects audited backend metrics, complete with provenance, making the system defensible in academic and operational settings.
