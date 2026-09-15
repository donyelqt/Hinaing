"""Audit the faithfulness metrics recorded in backend/data/metrics/*.jsonl.

Reproduces the aggregate claim counts, verification rate, hallucination count,
and the verification-on/off split from the persisted metrics files. No external
dependencies beyond the Python standard library.

Usage:
    cd backend
    poetry run python scripts/audit_faithfulness_metrics.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Resolve the metrics directory relative to this script's location so the
# audit works regardless of the caller's working directory.
METRICS_DIR = (
    Path(__file__).resolve().parent.parent / "data" / "metrics"
)


def _iter_metric_records(metrics_dir: Path):
    """Yield parsed JSON objects from every metrics_*.jsonl file, oldest first."""
    if not metrics_dir.is_dir():
        raise SystemExit(
            f"Metrics directory not found: {metrics_dir}\n"
            "Run this script from the backend/ directory."
        )
    for path in sorted(metrics_dir.glob("metrics_*.jsonl")):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield path.name, json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"WARN: skipping unparseable line in {path.name}: {exc}")


def main() -> int:
    total_runs = 0
    total_claims = 0
    total_verified = 0
    total_hallucinations = 0
    runs_with_claims = 0
    runs_without_claims = 0
    faithfulness_scores: Counter[float] = Counter()
    file_claims: dict[str, int] = {}
    file_verified: dict[str, int] = {}
    file_halluc: dict[str, int] = {}

    for filename, record in _iter_metric_records(METRICS_DIR):
        total_runs += 1
        claims = record.get("faithfulness_total_claims", 0) or 0
        verified = record.get("faithfulness_verified_claims", 0) or 0
        hallucinations = (
            (record.get("hallucination_analysis") or {}).get("hallucination_count", 0)
            or 0
        )
        score = record.get("faithfulness_score")

        if claims > 0:
            runs_with_claims += 1
        else:
            runs_without_claims += 1

        total_claims += claims
        total_verified += verified
        total_hallucinations += hallucinations
        if score is not None:
            faithfulness_scores[score] += 1

        # Track per-file aggregates only for files that actually ran verification.
            file_claims[filename] = file_claims.get(filename, 0) + claims
            file_verified[filename] = file_verified.get(filename, 0) + verified
            file_halluc[filename] = file_halluc.get(filename, 0) + hallucinations
    print("=" * 72)
    print("FAITHFULNESS METRICS AUDIT")
    print(f"Metrics directory: {METRICS_DIR}")
    print("=" * 72)
    print(f"Total runs recorded:        {total_runs}")
    print(f"Runs with verification on:  {runs_with_claims}")
    print(f"Runs with verification off: {runs_without_claims}")
    print(f"Total claims extracted:     {total_claims}")
    print(f"Total claims verified:      {total_verified}")
    print(f"Total hallucinations:       {total_hallucinations}")
    rate = (total_verified / total_claims) if total_claims else 0.0
    print(f"Faithfulness rate:          {rate:.4f}")
    print()
    print("faithfulness_score distribution across all runs:")
    for score, count in sorted(faithfulness_scores.items()):
        print(f"  {score:>5}: {count} run(s)")
    print()
    enabled = {f: c for f, c in file_claims.items() if c > 0}
    if enabled:
        print("Per-file claim aggregates (verification-enabled runs only):")
        print(f"  {'file':<28} {'claims':>7} {'verified':>9} {'halluc':>6}")
        for filename in sorted(enabled):
            print(
                f"  {filename:<28} {enabled[filename]:>7} "
                f"{file_verified[filename]:>9} {file_halluc[filename]:>6}"
            )
    print("=" * 72)

    # Exit non-zero if the audit could not find any data at all.
    return 0 if total_runs else 1


if __name__ == "__main__":
    sys.exit(main())