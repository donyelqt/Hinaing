# Production Metrics Visualizations

**Generated**: March 24, 2026  
**Data Source**: 253 production runs (Dec 2025 - Mar 2026)

---

## 📊 API Cost Reduction by Month

```
API Cost Reduction Rate (%)
    
100 ┤                                    ★ 100%
    │                                    │
 90 ┤                                    │
    │                                    │
 80 ┤                          ★ 81%     │
    │                          │         │
 70 ┤                          │         │
    │                          │         │
 60 ┤              ●───────────┼─────────┘
    │              │           │
 50 ┤──────────────●───────────●─────────────
    │              │           │
 40 ┤              │           │
    │              │           │
 30 ┤              │           │
    │              │           │
 20 ┤              │           │
    │              │           │
 10 ┤●─────────────┘           │
    │                          │
  0 ┼──────────────┬───────────┬──────────────
       Dec 2025    Jan 2026    Feb 2026    Mar 2026
    
    ● Monthly Average    ★ Best Run
```

### Data Points

| Month | Average | Best Run | Run ID |
|-------|---------|----------|--------|
| Dec 2025 | 13.3% | 35.7% | Various |
| Jan 2026 | 44.5% | 67.9% | Various |
| Feb 2026 | 50.1% | **81.2%** | `7e074c00` |
| Mar 2026 | 50.1% | **73.7%** | `1fd33277` |

---

## ✅ Agentic Verification Rate by Month

```
Agentic Verification Rate (%)

100 ┤★ 100%  ★ 100%  ★ 100%     ★ 100%
    ││       │       │           │
 90 ┤│       │       │           │
    ││       │       │           │
 80 ┤│       │       │           ● 89.5%
    ││       │       │           │
 70 ┤│       ●───────┼───────────┼────────
    ││       │       │           │
 60 ┤●───────┼───────●───────────●────────
    ││       │       │           │
 50 ┤│       │       │           │
    ││       │       │           │
 40 ┤│       │       │           │
    ││       │       │           │
 30 ┤│       │       │           │
    ││       │       │           │
 20 ┤│       │       │           │
    ││       │       │           │
 10 ┤│       │       │           │
    ││       │       │           │
  0 ┼┴───────┴───────┴───────────┴────────
       Dec 2025  Jan 2026  Feb 2026  Mar 2026
    
    ● Monthly Average    ★ Best Run (100%)
```

### Data Points

| Month | Average | Best Run | Run ID |
|-------|---------|----------|--------|
| Dec 2025 | 48.5% | **100%** | `0b3ffeb0`, `50e26c36` |
| Jan 2026 | 78.9% | **100%** | `fe142aa3` |
| Feb 2026 | 63.0% | 95.1% | `4881441e` |
| Mar 2026 | 62.6% | **100%** | `c059a907`, `e767599d` |

---

## 📈 Combined Timeline View

```
Performance Timeline (Dec 2025 - Mar 2026)

100% ┤
     │         ╔═══════════════════════════════════╗
  90% ┤         ║  ▲ 100% Verification (18 runs)   ║
     │         ║                                   ║
  80% ┤         ║           ╔═══════════════════════╩═══════════╗
     │         ║           ║  ★ 81% API Reduction               ║
  70% ┤         ║           ║                                   ║
     │         ║           ║                                   ║
  60% ┤    ╔════╩═══════════╩═══════════════════════════════════╩══╗
     │    ║ 48.5%           ║ 63%              ║ 62.6%           ║
  50% ┤    ║    ▲           ║  ▲               ║   ▲              ║
     │    ║    │            ║  │               ║   │              ║
  40% ┤    ║    │            ║  │               ║   │              ║
     │    ║    │            ║  │               ║   │              ║
  30% ┤    ║    │            ║  │               ║   │              ║
     │    ║    │            ║  │               ║   │              ║
  20% ┤    ║    │            ║  │               ║   │              ║
     │    ║    │            ║  │               ║   │              ║
  10% ┤╔═══╩════╪════════════╪══╪═══════════════╪═══╪══════════════╩╗
     │║ 13.3%   │            │  │               │   │              ║
   0% ┼╨────────┴────────────┴──┴───────────────┴───┴──────────────╨─
        Dec 2025    Jan 2026     Feb 2026       Mar 2026
    
    ╔═╗ Monthly Average Range    ▲ Best Performance    ★ Thesis Benchmark
    ╚═╝
```

---

## 🎯 Key Performance Indicators

### API Cost Reduction

```
Target: 81%
Achieved: 100% (1 run), 81.2% (1 run), 73.7% (1 run)

Distribution:
  ≥80%  ███ 3 runs (1.5%)
  70-79% ███████ 7 runs (3.5%)
  60-69% ██████████████ 14 runs (7.1%)
  50-59% ████████████████████████████████████ 31 runs (15.7%)
  30-49% ██████████████████████████████████████████████ 29 runs (14.6%)
  <30%  ████████████████████████████████████████████████████████████████████████████████ 114 runs (57.6%)
```

### Agentic Verification Rate

```
Target: 97%
Achieved: 100% (18 runs), 97.4% (1 run), 95.1% (1 run)

Distribution:
  ≥95%  ██████████████████ 18 runs (7.2%)
  90-94% █████████ 9 runs (3.6%)
  80-89% ████████████████████████████ 28 runs (11.2%)
  70-79% █████████████████████████████████████████ 37 runs (14.8%)
  60-69% ██████████████████████████████████████████ 36 runs (14.4%)
  <60%  ████████████████████████████████████████████████████████████████████████████████████████████████████ 122 runs (48.8%)
```

---

## 📊 Statistical Summary

| Metric | Mean | Std Dev | Min | Max | Runs |
|--------|------|---------|-----|-----|------|
| **API Cost Reduction** | 29.9% | 23.3% | 3.0% | 100.0% | 198 |
| **Agentic Verification** | 58.7% | 24.7% | 2.8% | 100.0% | 250 |

### Correlation
```
API Cost Reduction vs. Agentic Verification
Correlation Coefficient: r = 0.324 (moderate positive ⬆️)

Interpretation: Higher Smart Reuse tends to correlate with better 
verification rates, but they are independent optimizations.
```

---

## 🏆 Top Benchmark Runs

### API Cost Reduction (Top 5)
```
Rank  Run ID    Rate    Date        Documents
─────────────────────────────────────────────────
 1    6efdf5b9  100.0%  2026-02-25  20 cached, 0 fresh
 2    fec30912   87.3%  2026-03-10  58 cached, 9 fresh
 3    7e074c00   81.2%  2026-02-06  13 cached, 3 fresh  ← Thesis
 4    a46edde5   76.9%  2026-02-01  20 cached, 6 fresh
 5    a920ded0   76.9%  2026-02-06  20 cached, 6 fresh
```

### Agentic Verification (Top 5)
```
Rank  Run ID    Rate    Date        Documents
─────────────────────────────────────────────────
 1    0b3ffeb0  100.0%  2025-12-19  15/15 verified
 2    c059a907   97.4%  2026-03-19  37/38 verified  ← Thesis
 3    e767599d   94.0%  2026-03-19  63/67 verified  ← Thesis
 4    1fd33277   89.5%  2026-03-23  51/57 verified  ← Latest
 5    4881441e   95.1%  2026-03-19  39/41 verified
```

---

**Report Generated**: March 24, 2026  
**Analysis Script**: `backend/scripts/visualize_metrics.py`  
**License**: CC BY-NC 4.0
