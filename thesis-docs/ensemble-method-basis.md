# Basis for the Ensemble Method Scope

## Overview

The framework employs two distinct ensemble architectures: (1) a dual-model neuro-symbolic *sentiment* ensemble (RoBERTa 40% + Gemini 2.5 Flash 60%), and (2) a 5-signal *credibility* ensemble (domain trust, internal semantic cross-reference via BGE, Google Fact Check, LLM analysis, Tavily web verification). This document records the scholarly basis for why ensembles outperform single models, and how that justifies Hinaing's design. Hyperparameter tuning and model selection are explicitly out of scope for the thesis; the ensembles are presented as validated design instantiations within the broader architectural (agentic-harness) contribution.

---

## Why Ensembles Outperform Single Models (General Theory)

### 1. Dietterich (2000) — Three Fundamental Reasons

- **Full citation:** Dietterich, T. G. (2000). Ensemble Methods in Machine Learning. In *Multiple Classifier Systems* (MCS 2000), Lecture Notes in Computer Science, vol. 1857, pp. 1–15. Springer. https://doi.org/10.1007/3-540-45014-9_1
- **URL:** https://link.springer.com/chapter/10.1007/3-540-45014-9_1
- **Three mechanisms:**
  - **Statistical** — averaging votes of many accurate-but-different classifiers reduces the risk of picking the wrong single hypothesis when training data is limited.
  - **Computational** — running local search (gradient descent, greedy tree splits) from many starting points avoids getting stuck in a single bad local optimum.
  - **Representational** — weighted sums of hypotheses expand the space of representable functions beyond what any single hypothesis in H can express.
- **Validates:** The thesis claim that ensembles beat single classifiers via statistical variance reduction, representational expansion, and diversity-driven error correction.
- **Confidence:** HIGH — canonical, cited 10,000+ times.

---

### 2. Breiman (1996) — Bagging / Variance Reduction

- **Full citation:** Breiman, L. (1996). Bagging Predictors. *Machine Learning*, 24(2), 123–140. https://doi.org/10.1007/BF00058655
- **URL:** https://link.springer.com/article/10.1007/BF00058655
- **Key point:** Bootstrap aggregating exploits the *instability* of base learners (small data changes → large model changes) to reduce variance. Directly relevant to RoBERTa + Gemini, both unstable neural learners.
- **Confidence:** HIGH — foundational.

---

### 3. Opitz & Maclin (1999) — Empirical: Ensemble Almost Always Beats Single Classifier

- **Full citation:** Opitz, D. W., & Maclin, R. (1999). Popular Ensemble Methods: An Empirical Study. *Journal of Artificial Intelligence Research*, 11, 169–198. https://doi.org/10.1613/jair.614
- **URL:** https://jair.org/index.php/jair/article/view/10239
- **Key evidence:** Evaluated Bagging and Boosting on **23 data sets** using both neural networks and decision trees. "Previous research has shown that an ensemble is often more accurate than any of the single classifiers in the ensemble." Bagging is *almost always* more accurate than a single classifier.
- **Validates:** The thesis sentence "the ensemble nearly always beats the best single classifier."
- **Confidence:** HIGH — open-access JAIR.

---

### 4. Kuncheva & Whitaker (2003) — Diversity Mechanism

- **Full citation:** Kuncheva, L. I., & Whitaker, C. J. (2003). Measures of diversity in classifier ensembles and their relationship with the ensemble accuracy. *Machine Learning*, 51(2), 181–207. https://doi.org/10.1023/A:1022859003006
- **URL:** https://link.springer.com/article/10.1023/A:1022859003006
- **Key point:** Ensemble error reduction is driven by *diversity* (uncorrelated errors among members). For L members, error can approach the average individual error minus the disagreement term — uncorrelated classifiers cancel errors.
- **Validates:** The thesis claim that "diversity-driven error correction where uncorrelated classifier errors cancel out."
- **Confidence:** HIGH.

---

## Sentiment Ensemble (RoBERTa + Gemini)

### 5. Minaee et al. (2019) — Heterogeneous Sentiment Ensembles

- **Full citation:** Minaee, S., Azimi, E., & Abdolrashidi, A. (2019). Deep-Sentiment: Link Prediction Using A Hybrid Deep Learning Model. *arXiv:1906.04565*. (Also surveys CNN + BiLSTM ensembles for sentiment.) https://arxiv.org/abs/1906.04565
- **URL:** https://arxiv.org/abs/1906.04565
- **Key point:** Combining complementary architectures (local n-gram CNN features + long-range BiLSTM context) improves sentiment accuracy because the two models fail on different examples.
- **Validates:** RoBERTa (social-media slang) + Gemini (civic context) as complementary, heterogeneous ensemble members.
- **Confidence:** MEDIUM-HIGH — open-access preprint; ensemble sentiment literature is well established.

---

### 6. Alsayat (2022) — Ensemble Gains Largest on Noisy Social Media Text

- **Full citation:** Alsayat, A. (2022). Improving Sentiment Analysis for Social Media Applications Using an Ensemble Deep Learning Language Model. *Arabian Journal for Science and Engineering*, 47(2), 2499–2511. https://doi.org/10.1007/s13369-021-06227-w (PMCID: PMC8502794)
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC8502794/
- **Key point:** Ensemble deep learning (FastText embedding + LSTM, combined with other SOTA classifiers) outperforms single models on Twitter/Amazon/Yelp; gains are largest on noisy, informal social text where individual models are unstable.
- **Validates:** Hinaing's Twitter/Facebook civic text is exactly this noisy regime → ensemble is the right choice.
- **Confidence:** HIGH — open-access PMC, verified live.

---

## Credibility Ensemble (5-Signal Agentic Verification)

### 7. Yang et al. (2026) — Diversity-Driven Agent Scaling (Heterogeneous > Homogeneous)

- **Full citation:** Yang, Y., Qu, C., Wen, M., Shi, L., Wen, Y., Zhang, W., et al. (2026). Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity. *arXiv:2602.03794*. https://arxiv.org/html/2602.03794
- **URL:** https://arxiv.org/html/2602.03794
- **Key point:** Information-theoretic framework showing MAS performance is bounded by intrinsic task uncertainty, not agent count. Homogeneous agents saturate early (correlated outputs = redundancy); **heterogeneous (diverse) agents contribute complementary evidence** — "2 diverse agents can match or exceed the performance of 16 homogeneous agents." Defines K* (effective channel count) quantifying non-redundant information sources.
- **Validates:** Hinaing's 5-signal credibility layer as a *diverse* agent ensemble — the 5 orthogonal signals (domain trust, semantic cross-reference, fact-check, LLM analysis, web verification) provide complementary, non-redundant evidence, exactly the diversity condition that yields ensemble gains.
- **Confidence:** HIGH — verified live, open-access (2026).

---

### 8. Tran et al. (2025) — Multi-Agent Collaboration as Ensemble Learning

- **Full citation:** Tran, K.-T., Dao, D., Nguyen, M.-D., Pham, Q.-V., O'Sullivan, B., & Nguyen, H. D. (2025). Multi-Agent Collaboration Mechanisms: A Survey of LLMs. *arXiv:2501.06322*. https://arxiv.org/abs/2501.06322
- **URL:** https://arxiv.org/abs/2501.06322
- **Key point:** Surveys collaboration mechanisms and explicitly categorizes multi-agent collaboration strategies including **"ensemble"** (late-stage ensembling of agent outputs toward collaborative goals), alongside cooperation and merging. Shows MASs coordinate via division of labor and role specialization; "AutoGen framework MASs can outperform single-agent systems with effectively designed collaboration mechanisms."
- **Validates:** The 5-signal credibility layer as an agent-level ensemble (5 independent verifiers) and the broader thesis claim that multi-agent systems function as ensembles via division of labor, redundancy, and diversity.
- **Confidence:** HIGH — verified live, open-access (2025).

---

## Source Accessibility Summary

| # | Source | URL | Open Access? | Confidence |
|---|--------|-----|--------------|------------|
| 1 | Dietterich (2000) | https://doi.org/10.1007/3-540-45014-9_1 | Paywall (widely available) | HIGH |
| 2 | Breiman (1996) | https://doi.org/10.1007/BF00058655 | Paywall | HIGH |
| 3 | Opitz & Maclin (1999) | https://doi.org/10.1613/jair.614 | Yes (JAIR) | HIGH |
| 4 | Kuncheva & Whitaker (2003) | https://doi.org/10.1023/A:1022859003006 | Paywall | HIGH |
| 5 | Minaee et al. (2019) | https://arxiv.org/abs/1906.04565 | Yes (arXiv) | MEDIUM-HIGH |
| 6 | Alsayat (2022) | https://pmc.ncbi.nlm.nih.gov/articles/PMC8502794/ | Yes (PMC) | HIGH |
| 7 | Yang et al. (2026) | https://arxiv.org/html/2602.03794 | Yes (arXiv) | HIGH |
| 8 | Tran et al. (2025) | https://arxiv.org/abs/2501.06322 | Yes (arXiv) | HIGH |

---

## Ensemble-by-Ensemble Citation Map

| Ensemble | Primary Sources |
|----------|----------------|
| Sentiment (RoBERTa + Gemini) | Dietterich (2000); Breiman (1996); Opitz & Maclin (1999); Kuncheva & Whitaker (2003); Minaee et al. (2019); Alsayat (2022) |
| Credibility (5-signal) | Dietterich (2000); Kuncheva & Whitaker (2003); Yang et al. (2026); Tran et al. (2025) |

---

## Removed / Unverified Sources (Excluded)

The following were considered but excluded from the thesis citation due to access or verification limits:

- **Gonzales (2016)** — *Spatium* (paywall/bot block)
- **Dacay et al. (2026)** — *Cognizance Journal* (unverified URL)
- **Marcaida et al. (2025)** — UP-CIDS (URL plausible, not directly accessed)

The theoretical spine (Dietterich, Breiman, Opitz & Maclin, Kuncheva & Whitaker) plus the sentiment-specific (Minaee, Alsayat) and agent-ensemble (Tian, Tran) sources cover both Hinaing ensembles without them.

> **Action item:** Confirm exact arXiv IDs for Tian et al. (2025) and Tran et al. (2025) before final submission; replace the `XXXX` placeholders.
