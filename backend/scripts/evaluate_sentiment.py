"""
Sentiment Ensemble Evaluation Script

This script evaluates the accuracy of RoBERTa, Gemini, and the Ensemble
against human-labeled ground truth data.

Usage:
    python -m scripts.evaluate_sentiment --ground-truth data/ground_truth.csv

Output:
    - Accuracy, Precision, Recall, F1 for each model
    - Confusion matrices
    - Thesis-ready results table
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.agents.sentiment_agent import (
    EnsembleSentimentAgent,
    get_sentiment_model,
    sanitize_text,
)
from app.schemas.snapshot import WebDocument


@dataclass
class EvaluationResult:
    """Stores evaluation metrics for a model."""
    model_name: str
    accuracy: float
    precision: dict[str, float]
    recall: dict[str, float]
    f1: dict[str, float]
    confusion_matrix: dict[str, dict[str, int]]
    total_samples: int
    correct: int


def load_ground_truth(filepath: str) -> list[dict]:
    """
    Load ground truth CSV file.
    
    Expected format:
    text,human_label
    "Traffic is terrible in Session Road",negative
    "City hall meeting tomorrow",neutral
    "Festival was amazing!",positive
    """
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("text") and row.get("human_label"):
                samples.append({
                    "text": row["text"].strip(),
                    "label": row["human_label"].strip().lower(),
                })
    return samples


def calculate_metrics(
    predictions: list[str],
    ground_truth: list[str],
    labels: list[str] = ["positive", "negative", "neutral"]
) -> tuple[float, dict, dict, dict, dict]:
    """Calculate accuracy, precision, recall, F1 and confusion matrix."""
    
    # Confusion matrix
    confusion = {true: {pred: 0 for pred in labels} for true in labels}
    
    # Count predictions
    tp = {l: 0 for l in labels}  # True positives
    fp = {l: 0 for l in labels}  # False positives
    fn = {l: 0 for l in labels}  # False negatives
    
    correct = 0
    for pred, true in zip(predictions, ground_truth):
        if pred == true:
            correct += 1
            tp[pred] += 1
        else:
            fp[pred] += 1
            fn[true] += 1
        
        if true in confusion and pred in confusion[true]:
            confusion[true][pred] += 1
    
    accuracy = correct / len(predictions) if predictions else 0
    
    # Calculate per-class metrics
    precision = {}
    recall = {}
    f1 = {}
    
    for label in labels:
        p = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
        r = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
        
        precision[label] = round(p, 4)
        recall[label] = round(r, 4)
        f1[label] = round(2 * p * r / (p + r), 4) if (p + r) > 0 else 0
    
    return accuracy, precision, recall, f1, confusion


def run_evaluation(ground_truth_path: str, output_path: str | None = None):
    """
    Run full evaluation of sentiment models.
    
    Args:
        ground_truth_path: Path to ground truth CSV
        output_path: Optional path to save JSON results
    """
    print("=" * 60)
    print("SENTIMENT ENSEMBLE EVALUATION")
    print("=" * 60)
    
    # Load ground truth
    print(f"\n📂 Loading ground truth from: {ground_truth_path}")
    samples = load_ground_truth(ground_truth_path)
    print(f"   Loaded {len(samples)} samples")
    
    if not samples:
        print("❌ No samples found. Check your CSV format.")
        return
    
    # Show label distribution
    label_counts = defaultdict(int)
    for s in samples:
        label_counts[s["label"]] += 1
    print(f"   Distribution: {dict(label_counts)}")
    
    # Initialize models
    print("\n🤖 Initializing models...")
    roberta = get_sentiment_model()
    ensemble = EnsembleSentimentAgent()
    print("   ✓ RoBERTa loaded")
    print("   ✓ Ensemble (RoBERTa + Gemini) loaded")
    
    # Prepare data
    texts = [sanitize_text(s["text"])[:512] for s in samples]
    ground_truth_labels = [s["label"] for s in samples]
    
    # Run predictions
    print("\n🔄 Running predictions...")
    
    # RoBERTa predictions
    print("   → RoBERTa...")
    roberta_probs = roberta.predict_batch_with_probs(texts)
    roberta_preds = [max(p, key=p.get) for p in roberta_probs]
    
    # Create WebDocuments for ensemble
    docs = [
        WebDocument(
            url=f"https://localhost/eval/{i}",
            title=s["text"][:100],
            snippet=s["text"],
            source="evaluation",
        )
        for i, s in enumerate(samples)
    ]
    
    # Ensemble predictions (includes Gemini)
    print("   → Ensemble (RoBERTa + Gemini)...")
    enriched_docs = ensemble.analyze_batch(docs)
    
    ensemble_preds = [d.sentiment for d in enriched_docs]
    gemini_preds = [d.metadata.get("gemini_prediction", "neutral") for d in enriched_docs]
    agreement_status = [d.metadata.get("model_agreement", "unknown") for d in enriched_docs]
    
    # Calculate metrics
    print("\n📊 Calculating metrics...")
    
    results = {}
    
    # RoBERTa
    acc, prec, rec, f1, conf = calculate_metrics(roberta_preds, ground_truth_labels)
    results["roberta"] = EvaluationResult(
        model_name="RoBERTa (twitter-roberta-base-sentiment)",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
    )
    
    # Gemini
    acc, prec, rec, f1, conf = calculate_metrics(gemini_preds, ground_truth_labels)
    results["gemini"] = EvaluationResult(
        model_name="Gemini 2.5 Flash-Lite",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
    )
    
    # Ensemble
    acc, prec, rec, f1, conf = calculate_metrics(ensemble_preds, ground_truth_labels)
    results["ensemble"] = EvaluationResult(
        model_name="Ensemble (40% RoBERTa + 60% Gemini)",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
    )
    
    # Agreement analysis
    agreement_counts = defaultdict(int)
    for status in agreement_status:
        agreement_counts[status] += 1
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│                    ACCURACY COMPARISON                  │")
    print("├──────────────────────────┬──────────┬───────────────────┤")
    print("│ Model                    │ Accuracy │ Correct/Total     │")
    print("├──────────────────────────┼──────────┼───────────────────┤")
    
    for key in ["roberta", "gemini", "ensemble"]:
        r = results[key]
        print(f"│ {r.model_name[:24]:<24} │ {r.accuracy:>6.1%}  │ {r.correct:>6}/{r.total_samples:<6}     │")
    
    print("└──────────────────────────┴──────────┴───────────────────┘")
    
    # Macro F1
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│                    MACRO F1 SCORES                      │")
    print("├──────────────────────────┬──────────────────────────────┤")
    print("│ Model                    │ Positive │ Negative │ Neutral│")
    print("├──────────────────────────┼──────────┼──────────┼────────┤")
    
    for key in ["roberta", "gemini", "ensemble"]:
        r = results[key]
        print(f"│ {key.capitalize():<24} │ {r.f1.get('positive', 0):>6.2f}   │ {r.f1.get('negative', 0):>6.2f}   │ {r.f1.get('neutral', 0):>5.2f}  │")
    
    print("└──────────────────────────┴──────────┴──────────┴────────┘")
    
    # Agreement stats
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│                  MODEL AGREEMENT ANALYSIS               │")
    print("├──────────────────────────┬──────────────────────────────┤")
    
    for status, count in sorted(agreement_counts.items()):
        pct = count / len(samples) * 100
        print(f"│ {status:<24} │ {count:>6} ({pct:>5.1f}%)             │")
    
    print("└──────────────────────────┴──────────────────────────────┘")
    
    # Ensemble improvement
    roberta_acc = results["roberta"].accuracy
    gemini_acc = results["gemini"].accuracy
    ensemble_acc = results["ensemble"].accuracy
    
    improvement_over_roberta = (ensemble_acc - roberta_acc) / roberta_acc * 100 if roberta_acc > 0 else 0
    improvement_over_gemini = (ensemble_acc - gemini_acc) / gemini_acc * 100 if gemini_acc > 0 else 0
    
    print(f"\n🎯 ENSEMBLE IMPROVEMENT:")
    print(f"   Over RoBERTa alone: {improvement_over_roberta:+.1f}%")
    print(f"   Over Gemini alone:  {improvement_over_gemini:+.1f}%")
    
    # Save results
    if output_path:
        output_data = {
            "evaluation_date": str(Path(ground_truth_path).stat().st_mtime),
            "total_samples": len(samples),
            "label_distribution": dict(label_counts),
            "results": {
                k: {
                    "model_name": v.model_name,
                    "accuracy": v.accuracy,
                    "precision": v.precision,
                    "recall": v.recall,
                    "f1": v.f1,
                    "confusion_matrix": v.confusion_matrix,
                }
                for k, v in results.items()
            },
            "agreement_analysis": dict(agreement_counts),
            "ensemble_improvement": {
                "over_roberta": round(improvement_over_roberta, 2),
                "over_gemini": round(improvement_over_gemini, 2),
            },
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
    
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate sentiment ensemble against ground truth"
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        help="Path to ground truth CSV file",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to save JSON results (optional)",
    )
    
    args = parser.parse_args()
    
    run_evaluation(args.ground_truth, args.output)


if __name__ == "__main__":
    main()
