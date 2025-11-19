# Backend Insights Workflow

This backend powers the sentiment snapshot generator. The LangGraph pipeline in `app/services/insights/graph.py` orchestrates data collection, scoring, and summarization. To keep the frontend metrics “thesis-grade,” we plan to extend the backend in the following ways:

## 1. Sentiment Model Upgrade

1. **Model choice**: integrate a fine-tuned transformer or trusted API that supports English + Filipino social posts. Expose per-class confidence.
2. **Training loop**: maintain a labeled validation set. After every retrain, log precision/recall per sentiment class and persist the confusion matrix.
3. **API response**: add `confidence` and `model_version` fields under `overall_sentiment` so clients know which scorer produced each snapshot.

### Additional Sentiment Classifier Notes

- Keep the LangChain/LangGraph workflow but swap in the fine-tuned model so the current orchestrator continues to work.
- Maintain a labeled validation set dedicated to thesis evaluation. After every update, compute precision/recall per class and store the confusion matrix artifact beside the model weights.
- Include the model version plus confusion-matrix metadata inside `/insights/snapshot` so downstream clients can cite the provenance of every sentiment score.

## 2. Credibility Classification

1. **Metadata enrichment**: for each source, attach `is_verified`, `verification_status`, `credibility`, and a numeric confidence. Signals come from domain reputation lists, author verification, lexical cues, and cross-source agreement.
2. **Breakdown calculation**: compute `credibility_breakdown = { legit_percent, misinfo_percent, sample_size, classifier_version }` server-side instead of letting the UI infer it.
3. **Human QA**: sample “Legit” vs “Potential Fake News” items weekly for reviewers and feed corrections back into the training set to prevent drift.

### Additional Credibility Classifier Notes

- Train or integrate a model that outputs the three metadata fields per source (`is_verified`, `verification_status`, `credibility`).
- Feature set should include domain reputation lists, author verification signals, lexical cues, and cross-source agreement checks.
- Maintain a labeled calibration set and store accuracy metrics per release so you can demonstrate improvements over time.

## 3. Observability & Alerts

- Emit metrics like `sentiment.negative_pct`, `sentiment.sample_size`, and `credibility.fake_pct` to the monitoring stack.
- Trigger alerts when sample sizes are too small, classifier confidence drops, or percentages drift beyond historical bounds.

## 4. Documentation & Governance

- Version every model/config and keep release notes in `docs/model-log.md` (to be created) with validation scores and dataset hashes.
- Update this README whenever the workflow changes so anyone inspecting `graph.py` understands the data provenance.

Following this plan ensures the backend supplies trustworthy, auditable metrics that the frontend can surface without extra heuristics.

## Implementation Checklist (Expanded)

1. **Sentiment classifier wiring**
   - Plug the fine-tuned transformer/API into `app/services/insights/graph.py`.
   - Save model version + confusion matrix and include them in `/insights/snapshot`.
2. **Credibility classifier wiring**
   - Enrich each source with `is_verified`, `verification_status`, and `credibility` metadata during the graph run.
   - Compute `credibility_breakdown` server-side and send it to the frontend.
3. **Human QA & monitoring**
   - Schedule manual audits of sampled posts to catch drift.
   - Emit monitoring metrics (percentage of posts marked fake, average confidence, etc.) so alerts fire when behavior changes.

These steps make the stats trustworthy long-term while remaining compatible with the existing LangGraph pipeline.
