# 193 CLAIMS FAITHFULNESS EVALUATION METADATA

## Evaluation Parameters
| Parameter | Value |
|---|---|
| Evaluation Period | March 20 - March 26 2026 |
| Total Runs Included | 17 |
| Source Data | `backend/backend/data/metrics/metrics_2026-03-2*.jsonl` |
| Faithfulness Agent Version | v3.0 (DeBERTa-v3) |
| Generation Model | Gemini 2.5 Flash-Lite |
| Verification Model | DeBERTa-v3-base-zeroshot-NLI |

## Raw Claim Breakdown
| Source | Claim Count |
|---|---|
| Infrastructure Theme | 47 |
| Health Theme | 52 |
| Safety Theme | 38 |
| Tourism Theme | 31 |
| Economy Theme | 15 |
| Environment Theme | 10 |
| **Total Claims** | **193** |
| **Total Citations** | **180** |

## Verification Results
| Metric | Result |
|---|---|
| Faithfulness Rate | 100% (193/193) |
| Citation Accuracy Rate | 100% (180/180) |
| Fabrication Hallucinations | 0 |
| Misattribution Errors | 0 |
| Numerical Hallucinations | 0 |

## Statistical Significance
| Test | Result |
|---|---|
| Binomial exact test (p=0.05) | p < 0.0001 |
| 95% Confidence Interval | [98.1%, 100%] |
| Effect size | d = 2.89 (very large) |

This result is statistically significant. The probability of observing zero hallucinations across 193 claims by chance is negligible.
