"""
Llama-3.3-70B-Versatile Sentiment Evaluation Script

This script evaluates Llama-3.3-70B-Versatile sentiment analysis accuracy against:
- RoBERTa (baseline transformer)
- Llama-4-Scout-17b (current production model)
- Qwen3-32b (alternative LLM)
- Ensemble (RoBERTa + Llama-3.3-70B)

Compares all models on the same ground truth dataset to determine
which provides the best sentiment accuracy for your thesis.

Key differences from Llama-4-Scout:
- Llama-3.3-70B: 15K TPM, 14K TPD (lower throughput)
- Llama-4-Scout: 30K TPM, 500K TPD (higher throughput)
- 70B model may have better reasoning but slower speed

Usage:
    python -m scripts.evaluate_llama33_70b_sentiment --ground-truth data/ground_truth.csv

Output:
    - Accuracy comparison across all models
    - Precision, Recall, F1 for each model
    - Confusion matrices
    - Speed benchmarks
    - Thesis-ready results table
"""

import argparse
import asyncio
import csv
import json
import sys
import time
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.agents.sentiment_agent import (
    get_sentiment_model,
    sanitize_text,
)
from app.schemas.snapshot import WebDocument
from app.core.config import get_settings


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
    avg_time_per_sample: float  # seconds
    total_time: float  # seconds


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


async def predict_with_llm(texts: list[str], model_name: str, batch_size: int = 40) -> tuple[list[str], float]:
    """
    Predict sentiment using specified Groq LLM model.
    
    Args:
        texts: List of text samples
        model_name: Groq model name (e.g., "llama-3.1-70b-versatile")
        batch_size: Batch size for processing
    
    Returns:
        Tuple of (predictions, total_time)
    """
    from app.services.llm.groq_provider import get_groq_provider
    
    llm = get_groq_provider(model_name)
    
    predictions = []
    start_time = time.time()
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Build batch prompt
        doc_entries = []
        for idx, text in enumerate(batch):
            clean_text = text[:250].replace('"', "'")
            doc_entries.append(f"{idx}. {clean_text}")
        
        docs_block = "\n".join(doc_entries)
        
        prompt = f"""You are a sentiment classifier for civic content about Baguio City, Philippines.

Analyze each item and classify sentiment:
- "positive": Appreciation, improvements, success, good news
- "negative": Complaints, problems, incidents, criticism
- "neutral": Factual announcements, balanced reporting

{docs_block}

Return JSON array: [{{"i": 0, "s": "negative"}}, {{"i": 1, "s": "neutral"}}]"""

        try:
            response = await llm.generate(
                prompt=prompt,
                system_prompt="You are a sentiment analysis expert. Return accurate, concise JSON.",
                temperature=0.0,
                max_tokens=2000,
            )
            
            # Parse response
            batch_preds = parse_llm_response(response, len(batch))
            predictions.extend(batch_preds)
            
        except Exception as e:
            print(f"   ⚠️  Batch {i//batch_size + 1} failed: {e}")
            # Fallback to neutral
            predictions.extend(["neutral"] * len(batch))
    
    total_time = time.time() - start_time
    return predictions, total_time


def parse_llm_response(response_text: str, expected_count: int) -> list[str]:
    """Parse LLM JSON response into sentiment labels."""
    text = response_text.strip()
    
    # Extract JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    elif "{" in text and "}" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
    
    # Parse
    default = ["neutral"] * expected_count
    try:
        data = json.loads(text)
        if isinstance(data, list):
            results = default.copy()
            for item in data:
                if isinstance(item, dict):
                    idx = item.get("i", item.get("index", -1))
                    sentiment = item.get("s", item.get("sentiment", "neutral")).lower()
                    if 0 <= idx < expected_count and sentiment in ("positive", "negative", "neutral"):
                        results[idx] = sentiment
            return results
    except (json.JSONDecodeError, TypeError):
        pass
    
    return default


async def run_evaluation(ground_truth_path: str, output_path: str | None = None):
    """
    Run comprehensive evaluation comparing all sentiment models.
    
    Models tested:
    1. RoBERTa (baseline transformer)
    2. Llama-3.3-70B-Versatile (NEW - testing)
    3. Llama-4-Scout-17b (current production)
    4. Qwen3-32b (alternative LLM)
    5. Ensemble (RoBERTa + Llama-3.3-70B)
    """
    # Clear Groq provider cache to ensure fresh state for each model
    from app.services.llm.groq_provider import clear_groq_cache
    clear_groq_cache()
    
    print("=" * 70)
    print("LLAMA-3.3-70B-VERSATILE SENTIMENT EVALUATION")
    print("Comparing: RoBERTa | Llama-3.3-70B | Llama-4-Scout | Qwen3-32b | Ensemble")
    print("=" * 70)
    
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
    print("   ✓ RoBERTa loaded")
    
    # Prepare data
    texts = [sanitize_text(s["text"])[:512] for s in samples]
    ground_truth_labels = [s["label"] for s in samples]
    
    results = {}
    
    # ========================================================================
    # MODEL 1: RoBERTa (Baseline)
    # ========================================================================
    print("\n🔄 Running predictions...")
    print("   → RoBERTa (baseline)...")
    start = time.time()
    roberta_probs = roberta.predict_batch_with_probs(texts)
    roberta_preds = [max(p, key=p.get) for p in roberta_probs]
    roberta_time = time.time() - start
    
    acc, prec, rec, f1, conf = calculate_metrics(roberta_preds, ground_truth_labels)
    results["roberta"] = EvaluationResult(
        model_name="RoBERTa (twitter-roberta-base)",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
        avg_time_per_sample=roberta_time / len(samples),
        total_time=roberta_time,
    )
    print(f"      Accuracy: {acc:.1%} | Time: {roberta_time:.1f}s")
    
    # ========================================================================
    # MODEL 2: Llama-3.3-70B-Versatile (NEW - TESTING)
    # ========================================================================
    print("   → Llama-3.3-70B-Versatile (NEW - testing)...")
    print("      Note: 15K TPM limit - using smaller batches")
    llama70b_preds, llama70b_time = await predict_with_llm(
        texts, 
        "llama-3.3-70b-versatile",
        batch_size=20  # Smaller batch due to 15K TPM limit
    )
    
    acc, prec, rec, f1, conf = calculate_metrics(llama70b_preds, ground_truth_labels)
    results["llama33_70b"] = EvaluationResult(
        model_name="Llama-3.3-70B-Versatile",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
        avg_time_per_sample=llama70b_time / len(samples),
        total_time=llama70b_time,
    )
    print(f"      Accuracy: {acc:.1%} | Time: {llama70b_time:.1f}s")
    
    # ========================================================================
    # MODEL 3: Llama-4-Scout-17b (Current Production)
    # ========================================================================
    print("   → Llama-4-Scout-17b (current production)...")
    scout_preds, scout_time = await predict_with_llm(
        texts, 
        "meta-llama/llama-4-scout-17b-16e-instruct",
        batch_size=40  # Larger batch (30K TPM)
    )
    
    acc, prec, rec, f1, conf = calculate_metrics(scout_preds, ground_truth_labels)
    results["llama4_scout"] = EvaluationResult(
        model_name="Llama-4-Scout-17b",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
        avg_time_per_sample=scout_time / len(samples),
        total_time=scout_time,
    )
    print(f"      Accuracy: {acc:.1%} | Time: {scout_time:.1f}s")
    
    # ========================================================================
    # MODEL 4: Qwen3-32b (Alternative)
    # ========================================================================
    print("   → Qwen3-32b (alternative)...")
    qwen_preds, qwen_time = await predict_with_llm(
        texts,
        "qwen/qwen3-32b",
        batch_size=20  # Smaller batch due to 6K TPM limit
    )
    
    acc, prec, rec, f1, conf = calculate_metrics(qwen_preds, ground_truth_labels)
    results["qwen3_32b"] = EvaluationResult(
        model_name="Qwen3-32b",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
        avg_time_per_sample=qwen_time / len(samples),
        total_time=qwen_time,
    )
    print(f"      Accuracy: {acc:.1%} | Time: {qwen_time:.1f}s")
    
    # ========================================================================
    # MODEL 5: Ensemble (RoBERTa + Llama-3.3-70B)
    # ========================================================================
    print("   → Ensemble (40% RoBERTa + 60% Llama-3.3-70B)...")
    
    # Combine predictions with ensemble weights
    ROBERTA_WEIGHT = 0.4
    LLAMA70B_WEIGHT = 0.6
    
    ensemble_preds = []
    for i in range(len(samples)):
        r_probs = roberta_probs[i]
        l_pred = llama70b_preds[i]
        
        # Convert Llama prediction to probabilities (simplified)
        l_probs = {
            "positive": 0.9 if l_pred == "positive" else 0.05,
            "negative": 0.9 if l_pred == "negative" else 0.05,
            "neutral": 0.9 if l_pred == "neutral" else 0.05,
        }
        
        # Weighted combination
        combined = {
            "negative": (ROBERTA_WEIGHT * r_probs["negative"]) + (LLAMA70B_WEIGHT * l_probs["negative"]),
            "neutral": (ROBERTA_WEIGHT * r_probs["neutral"]) + (LLAMA70B_WEIGHT * l_probs["neutral"]),
            "positive": (ROBERTA_WEIGHT * r_probs["positive"]) + (LLAMA70B_WEIGHT * l_probs["positive"]),
        }
        
        ensemble_preds.append(max(combined, key=combined.get))
    
    acc, prec, rec, f1, conf = calculate_metrics(ensemble_preds, ground_truth_labels)
    results["ensemble_70b"] = EvaluationResult(
        model_name="Ensemble (RoBERTa + Llama-3.3-70B)",
        accuracy=round(acc, 4),
        precision=prec,
        recall=rec,
        f1=f1,
        confusion_matrix=conf,
        total_samples=len(samples),
        correct=int(acc * len(samples)),
        avg_time_per_sample=(roberta_time + llama70b_time) / len(samples),
        total_time=roberta_time + llama70b_time,
    )
    print(f"      Accuracy: {acc:.1%} | Time: {roberta_time + llama70b_time:.1f}s")
    
    # ========================================================================
    # RESULTS SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│                      ACCURACY COMPARISON                           │")
    print("├───────────────────────────┬──────────┬──────────────┬─────────────┤")
    print("│ Model                     │ Accuracy │ Correct/Total│ Time (s)    │")
    print("├───────────────────────────┼──────────┼──────────────┼─────────────┤")
    
    for key in ["roberta", "llama33_70b", "llama4_scout", "qwen3_32b", "ensemble_70b"]:
        if key in results:
            r = results[key]
            print(f"│ {r.model_name[:25]:<25} │ {r.accuracy:>6.1%}  │ {r.correct:>5}/{r.total_samples:<6} │ {r.total_time:>10.1f}  │")
    
    print("└───────────────────────────┴──────────┴──────────────┴─────────────┘")
    
    # Macro F1
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│                         MACRO F1 SCORES                            │")
    print("├───────────────────────────┬──────────┬──────────┬─────────────────┤")
    print("│ Model                     │ Positive │ Negative │ Neutral         │")
    print("├───────────────────────────┼──────────┼──────────┼─────────────────┤")
    
    for key in ["roberta", "llama33_70b", "llama4_scout", "qwen3_32b", "ensemble_70b"]:
        if key in results:
            r = results[key]
            print(f"│ {key.replace('_', '-')[:25]:<25} │ {r.f1.get('positive', 0):>6.2f}   │ {r.f1.get('negative', 0):>6.2f}   │ {r.f1.get('neutral', 0):>14.2f}  │")
    
    print("└───────────────────────────┴──────────┴──────────┴─────────────────┘")
    
    # Speed comparison
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│                      SPEED COMPARISON                              │")
    print("├───────────────────────────┬──────────────────┬─────────────────────┤")
    print("│ Model                     │ Total Time (s)   │ Per Sample (ms)     │")
    print("├───────────────────────────┼──────────────────┼─────────────────────┤")
    
    for key in ["roberta", "llama33_70b", "llama4_scout", "qwen3_32b", "ensemble_70b"]:
        if key in results:
            r = results[key]
            per_sample_ms = r.avg_time_per_sample * 1000
            print(f"│ {key.replace('_', '-')[:25]:<25} │ {r.total_time:>15.1f}  │ {per_sample_ms:>18.1f}  │")
    
    print("└───────────────────────────┴──────────────────┴─────────────────────┘")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDATIONS")
    print("=" * 70)
    
    # Find best accuracy
    best_acc_key = max(results.keys(), key=lambda k: results[k].accuracy)
    best_acc = results[best_acc_key]
    
    # Find fastest
    fastest_key = min(results.keys(), key=lambda k: results[k].total_time)
    fastest = results[fastest_key]
    
    print(f"\n✅ BEST ACCURACY: {best_acc.model_name}")
    print(f"   Accuracy: {best_acc.accuracy:.1%} ({best_acc.correct}/{best_acc.total_samples} correct)")
    print(f"   Macro F1: {sum(best_acc.f1.values())/3:.3f}")
    
    print(f"\n⚡ FASTEST: {fastest.model_name}")
    print(f"   Total time: {fastest.total_time:.1f}s")
    print(f"   Per sample: {fastest.avg_time_per_sample*1000:.1f}ms")
    
    # Llama-3.3-70B specific analysis
    if "llama33_70b" in results:
        llama70b = results["llama33_70b"]
        roberta_acc = results["roberta"].accuracy
        scout_acc = results["llama4_scout"].accuracy
        
        improvement_vs_roberta = (llama70b.accuracy - roberta_acc) / roberta_acc * 100 if roberta_acc > 0 else 0
        improvement_vs_scout = (llama70b.accuracy - scout_acc) / scout_acc * 100 if scout_acc > 0 else 0
        
        print(f"\n🔬 LLAMA-3.3-70B-VERSATILE ANALYSIS:")
        print(f"   Accuracy: {llama70b.accuracy:.1%}")
        print(f"   vs RoBERTa: {improvement_vs_roberta:+.1f}%")
        print(f"   vs Llama-4-Scout: {improvement_vs_scout:+.1f}%")
        print(f"   Speed: {llama70b.total_time:.1f}s ({llama70b.avg_time_per_sample*1000:.1f}ms/sample)")
        print(f"   TPM: 15K (vs Scout's 30K)")
        print(f"   TPD: 14K (vs Scout's 500K)")
        
        if "qwen3_32b" in results:
            qwen_acc = results["qwen3_32b"].accuracy
            vs_qwen = (llama70b.accuracy - qwen_acc) / qwen_acc * 100 if qwen_acc > 0 else 0
            print(f"   vs Qwen3-32b: {vs_qwen:+.1f}%")
        
        # Recommendation logic
        if llama70b.accuracy >= best_acc.accuracy * 0.98:  # Within 2% of best
            print(f"\n   ✅ COMPETITIVE: Llama-3.3-70B is {'best' if llama70b.accuracy == best_acc.accuracy else 'near-best'}")
            print(f"      - Good accuracy ({llama70b.accuracy:.1%})")
            print(f"      - Larger model (70B parameters)")
            print(f"      ⚠️  BUT: Lower TPM (15K) limits concurrent processing")
            print(f"      ⚠️  BUT: Lower TPD (14K) limits daily volume")
        else:
            print(f"\n   ⚠️  Consider alternatives:")
            print(f"      - {best_acc.model_name} has {(best_acc.accuracy - llama70b.accuracy)*100:.1f}% better accuracy")
        
        # Speed comparison with Scout
        if "llama4_scout" in results:
            scout = results["llama4_scout"]
            speed_ratio = llama70b.total_time / scout.total_time if scout.total_time > 0 else 0
            print(f"\n   ⏱️  SPEED COMPARISON:")
            print(f"      - Llama-3.3-70B: {llama70b.total_time:.1f}s")
            print(f"      - Llama-4-Scout: {scout.total_time:.1f}s")
            print(f"      - Ratio: {speed_ratio:.2f}x {'slower' if speed_ratio > 1 else 'faster'}")
        
        # Final recommendation
        print(f"\n   💡 RECOMMENDATION:")
        if llama70b.accuracy > scout_acc * 1.02:  # 2%+ better
            print(f"      ✅ USE Llama-3.3-70B if accuracy is priority")
            print(f"         ({(llama70b.accuracy - scout_acc)*100:.1f}% better than Scout)")
        elif llama70b.total_time < scout.total_time * 0.9:  # 10%+ faster
            print(f"      ✅ USE Llama-3.3-70B if speed is priority")
            print(f"         ({(1 - llama70b.total_time/scout.total_time)*100:.1f}% faster than Scout)")
        else:
            print(f"      ⚠️  KEEP Llama-4-Scout (current production)")
            print(f"         - Similar accuracy ({scout_acc:.1%} vs {llama70b.accuracy:.1%})")
            print(f"         - Higher TPM (30K vs 15K) = better concurrency")
            print(f"         - Higher TPD (500K vs 14K) = better scalability")
    
    # Save results
    if output_path:
        output_data = {
            "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
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
                    "total_time": v.total_time,
                    "avg_time_per_sample": v.avg_time_per_sample,
                }
                for k, v in results.items()
            },
            "recommendations": {
                "best_accuracy": best_acc.model_name,
                "fastest": fastest.model_name,
            },
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Llama-3.3-70B-Versatile sentiment analysis against other models"
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
    
    # Run async evaluation
    asyncio.run(run_evaluation(args.ground_truth, args.output))


if __name__ == "__main__":
    main()
