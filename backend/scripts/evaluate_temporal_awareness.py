"""
Evaluate Temporal-Aware Context Engineering

This script specifically measures the value of temporal awareness
in the Query Orchestrator (Node 1) - YOUR KEY INNOVATION.

Compares:
1. Full System (with temporal awareness)
2. Static Query Baseline (without temporal awareness)
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class TemporalAwarenessEvaluator:
    """Evaluates the impact of temporal-aware context engineering"""
    
    def __init__(self):
        # Define temporal patterns for Baguio
        self.temporal_patterns = {
            "february": ["panagbenga", "flower festival", "valentine"],
            "march": ["panagbenga", "summer start"],
            "april": ["summer", "holy week", "easter"],
            "may": ["summer", "election"],
            "june": ["rainy season start", "typhoon"],
            "july": ["rainy season", "typhoon", "flood"],
            "august": ["rainy season", "typhoon", "landslide"],
            "september": ["rainy season", "typhoon"],
            "october": ["rainy season end", "undas preparation"],
            "november": ["undas", "all saints day", "all souls day"],
            "december": ["christmas", "holiday", "new year"],
            "january": ["new year", "winter", "cold weather"]
        }
    
    def evaluate_query_coverage(
        self,
        static_queries: List[str],
        temporal_queries: List[str],
        month: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate how well queries cover temporal context
        
        Args:
            static_queries: Queries from static KEYWORD_CLUSTERS only
            temporal_queries: Queries including temporal expansion
            month: Current month (e.g., "february")
            focus_areas: Focus areas being analyzed
        
        Returns:
            Metrics showing temporal coverage improvement
        """
        month_lower = month.lower()
        expected_keywords = self.temporal_patterns.get(month_lower, [])
        
        # Check static query coverage
        static_coverage = sum(
            1 for keyword in expected_keywords
            if any(keyword in query.lower() for query in static_queries)
        )
        
        # Check temporal query coverage
        temporal_coverage = sum(
            1 for keyword in expected_keywords
            if any(keyword in query.lower() for query in temporal_queries)
        )
        
        # Calculate metrics
        total_expected = len(expected_keywords)
        
        results = {
            "month": month,
            "focus_areas": focus_areas,
            "expected_temporal_keywords": expected_keywords,
            "static_queries": {
                "count": len(static_queries),
                "queries": static_queries,
                "temporal_coverage": static_coverage / total_expected if total_expected > 0 else 0,
                "covered_keywords": [
                    kw for kw in expected_keywords
                    if any(kw in q.lower() for q in static_queries)
                ]
            },
            "temporal_queries": {
                "count": len(temporal_queries),
                "queries": temporal_queries,
                "temporal_coverage": temporal_coverage / total_expected if total_expected > 0 else 0,
                "covered_keywords": [
                    kw for kw in expected_keywords
                    if any(kw in q.lower() for q in temporal_queries)
                ]
            },
            "improvement": {
                "additional_queries": len(temporal_queries) - len(static_queries),
                "coverage_gain": (temporal_coverage - static_coverage) / total_expected if total_expected > 0 else 0,
                "percentage_improvement": ((temporal_coverage - static_coverage) / static_coverage * 100) if static_coverage > 0 else float('inf')
            }
        }
        
        return results
    
    def evaluate_retrieval_quality(
        self,
        static_results: List[Dict],
        temporal_results: List[Dict],
        ground_truth: Dict
    ) -> Dict[str, Any]:
        """
        Evaluate if temporal queries retrieve more relevant documents
        
        Args:
            static_results: Documents retrieved with static queries
            temporal_results: Documents retrieved with temporal queries
            ground_truth: Ground truth relevant documents
        
        Returns:
            Precision, recall, F1 for both approaches
        """
        gt_doc_ids = set(ground_truth.get("relevant_doc_ids", []))
        
        # Static results
        static_doc_ids = set(doc.get("id") for doc in static_results)
        static_tp = len(static_doc_ids & gt_doc_ids)
        static_precision = static_tp / len(static_doc_ids) if static_doc_ids else 0
        static_recall = static_tp / len(gt_doc_ids) if gt_doc_ids else 0
        static_f1 = 2 * (static_precision * static_recall) / (static_precision + static_recall) if (static_precision + static_recall) > 0 else 0
        
        # Temporal results
        temporal_doc_ids = set(doc.get("id") for doc in temporal_results)
        temporal_tp = len(temporal_doc_ids & gt_doc_ids)
        temporal_precision = temporal_tp / len(temporal_doc_ids) if temporal_doc_ids else 0
        temporal_recall = temporal_tp / len(gt_doc_ids) if gt_doc_ids else 0
        temporal_f1 = 2 * (temporal_precision * temporal_recall) / (temporal_precision + temporal_recall) if (temporal_precision + temporal_recall) > 0 else 0
        
        return {
            "static": {
                "precision": static_precision,
                "recall": static_recall,
                "f1": static_f1,
                "retrieved_count": len(static_doc_ids)
            },
            "temporal": {
                "precision": temporal_precision,
                "recall": temporal_recall,
                "f1": temporal_f1,
                "retrieved_count": len(temporal_doc_ids)
            },
            "improvement": {
                "precision_gain": temporal_precision - static_precision,
                "recall_gain": temporal_recall - static_recall,
                "f1_gain": temporal_f1 - static_f1
            }
        }
    
    def evaluate_seasonal_issue_detection(
        self,
        static_insights: List[str],
        temporal_insights: List[str],
        seasonal_ground_truth: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate if temporal awareness helps detect seasonal issues
        
        Args:
            static_insights: Insights from static queries
            temporal_insights: Insights from temporal queries
            seasonal_ground_truth: Known seasonal issues for this period
        
        Returns:
            Detection rates for seasonal issues
        """
        # Check how many seasonal issues were detected
        static_detected = sum(
            1 for issue in seasonal_ground_truth
            if any(issue.lower() in insight.lower() for insight in static_insights)
        )
        
        temporal_detected = sum(
            1 for issue in seasonal_ground_truth
            if any(issue.lower() in insight.lower() for insight in temporal_insights)
        )
        
        total_seasonal = len(seasonal_ground_truth)
        
        return {
            "seasonal_issues": seasonal_ground_truth,
            "static_detection_rate": static_detected / total_seasonal if total_seasonal > 0 else 0,
            "temporal_detection_rate": temporal_detected / total_seasonal if total_seasonal > 0 else 0,
            "improvement": {
                "additional_detections": temporal_detected - static_detected,
                "detection_rate_gain": (temporal_detected - static_detected) / total_seasonal if total_seasonal > 0 else 0
            }
        }
    
    def run_complete_evaluation(
        self,
        dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run complete temporal awareness evaluation
        
        Dataset format:
        [
            {
                "id": "issue_1",
                "month": "february",
                "focus_areas": ["safety", "tourism"],
                "static_queries": [...],
                "temporal_queries": [...],
                "static_results": [...],
                "temporal_results": [...],
                "static_insights": [...],
                "temporal_insights": [...],
                "ground_truth": {
                    "relevant_doc_ids": [...],
                    "seasonal_issues": [...]
                }
            },
            ...
        ]
        """
        all_query_coverage = []
        all_retrieval_quality = []
        all_seasonal_detection = []
        
        for sample in dataset:
            # 1. Query Coverage
            coverage = self.evaluate_query_coverage(
                static_queries=sample["static_queries"],
                temporal_queries=sample["temporal_queries"],
                month=sample["month"],
                focus_areas=sample["focus_areas"]
            )
            all_query_coverage.append(coverage)
            
            # 2. Retrieval Quality
            retrieval = self.evaluate_retrieval_quality(
                static_results=sample["static_results"],
                temporal_results=sample["temporal_results"],
                ground_truth=sample["ground_truth"]
            )
            all_retrieval_quality.append(retrieval)
            
            # 3. Seasonal Issue Detection
            seasonal = self.evaluate_seasonal_issue_detection(
                static_insights=sample["static_insights"],
                temporal_insights=sample["temporal_insights"],
                seasonal_ground_truth=sample["ground_truth"]["seasonal_issues"]
            )
            all_seasonal_detection.append(seasonal)
        
        # Aggregate results
        import numpy as np
        
        results = {
            "query_coverage": {
                "mean_static_coverage": np.mean([c["static_queries"]["temporal_coverage"] for c in all_query_coverage]),
                "mean_temporal_coverage": np.mean([c["temporal_queries"]["temporal_coverage"] for c in all_query_coverage]),
                "mean_coverage_gain": np.mean([c["improvement"]["coverage_gain"] for c in all_query_coverage]),
                "mean_additional_queries": np.mean([c["improvement"]["additional_queries"] for c in all_query_coverage])
            },
            "retrieval_quality": {
                "static_f1": np.mean([r["static"]["f1"] for r in all_retrieval_quality]),
                "temporal_f1": np.mean([r["temporal"]["f1"] for r in all_retrieval_quality]),
                "f1_gain": np.mean([r["improvement"]["f1_gain"] for r in all_retrieval_quality])
            },
            "seasonal_detection": {
                "static_detection_rate": np.mean([s["static_detection_rate"] for s in all_seasonal_detection]),
                "temporal_detection_rate": np.mean([s["temporal_detection_rate"] for s in all_seasonal_detection]),
                "detection_rate_gain": np.mean([s["improvement"]["detection_rate_gain"] for s in all_seasonal_detection])
            },
            "sample_size": len(dataset)
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Pretty print temporal awareness evaluation results"""
        print("\n" + "="*70)
        print("TEMPORAL-AWARE CONTEXT ENGINEERING EVALUATION")
        print("="*70)
        
        print(f"\nSample Size: {results['sample_size']}")
        
        print("\n1. QUERY COVERAGE (Temporal Keywords)")
        print("-" * 50)
        qc = results["query_coverage"]
        print(f"   Static Coverage:    {qc['mean_static_coverage']:.1%}")
        print(f"   Temporal Coverage:  {qc['mean_temporal_coverage']:.1%}")
        print(f"   Coverage Gain:      +{qc['mean_coverage_gain']:.1%}")
        print(f"   Additional Queries: +{qc['mean_additional_queries']:.1f} queries")
        
        print("\n2. RETRIEVAL QUALITY (Document Relevance)")
        print("-" * 50)
        rq = results["retrieval_quality"]
        print(f"   Static F1:     {rq['static_f1']:.1%}")
        print(f"   Temporal F1:   {rq['temporal_f1']:.1%}")
        print(f"   F1 Gain:       +{rq['f1_gain']:.1%}")
        
        print("\n3. SEASONAL ISSUE DETECTION")
        print("-" * 50)
        sd = results["seasonal_detection"]
        print(f"   Static Detection:    {sd['static_detection_rate']:.1%}")
        print(f"   Temporal Detection:  {sd['temporal_detection_rate']:.1%}")
        print(f"   Detection Gain:      +{sd['detection_rate_gain']:.1%}")
        
        print("\n" + "="*70)
        print("KEY FINDING: Temporal-Aware Context Engineering improves:")
        print(f"  • Query coverage by {qc['mean_coverage_gain']:.1%}")
        print(f"  • Retrieval quality by {rq['f1_gain']:.1%}")
        print(f"  • Seasonal detection by {sd['detection_rate_gain']:.1%}")
        print("="*70 + "\n")


# Example usage
if __name__ == "__main__":
    evaluator = TemporalAwarenessEvaluator()
    
    # Example dataset
    example_dataset = [
        {
            "id": "issue_1",
            "month": "february",
            "focus_areas": ["safety", "tourism"],
            "static_queries": [
                "Baguio crime incident OR Baguio theft problem",
                "Baguio tourist complaint OR Baguio scam tourist"
            ],
            "temporal_queries": [
                "Baguio crime incident OR Baguio theft problem",
                "Baguio tourist complaint OR Baguio scam tourist",
                "Baguio Panagbenga safety security",  # Temporal
                "Baguio flower festival crowd"  # Temporal
            ],
            "static_results": [],
            "temporal_results": [],
            "static_insights": [],
            "temporal_insights": [],
            "ground_truth": {
                "relevant_doc_ids": [],
                "seasonal_issues": ["panagbenga crowd control", "festival traffic"]
            }
        }
    ]
    
    # results = evaluator.run_complete_evaluation(example_dataset)
    # evaluator.print_results(results)
    
    print("Temporal awareness evaluation script ready!")
    print("This specifically measures YOUR KEY INNOVATION.")
