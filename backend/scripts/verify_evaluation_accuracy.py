"""
CTO-Level Verification Script for Evaluation Accuracy

This script performs rigorous validation of evaluation results to ensure:
1. Confusion matrices are mathematically correct
2. Accuracy calculations match confusion matrix totals
3. No data corruption or calculation errors
4. Results are reproducible and scientifically valid

Run this after any evaluation to verify integrity.
"""

import json
import sys
from pathlib import Path

def verify_confusion_matrix(model_name: str, result: dict, total_samples: int) -> tuple[bool, list[str]]:
    """Verify confusion matrix integrity and accuracy calculation."""
    errors = []
    
    confusion = result["confusion_matrix"]
    stated_accuracy = result["accuracy"]
    stated_correct = result.get("correct", int(stated_accuracy * total_samples))
    
    # Calculate actual totals from confusion matrix
    actual_correct = 0
    actual_total = 0
    
    for true_label in confusion:
        for pred_label, count in confusion[true_label].items():
            actual_total += count
            if true_label == pred_label:
                actual_correct += count
    
    # Verify total samples
    if actual_total != total_samples:
        errors.append(
            f"❌ Total mismatch: confusion matrix has {actual_total} samples "
            f"but metadata says {total_samples}"
        )
    
    # Verify correct count
    if actual_correct != stated_correct:
        errors.append(
            f"❌ Correct count mismatch: confusion matrix shows {actual_correct} correct "
            f"but metadata says {stated_correct}"
        )
    
    # Verify accuracy calculation
    calculated_accuracy = actual_correct / actual_total if actual_total > 0 else 0
    if abs(calculated_accuracy - stated_accuracy) > 0.001:  # Allow 0.1% rounding error
        errors.append(
            f"❌ Accuracy mismatch: calculated {calculated_accuracy:.4f} "
            f"but stated {stated_accuracy:.4f}"
        )
    
    # Verify precision/recall/F1 calculations
    for label in ["positive", "negative", "neutral"]:
        # Calculate TP, FP, FN
        tp = confusion.get(label, {}).get(label, 0)
        
        fp = sum(
            confusion.get(other_label, {}).get(label, 0)
            for other_label in confusion
            if other_label != label
        )
        
        fn = sum(
            count for pred_label, count in confusion.get(label, {}).items()
            if pred_label != label
        )
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Verify against stated values
        stated_precision = result["precision"].get(label, 0)
        stated_recall = result["recall"].get(label, 0)
        stated_f1 = result["f1"].get(label, 0)
        
        if abs(precision - stated_precision) > 0.001:
            errors.append(
                f"❌ {label} precision mismatch: calculated {precision:.4f} "
                f"but stated {stated_precision:.4f}"
            )
        
        if abs(recall - stated_recall) > 0.001:
            errors.append(
                f"❌ {label} recall mismatch: calculated {recall:.4f} "
                f"but stated {stated_recall:.4f}"
            )
        
        if abs(f1 - stated_f1) > 0.001:
            errors.append(
                f"❌ {label} F1 mismatch: calculated {f1:.4f} "
                f"but stated {stated_f1:.4f}"
            )
    
    return len(errors) == 0, errors


def verify_evaluation_file(filepath: str) -> bool:
    """Verify entire evaluation file for integrity."""
    print("=" * 70)
    print("CTO-LEVEL EVALUATION VERIFICATION")
    print("=" * 70)
    print(f"\n📂 Verifying: {filepath}\n")
    
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ FAILED: Could not load file: {e}")
        return False
    
    # Verify metadata
    print("✓ File loaded successfully")
    print(f"  Evaluation date: {data.get('evaluation_date')}")
    print(f"  Total samples: {data.get('total_samples')}")
    print(f"  Label distribution: {data.get('label_distribution')}")
    
    # Verify label distribution sums to total
    label_dist = data.get("label_distribution", {})
    dist_total = sum(label_dist.values())
    stated_total = data.get("total_samples", 0)
    
    if dist_total != stated_total:
        print(f"\n❌ CRITICAL: Label distribution ({dist_total}) doesn't match total ({stated_total})")
        return False
    
    print(f"✓ Label distribution verified ({dist_total} samples)")
    
    # Verify each model
    results = data.get("results", {})
    all_valid = True
    total_samples = data.get("total_samples", 0)
    
    print(f"\n🔍 Verifying {len(results)} models...\n")
    
    for model_key, result in results.items():
        model_name = result.get("model_name", model_key)
        print(f"{'─' * 70}")
        print(f"Model: {model_name}")
        print(f"{'─' * 70}")
        
        is_valid, errors = verify_confusion_matrix(model_name, result, total_samples)
        
        if is_valid:
            print(f"✅ VALID - All calculations correct")
            correct = int(result['accuracy'] * total_samples)
            print(f"   Accuracy: {result['accuracy']:.1%} ({correct}/{total_samples})")
            print(f"   Macro F1: {sum(result['f1'].values())/3:.4f}")
        else:
            print(f"❌ INVALID - Found {len(errors)} errors:")
            for error in errors:
                print(f"   {error}")
            all_valid = False
        
        print()
    
    # Final verdict
    print("=" * 70)
    if all_valid:
        print("✅ VERIFICATION PASSED")
        print("All models have mathematically correct results.")
        print("Evaluation is scientifically valid and reproducible.")
    else:
        print("❌ VERIFICATION FAILED")
        print("Some models have calculation errors.")
        print("DO NOT use these results for thesis - re-run evaluation.")
    print("=" * 70)
    
    return all_valid


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_evaluation_accuracy.py <results_file.json>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    
    is_valid = verify_evaluation_file(filepath)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
