"""
Baseline Models for Empirical Evaluation

Implements 3 baseline models:
1. Simple LLM (single call, no agents)
2. RoBERTa-Only (sentiment classifier only)
3. RAG-Only (simple RAG without agents)
"""

import json
import time
from typing import Dict, List, Any
from transformers import pipeline
import google.generativeai as genai
from backend.app.core.config import settings


class SimpleL LMBaseline:
    """Baseline 1: Single LLM call with basic prompt"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    def analyze(self, post_text: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Single LLM call for analysis"""
        
        prompt = f"""
        Analyze this social media post about Baguio City:
        
        POST:
        {post_text}
        
        FOCUS AREAS: {', '.join(focus_areas)}
        
        Provide a JSON response with:
        1. sentiment: "positive", "negative", or "neutral"
        2. themes: list of relevant themes from {focus_areas}
        3. insights: list of 3-5 key insights
        4. credibility: "high", "medium", or "low"
        5. actionable_recommendations: list of concrete actions
        
        Return ONLY valid JSON, no markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "themes": result.get("themes", []),
                "insights": result.get("insights", []),
                "credibility": result.get("credibility", "medium"),
                "recommendations": result.get("actionable_recommendations", []),
                "source": "simple_llm"
            }
        except Exception as e:
            print(f"Error in Simple LLM: {e}")
            return {
                "sentiment": "neutral",
                "themes": [],
                "insights": [],
                "credibility": "low",
                "recommendations": [],
                "source": "simple_llm",
                "error": str(e)
            }


class RoBERTaBaseline:
    """Baseline 2: RoBERTa sentiment classifier only"""
    
    def __init__(self):
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment",
            max_length=512,
            truncation=True
        )
    
    def analyze(self, post_text: str, focus_areas: List[str]) -> Dict[str, Any]:
        """RoBERTa sentiment only, no themes or insights"""
        
        try:
            result = self.sentiment_analyzer(post_text)[0]
            
            # Map RoBERTa labels to our format
            label_map = {
                "LABEL_0": "negative",
                "LABEL_1": "neutral",
                "LABEL_2": "positive"
            }
            
            sentiment = label_map.get(result["label"], "neutral")
            
            return {
                "sentiment": sentiment,
                "confidence": result["score"],
                "themes": [],  # No theme detection
                "insights": [],  # No insights
                "credibility": "unknown",  # No credibility check
                "recommendations": [],  # No recommendations
                "source": "roberta_only"
            }
        except Exception as e:
            print(f"Error in RoBERTa: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "themes": [],
                "insights": [],
                "credibility": "unknown",
                "recommendations": [],
                "source": "roberta_only",
                "error": str(e)
            }


class RAGOnlyBaseline:
    """Baseline 3: Simple RAG without multi-agent orchestration"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    def analyze(self, post_text: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Simple RAG: retrieve + single LLM call"""
        
        try:
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(post_text, k=5)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            prompt = f"""
            CONTEXT (from past analyses):
            {context}
            
            NEW POST:
            {post_text}
            
            FOCUS AREAS: {', '.join(focus_areas)}
            
            Analyze the new post using the context. Provide JSON with:
            1. sentiment
            2. themes
            3. insights
            4. credibility
            5. actionable_recommendations
            
            Return ONLY valid JSON.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "themes": result.get("themes", []),
                "insights": result.get("insights", []),
                "credibility": result.get("credibility", "medium"),
                "recommendations": result.get("actionable_recommendations", []),
                "source": "rag_only",
                "retrieved_docs": len(docs)
            }
        except Exception as e:
            print(f"Error in RAG-Only: {e}")
            return {
                "sentiment": "neutral",
                "themes": [],
                "insights": [],
                "credibility": "low",
                "recommendations": [],
                "source": "rag_only",
                "error": str(e)
            }


class BaselineRunner:
    """Runs all baselines on evaluation dataset"""
    
    def __init__(self, vector_store=None):
        self.simple_llm = SimpleLLMBaseline()
        self.roberta = RoBERTaBaseline()
        self.rag_only = RAGOnlyBaseline(vector_store) if vector_store else None
    
    def run_all_baselines(
        self,
        dataset: List[Dict[str, Any]],
        output_dir: str = "results/baselines"
    ):
        """Run all baselines on dataset"""
        
        results = {
            "simple_llm": [],
            "roberta_only": [],
            "rag_only": []
        }
        
        print(f"Running baselines on {len(dataset)} samples...")
        
        for i, sample in enumerate(dataset):
            post_text = sample["text"]
            focus_areas = sample.get("focus_areas", ["infrastructure", "health", "safety"])
            
            print(f"\nSample {i+1}/{len(dataset)}")
            
            # Baseline 1: Simple LLM
            print("  Running Simple LLM...")
            start = time.time()
            simple_result = self.simple_llm.analyze(post_text, focus_areas)
            simple_result["latency"] = time.time() - start
            simple_result["sample_id"] = sample.get("id", i)
            results["simple_llm"].append(simple_result)
            
            # Baseline 2: RoBERTa
            print("  Running RoBERTa...")
            start = time.time()
            roberta_result = self.roberta.analyze(post_text, focus_areas)
            roberta_result["latency"] = time.time() - start
            roberta_result["sample_id"] = sample.get("id", i)
            results["roberta_only"].append(roberta_result)
            
            # Baseline 3: RAG-Only (if available)
            if self.rag_only:
                print("  Running RAG-Only...")
                start = time.time()
                rag_result = self.rag_only.analyze(post_text, focus_areas)
                rag_result["latency"] = time.time() - start
                rag_result["sample_id"] = sample.get("id", i)
                results["rag_only"].append(rag_result)
        
        # Save results
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for baseline_name, baseline_results in results.items():
            if baseline_results:
                output_path = f"{output_dir}/{baseline_name}.json"
                with open(output_path, "w") as f:
                    json.dump(baseline_results, f, indent=2)
                print(f"\nSaved {baseline_name} results to {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("BASELINE SUMMARY")
        print("="*60)
        
        for baseline_name, baseline_results in results.items():
            if baseline_results:
                avg_latency = sum(r["latency"] for r in baseline_results) / len(baseline_results)
                print(f"\n{baseline_name.upper()}:")
                print(f"  Samples: {len(baseline_results)}")
                print(f"  Avg Latency: {avg_latency:.2f}s")
        
        return results


# Example usage
if __name__ == "__main__":
    # Load evaluation dataset
    with open("data/ground_truth.json", "r") as f:
        dataset = json.load(f)
    
    # Run baselines
    runner = BaselineRunner()
    results = runner.run_all_baselines(dataset)
    
    print("\nBaseline evaluation complete!")
