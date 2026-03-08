"""
Final Verification: Ensure No Model Fallback During Evaluation

This script runs a mini-evaluation (10 samples) with detailed logging
to prove that each model is actually being used without fallbacks.

Usage:
    python -m scripts.verify_no_fallback
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Enable DEBUG logging to see model confirmations
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

from app.services.llm.groq_provider import get_groq_provider, clear_groq_cache


async def verify_no_fallback():
    """Run mini-evaluation with detailed logging to verify no fallbacks."""
    
    print("=" * 70)
    print("FALLBACK VERIFICATION TEST")
    print("=" * 70)
    print("\nRunning mini-evaluation with 3 samples per model...")
    print("Watch for '[Groq] Confirmed using model:' messages\n")
    
    # Clear cache
    clear_groq_cache()
    
    # Test samples
    samples = [
        "Traffic is terrible in Session Road today",
        "City hall meeting scheduled for tomorrow",
        "Panagbenga festival was amazing this year!",
    ]
    
    models = [
        ("llama-3.3-70b-versatile", "Llama-3.3-70B"),
        ("meta-llama/llama-4-scout-17b-16e-instruct", "Llama-4-Scout"),
        ("qwen/qwen3-32b", "Qwen3-32b"),
    ]
    
    results = {}
    
    for model_id, model_name in models:
        print(f"\n{'=' * 70}")
        print(f"Testing: {model_name}")
        print(f"Model ID: {model_id}")
        print(f"{'=' * 70}\n")
        
        provider = get_groq_provider(model_id)
        predictions = []
        
        for i, sample in enumerate(samples, 1):
            print(f"Sample {i}/3: {sample[:50]}...")
            
            try:
                response = await provider.generate(
                    prompt=f"Classify sentiment as positive, negative, or neutral: {sample}",
                    system_prompt="You are a sentiment classifier. Return only the label.",
                    temperature=0.0,
                    max_tokens=10,
                )
                
                sentiment = response.strip().lower()
                if "positive" in sentiment:
                    pred = "positive"
                elif "negative" in sentiment:
                    pred = "negative"
                else:
                    pred = "neutral"
                
                predictions.append(pred)
                print(f"  → Prediction: {pred}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                predictions.append("error")
        
        results[model_name] = predictions
        print(f"\n✓ {model_name} completed: {predictions}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    print("\nPredictions by model:")
    for model_name, preds in results.items():
        print(f"  {model_name}: {preds}")
    
    # Check for suspicious patterns
    print("\n🔍 Checking for suspicious patterns...")
    
    # If all models give identical predictions, might be fallback
    all_preds = list(results.values())
    if len(set(tuple(p) for p in all_preds)) == 1:
        print("⚠️  WARNING: All models gave identical predictions!")
        print("   This could indicate fallback to same model.")
        print("   Check DEBUG logs above for '[Groq] Confirmed using model:' messages")
    else:
        print("✅ Models gave different predictions - likely using correct models")
    
    # Check logs for fallback warnings
    print("\n📋 Check the DEBUG logs above for:")
    print("   ✓ '[Groq] Confirmed using model: <model_name>'")
    print("   ❌ '[Groq] Model mismatch!' (should NOT appear)")
    print("   ❌ '[Groq] Attempting fallback to Gemini' (should NOT appear)")
    
    print("\n" + "=" * 70)
    print("If you see '[Groq] Confirmed using model:' for each model,")
    print("then evaluation is using correct models without fallbacks.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_no_fallback())
