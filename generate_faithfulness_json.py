#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, 'backend')
from scripts.faithfulness.faithfulness_analytics import (
    load_all_runs,
    filter_faithfulness_runs,
    section_aggregate_stats,
    section_confidence_intervals
)

metrics_dir = Path("backend/backend/data/metrics")
all_runs = load_all_runs(metrics_dir)
runs = [r for r in filter_faithfulness_runs(all_runs) if r["timestamp"] > "2026-03-20"]

stats = section_aggregate_stats(runs)
ci = section_confidence_intervals(runs)

result = {
    "generated_at": __import__("datetime").datetime.now().isoformat(),
    "total_runs": len(runs),
    "aggregate": stats,
    "confidence_intervals": ci
}

output_path = "backend/backend/data/metrics/faithfulness_analytics_stabilized.json"
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)

print(f"Generated: {output_path}")
print(f"Total runs: {len(runs)}")
print(f"Total claims: {stats['total_claims_verified']}")
print(f"Faithfulness rate: {stats['overall_faithfulness_rate']}")
print(f"Citation accuracy mean: {stats['citation_accuracy_rate']['mean']}")
print(f"Citation accuracy median: {stats['citation_accuracy_rate']['median']}")
print(f"Total hallucinations: {stats['hallucination_totals']['total_hallucinations']}")
