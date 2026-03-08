"""
Empirical Evaluation Script for Hinaing Framework

Metrics:
1. Contextual Faithfulness
2. Thematic Actionability  
3. Agentic Verification Rate
"""

import json
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class GroundTruth:
    """Ground truth annotation for a civic issue"""
    issue_id: str
    true_sentiment: str  # positive, negative, neutral
    true_themes: List[str]
    verified_facts: List[str]
    unverified_opinions: List[str]
    actionable_recommendations: List[str]
    source_documents: List[str]


@dataclass
class SystemOutput:
    """System-generated output for evaluation"""
    issue_id: str
    generated_sentiment: str
    generated_themes: List[str]
    generated_insights: List[str]
    claims: List[Dict[str, Any]]
    credibility_scores: Dict[str, float]
    source_attributions: List[str]


class EmpiricalEvaluator:
    """Evaluates Hinaing framework on three key metrics"""
    
    def __init__(self):
        self.results = {
            "contextual_faithfulness": {},
            "thematic_actionability": {},
            "agentic_verification": {}
        }
    
    # ========================================
    # METRIC 1: CONTEXTUAL FAITHFULNESS
    # ========================================
    
    def evaluate_contextual_faithfulness(
        self, 
        ground_truth: GroundTruth,
        system_output: SystemOutput
    ) -> Dict[str, float]:
        """
        Measures how accurately system outputs reflect actual sources
        
        Returns:
            - hallucination_rate: % of claims not in sources
            - sentiment_accuracy: % correct sentiment classification
            - source_attribution_rate: % of insights with valid sources
            - overall_faithfulness: Combined score (0-1)
        """
        scores = {}
        
        # 1. Hallucination Rate
        hallucinations = 0
        for claim in system_output.claims:
            claim_text = claim.get("text", "")
            found_in_source = any(
                claim_text.lower() in doc.lower() 
                for doc in ground_truth.source_documents
            )
            if not found_in_source:
                hallucinations += 1
        
        scores["hallucination_rate"] = hallucinations / len(system_output.claims) if system_output.claims else 0
        
        # 2. Sentiment Accuracy
        scores["sentiment_accuracy"] = 1.0 if system_output.generated_sentiment == ground_truth.true_sentiment else 0.0
        
        # 3. Source Attribution Rate
        attributed = sum(1 for attr in system_output.source_attributions if attr)
        scores["source_attribution_rate"] = attributed / len(system_output.generated_insights) if system_output.generated_insights else 0
        
        # 4. Overall Faithfulness (inverse of hallucination, weighted with other metrics)
        scores["overall_faithfulness"] = (
            (1 - scores["hallucination_rate"]) * 0.4 +
            scores["sentiment_accuracy"] * 0.3 +
            scores["source_attribution_rate"] * 0.3
        )
        
        return scores
    
    # ========================================
    # METRIC 2: THEMATIC ACTIONABILITY
    # ========================================
    
    def evaluate_thematic_actionability(
        self,
        ground_truth: GroundTruth,
        system_output: SystemOutput
    ) -> Dict[str, float]:
        """
        Measures how useful insights are for civic decision-making
        
        Returns:
            - specificity_score: Has specific locations/timeframes
            - recommendation_quality: Has concrete recommendations
            - stakeholder_identification: Identifies responsible parties
            - overall_actionability: Combined score (0-1)
        """
        scores = {}
        actionability_scores = []
        
        for insight in system_output.generated_insights:
            insight_score = 0
            
            # Check for specific location
            baguio_locations = [
                "session road", "burnham park", "kennon road", 
                "camp john hay", "baguio cathedral", "mines view"
            ]
            if any(loc in insight.lower() for loc in baguio_locations):
                insight_score += 0.2
            
            # Check for timeframe
            temporal_markers = [
                "panagbenga", "february", "december", "rainy season",
                "typhoon season", "summer", "undas", "christmas"
            ]
            if any(marker in insight.lower() for marker in temporal_markers):
                insight_score += 0.2
            
            # Check for stakeholder
            stakeholders = [
                "dpwh", "city hall", "mayor", "lgu", "baguio government",
                "tourism office", "health department", "police"
            ]
            if any(stakeholder in insight.lower() for stakeholder in stakeholders):
                insight_score += 0.2
            
            # Check for concrete recommendation
            action_verbs = [
                "should", "must", "recommend", "propose", "suggest",
                "implement", "improve", "fix", "address", "resolve"
            ]
            if any(verb in insight.lower() for verb in action_verbs):
                insight_score += 0.2
            
            # Check for priority/urgency
            priority_markers = ["urgent", "critical", "immediate", "priority", "important"]
            if any(marker in insight.lower() for marker in priority_markers):
                insight_score += 0.2
            
            actionability_scores.append(insight_score)
        
        scores["specificity_score"] = np.mean([s >= 0.2 for s in actionability_scores]) if actionability_scores else 0
        scores["recommendation_quality"] = np.mean([s >= 0.4 for s in actionability_scores]) if actionability_scores else 0
        scores["stakeholder_identification"] = np.mean([s >= 0.6 for s in actionability_scores]) if actionability_scores else 0
        scores["overall_actionability"] = np.mean(actionability_scores) if actionability_scores else 0
        
        return scores
    
    # ========================================
    # METRIC 3: AGENTIC VERIFICATION RATE
    # ========================================
    
    def evaluate_agentic_verification(
        self,
        ground_truth: GroundTruth,
        system_output: SystemOutput
    ) -> Dict[str, float]:
        """
        Measures how effectively multi-agent system verifies claims
        
        Returns:
            - verification_rate: % of claims verified by 3+ signals
            - precision: Of verified claims, % actually true
            - recall: Of true claims, % system verified
            - f1_score: Harmonic mean of precision and recall
            - signal_breakdown: Contribution of each signal
        """
        scores = {}
        
        verified_claims = []
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        signal_counts = defaultdict(int)
        
        for claim in system_output.claims:
            claim_text = claim.get("text", "")
            verification_signals = 0
            
            # Signal 1: Domain Trust
            if claim.get("domain_trust_score", 0) > 0.7:
                verification_signals += 1
                signal_counts["domain_trust"] += 1
            
            # Signal 2: Cross-Reference
            if claim.get("cross_reference_count", 0) >= 2:
                verification_signals += 1
                signal_counts["cross_reference"] += 1
            
            # Signal 3: Fact-Check (Tavily)
            if claim.get("tavily_verified", False):
                verification_signals += 1
                signal_counts["tavily"] += 1
            
            # Signal 4: LLM Analysis
            if claim.get("llm_plausibility", 0) > 0.7:
                verification_signals += 1
                signal_counts["llm_analysis"] += 1
            
            # Signal 5: Semantic Similarity
            if claim.get("semantic_similarity", 0) > 0.8:
                verification_signals += 1
                signal_counts["semantic_similarity"] += 1
            
            # Claim is verified if 3+ signals agree
            is_verified = verification_signals >= 3
            verified_claims.append(is_verified)
            
            # Check against ground truth
            is_actually_true = claim_text in ground_truth.verified_facts
            
            if is_verified and is_actually_true:
                true_positives += 1
            elif is_verified and not is_actually_true:
                false_positives += 1
            elif not is_verified and is_actually_true:
                false_negatives += 1
        
        # Calculate metrics
        scores["verification_rate"] = sum(verified_claims) / len(verified_claims) if verified_claims else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        scores["precision"] = precision
        scores["recall"] = recall
        scores["f1_score"] = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Signal breakdown
        total_signals = sum(signal_counts.values())
        scores["signal_breakdown"] = {
            signal: count / total_signals if total_signals > 0 else 0
            for signal, count in signal_counts.items()
        }
        
        return scores
    
    # ========================================
    # AGGREGATE EVALUATION
    # ========================================
    
    def evaluate_all(
        self,
        ground_truths: List[GroundTruth],
        system_outputs: List[SystemOutput]
    ) -> Dict[str, Any]:
        """
        Evaluate all metrics across entire dataset
        """
        all_faithfulness = []
        all_actionability = []
        all_verification = []
        
        for gt, output in zip(ground_truths, system_outputs):
            # Metric 1: Contextual Faithfulness
            faith_scores = self.evaluate_contextual_faithfulness(gt, output)
            all_faithfulness.append(faith_scores)
            
            # Metric 2: Thematic Actionability
            action_scores = self.evaluate_thematic_actionability(gt, output)
            all_actionability.append(action_scores)
            
            # Metric 3: Agentic Verification
            verif_scores = self.evaluate_agentic_verification(gt, output)
            all_verification.append(verif_scores)
        
        # Aggregate results
        results = {
            "contextual_faithfulness": {
                "mean_overall": np.mean([s["overall_faithfulness"] for s in all_faithfulness]),
                "mean_hallucination_rate": np.mean([s["hallucination_rate"] for s in all_faithfulness]),
                "mean_sentiment_accuracy": np.mean([s["sentiment_accuracy"] for s in all_faithfulness]),
                "std_overall": np.std([s["overall_faithfulness"] for s in all_faithfulness])
            },
            "thematic_actionability": {
                "mean_overall": np.mean([s["overall_actionability"] for s in all_actionability]),
                "mean_specificity": np.mean([s["specificity_score"] for s in all_actionability]),
                "mean_recommendation_quality": np.mean([s["recommendation_quality"] for s in all_actionability]),
                "std_overall": np.std([s["overall_actionability"] for s in all_actionability])
            },
            "agentic_verification": {
                "mean_verification_rate": np.mean([s["verification_rate"] for s in all_verification]),
                "mean_precision": np.mean([s["precision"] for s in all_verification]),
                "mean_recall": np.mean([s["recall"] for s in all_verification]),
                "mean_f1": np.mean([s["f1_score"] for s in all_verification]),
                "std_verification_rate": np.std([s["verification_rate"] for s in all_verification])
            },
            "sample_size": len(ground_truths)
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Pretty print evaluation results"""
        print("\n" + "="*60)
        print("EMPIRICAL EVALUATION RESULTS")
        print("="*60)
        
        print(f"\nSample Size: {results['sample_size']}")
        
        print("\n1. CONTEXTUAL FAITHFULNESS")
        print("-" * 40)
        cf = results["contextual_faithfulness"]
        print(f"   Overall Faithfulness: {cf['mean_overall']:.2%} (±{cf['std_overall']:.2%})")
        print(f"   Hallucination Rate:   {cf['mean_hallucination_rate']:.2%}")
        print(f"   Sentiment Accuracy:   {cf['mean_sentiment_accuracy']:.2%}")
        
        print("\n2. THEMATIC ACTIONABILITY")
        print("-" * 40)
        ta = results["thematic_actionability"]
        print(f"   Overall Actionability: {ta['mean_overall']:.2%} (±{ta['std_overall']:.2%})")
        print(f"   Specificity Score:     {ta['mean_specificity']:.2%}")
        print(f"   Recommendation Quality: {ta['mean_recommendation_quality']:.2%}")
        
        print("\n3. AGENTIC VERIFICATION RATE")
        print("-" * 40)
        av = results["agentic_verification"]
        print(f"   Verification Rate: {av['mean_verification_rate']:.2%} (±{av['std_verification_rate']:.2%})")
        print(f"   Precision:         {av['mean_precision']:.2%}")
        print(f"   Recall:            {av['mean_recall']:.2%}")
        print(f"   F1-Score:          {av['mean_f1']:.2%}")
        
        print("\n" + "="*60)


# Example usage
if __name__ == "__main__":
    evaluator = EmpiricalEvaluator()
    
    # Load your ground truth and system outputs
    # ground_truths = load_ground_truth("data/ground_truth.json")
    # system_outputs = load_system_outputs("data/system_outputs.json")
    
    # results = evaluator.evaluate_all(ground_truths, system_outputs)
    # evaluator.print_results(results)
    
    print("Empirical evaluation script ready!")
    print("Implement data loading and run evaluation.")
