# Empirical Study Protocol for Hinaing Framework

**Date**: February 5, 2026  
**Purpose**: Evaluate Hinaing on three panel-recommended metrics

---

## Evaluation Metrics

### 1. Contextual Faithfulness
**Definition**: How accurately system outputs reflect actual social media sources

**Sub-metrics**:
- Hallucination rate (% claims not in sources)
- Sentiment accuracy (% correct classifications)
- Source attribution rate (% insights with valid sources)

### 2. Thematic Actionability
**Definition**: How useful generated insights are for civic decision-making

**Sub-metrics**:
- Specificity score (has locations/timeframes)
- Recommendation quality (has concrete actions)
- Stakeholder identification (identifies responsible parties)

### 3. Agentic Verification Rate
**Definition**: How effectively multi-agent system verifies claims

**Sub-metrics**:
- Verification rate (% claims verified by 3+ signals)
- Precision (of verified claims, % actually true)
- Recall (of true claims, % system verified)
- F1-score (harmonic mean)

### 4. Temporal Awareness Impact ⭐ (YOUR KEY INNOVATION)
**Definition**: How much temporal-aware context engineering improves query coverage and retrieval

**Sub-metrics**:
- Query coverage gain (% more temporal keywords covered)
- Retrieval quality gain (F1 improvement)
- Seasonal issue detection rate (% seasonal issues found)
- Additional queries generated (count)

---

## Study Design

### Dataset

**Size**: 100 civic issues from Baguio social media

**Distribution**:
- 20 issues per focus area:
  - Infrastructure (traffic, roads, utilities)
  - Health (hospitals, clinics, public health)
  - Safety (crime, disasters, emergencies)
  - Tourism (attractions, festivals, complaints)
  - Economy (businesses, employment, prices)
  - Environment (pollution, climate, conservation)

**Time Coverage**:
- 40 issues from festival periods (Panagbenga, Christmas, Undas)
- 30 issues from rainy season (typhoons, floods)
- 30 issues from regular periods

**Source Mix**:
- 50 from Reddit (r/Baguio, r/Philippines)
- 50 from Facebook (Baguio community groups)

---

## Ground Truth Creation

### Annotation Team

**3 Expert Annotators**:
1. Baguio city official (infrastructure/planning)
2. Local journalist (fact-checking)
3. Community leader (civic engagement)

### Annotation Tasks

For each of 100 issues, annotators label:

1. **True Sentiment**: positive / negative / neutral
2. **True Themes**: List of applicable themes
3. **Verified Facts**: Claims that can be fact-checked
4. **Unverified Opinions**: Subjective statements
5. **Actionable Recommendations**: What should be done
6. **Source Documents**: Original social media posts

### Inter-Annotator Agreement

- Calculate Cohen's Kappa for sentiment
- Calculate Fleiss' Kappa for themes
- Resolve disagreements through discussion
- Target: Kappa > 0.7 (substantial agreement)

---

## System Configurations

### Configuration 1: Full System (Hinaing)
- All 18 agents active
- 5-signal credibility verification
- Self-learning RAG enabled
- Temporal-aware context engineering

### Configuration 2: No RAG
- Disable Node 3 (memory recall)
- Disable Node 5 (memory consolidation)
- Everything else same

### Configuration 3: No Credibility
- Disable 5-signal credibility framework
- Accept all claims without verification
- Everything else same

### Configuration 4: No Temporal Awareness ⭐ (CRITICAL ABLATION)
- Disable `expand_contextual_queries` tool
- Only use static EMERGING_CONCERNS
- No seasonal pattern generation
- Everything else same

**This tests YOUR KEY INNOVATION #1**: Temporal-aware context engineering

### Configuration 5: Sub-Agent Ablations ⭐ (CRITICAL ABLATION)
Test each of the 5 credibility sub-agents individually:

**5a. No Domain Agent**
- Remove DomainTrustAgent from CredibilityAgent
- Other 4 agents active
- Reweight remaining agents proportionally

**5b. No CrossRef Agent**
- Remove CrossReferenceAgent from CredibilityAgent
- Other 4 agents active
- Reweight remaining agents proportionally

**5c. No FactCheck Agent**
- Remove FactCheckAgent from CredibilityAgent
- Other 4 agents active
- Reweight remaining agents proportionally

**5d. No LLM Agent**
- Remove LLMAnalysisAgent from CredibilityAgent
- Other 4 agents active
- Reweight remaining agents proportionally

**5e. No Tavily Agent**
- Remove TavilyAgent from CredibilityAgent
- Other 4 agents active
- Reweight remaining agents proportionally

**This tests YOUR KEY INNOVATION #2**: Hierarchical sub-agent spawning

### Configuration 6: No Theme Agents
- Disable 6 theme sub-agents
- Only use core 7 agents
- Everything else same

### Baseline 1: Simple LLM
- Single GPT-4 call with basic prompt
- No agents, no RAG, no verification

### Baseline 2: Manual Analysis
- Human analyst (1 person)
- Manual sentiment analysis and theme identification
- Measure time taken

---

## Evaluation Protocol

### Phase 1: Data Collection (Week 1)

**Day 1-2**: Scrape social media
```bash
# Collect Reddit posts
python backend/scripts/collect_reddit_data.py --subreddit Baguio --limit 50

# Collect Facebook posts (manual or API)
# Save to: data/raw_social_media.json
```

**Day 3-5**: Create ground truth
- Distribute 100 issues to 3 annotators
- Each annotator labels all 100 issues
- Calculate inter-annotator agreement

**Day 6-7**: Resolve disagreements
- Annotators discuss conflicting labels
- Create final ground truth dataset
- Save to: `data/ground_truth.json`

### Phase 2: System Runs (Week 2)

**Day 1-2**: Run all configurations
```bash
# Full system
python backend/scripts/run_evaluation.py --config full --input data/ground_truth.json --output results/full_system.json

# Ablations
python backend/scripts/run_evaluation.py --config no_rag --input data/ground_truth.json --output results/no_rag.json
python backend/scripts/run_evaluation.py --config no_credibility --input data/ground_truth.json --output results/no_credibility.json
python backend/scripts/run_evaluation.py --config no_temporal --input data/ground_truth.json --output results/no_temporal.json

# Sub-agent ablations (test each agent's contribution)
python backend/scripts/run_evaluation.py --config no_domain_agent --input data/ground_truth.json --output results/no_domain_agent.json
python backend/scripts/run_evaluation.py --config no_crossref_agent --input data/ground_truth.json --output results/no_crossref_agent.json
python backend/scripts/run_evaluation.py --config no_factcheck_agent --input data/ground_truth.json --output results/no_factcheck_agent.json
python backend/scripts/run_evaluation.py --config no_llm_agent --input data/ground_truth.json --output results/no_llm_agent.json
python backend/scripts/run_evaluation.py --config no_tavily_agent --input data/ground_truth.json --output results/no_tavily_agent.json

python backend/scripts/run_evaluation.py --config no_themes --input data/ground_truth.json --output results/no_themes.json

# Baselines
python backend/scripts/run_evaluation.py --config simple_llm --input data/ground_truth.json --output results/simple_llm.json
```

**Day 3-4**: Log all metrics
- Automatically calculate faithfulness, actionability, verification
- Save detailed logs for analysis

**Day 5-7**: Quality check
- Manually review sample outputs
- Verify metric calculations
- Fix any issues

### Phase 3: Human Evaluation (Week 3-4)

**Week 3**: Contextual Faithfulness
- 3 annotators rate all outputs (100 × 7 configs = 700 ratings)
- Rate on 1-5 scale
- Calculate inter-rater reliability

**Week 4**: Thematic Actionability
- Recruit 5-10 Baguio city officials
- Show them insights (blind to system)
- Rate actionability on 1-5 scale
- Collect qualitative feedback

### Phase 4: Analysis (Week 5)

**Day 1-2**: Calculate metrics
```bash
python backend/scripts/evaluate_empirical_metrics.py --ground_truth data/ground_truth.json --system_outputs results/ --output analysis/metrics.json
```

**Day 3-4**: Statistical tests
- T-tests: Compare full system vs ablations
- ANOVA: Compare all configurations
- Effect sizes: Cohen's d
- Confidence intervals: 95% CI

**Day 5-7**: Visualizations
- Bar charts: Metric comparisons
- Heatmaps: Confusion matrices
- Line plots: Performance by focus area
- Box plots: Distribution of scores

---

## Expected Results

### Hypothesis 1: Contextual Faithfulness

**H1**: Full system achieves >85% faithfulness

| Configuration | Expected Faithfulness | Hallucination Rate |
|--------------|----------------------|-------------------|
| Full System | 85-95% | <10% |
| No RAG | 70-80% | 15-20% |
| No Credibility | 75-85% | 10-15% |
| Simple LLM | 60-70% | 20-30% |

### Hypothesis 2: Thematic Actionability

**H2**: Full system achieves >75% actionability

| Configuration | Expected Actionability | Specificity |
|--------------|----------------------|-------------|
| Full System | 75-85% | 80-90% |
| No Temporal | 65-75% | 70-80% |
| No Theme Agents | 60-70% | 75-85% |
| Simple LLM | 50-60% | 60-70% |

### Hypothesis 3: Agentic Verification Rate

**H3**: Full system achieves >80% verification with >85% precision

| Configuration | Verification Rate | Precision | Recall | F1 |
|--------------|------------------|-----------|--------|-----|
| Full System (5 signals) | 80-90% | 85-95% | 80-90% | 82-92% |
| No Credibility | 100% | 60-70% | 100% | 75-82% |
| Single Signal | 60-70% | 70-80% | 60-70% | 65-75% |
| Simple LLM | 50-60% | 65-75% | 50-60% | 57-67% |

---

## Statistical Analysis

### Significance Tests

**T-tests** (paired, two-tailed):
- Full system vs No RAG
- Full system vs No Credibility
- Full system vs No Temporal
- Full system vs Simple LLM

**ANOVA** (one-way):
- Compare all 7 configurations
- Post-hoc: Tukey HSD test

**Significance level**: α = 0.05

### Effect Sizes

**Cohen's d**:
- Small: d = 0.2
- Medium: d = 0.5
- Large: d = 0.8

**Expected effect sizes**:
- Full vs No RAG: d = 0.8 (large)
- Full vs No Credibility: d = 0.6 (medium)
- Full vs Simple LLM: d = 1.2 (very large)

---

## Deliverables

### 1. Dataset
- `data/ground_truth.json` - 100 annotated issues
- `data/raw_social_media.json` - Original posts
- `data/annotation_guidelines.pdf` - For annotators

### 2. Results
- `results/full_system.json` - Full system outputs
- `results/ablations/` - All ablation outputs
- `results/baselines/` - Baseline outputs

### 3. Analysis
- `analysis/metrics.json` - All calculated metrics
- `analysis/statistical_tests.json` - T-tests, ANOVA results
- `analysis/visualizations/` - All charts and plots

### 4. Documentation
- `docs/EMPIRICAL_STUDY_RESULTS.md` - Complete results
- `docs/STATISTICAL_ANALYSIS.md` - Detailed statistics
- `docs/QUALITATIVE_FEEDBACK.md` - Expert comments

---

## Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| Week 1 | Data collection, ground truth creation | `ground_truth.json` |
| Week 2 | System runs, ablations, baselines | All system outputs |
| Week 3 | Human evaluation (faithfulness) | Faithfulness ratings |
| Week 4 | Human evaluation (actionability) | Actionability ratings |
| Week 5 | Statistical analysis, visualizations | Complete results |

**Total Duration**: 5 weeks

---

## Budget

### Human Resources
- 3 annotators × 20 hours × $20/hour = $1,200
- 5 expert evaluators × 5 hours × $50/hour = $1,250
- **Total**: $2,450

### Compute Resources
- API costs (Gemini, Groq): ~$100
- Server costs: ~$50
- **Total**: $150

### Grand Total: $2,600

---

## Ethical Considerations

### Data Privacy
- Anonymize all social media posts
- Remove personally identifiable information
- Comply with platform terms of service

### Informed Consent
- Obtain consent from expert evaluators
- Explain study purpose and data usage
- Allow withdrawal at any time

### Bias Mitigation
- Diverse annotator backgrounds
- Blind evaluation (evaluators don't know system)
- Multiple annotators for reliability

---

## Success Criteria

**Study is successful if**:
1. ✅ Full system achieves >85% contextual faithfulness
2. ✅ Full system achieves >75% thematic actionability
3. ✅ Full system achieves >80% agentic verification rate
4. ✅ Full system significantly outperforms all ablations (p < 0.05)
5. ✅ Full system significantly outperforms baselines (p < 0.01)

**Thesis defense is strong if**:
- All 5 success criteria met
- Effect sizes are large (d > 0.8)
- Expert evaluators provide positive qualitative feedback
- Results are reproducible

---

**Last Updated**: February 5, 2026  
**Status**: Ready to execute  
**Next Steps**: Begin data collection (Week 1)

