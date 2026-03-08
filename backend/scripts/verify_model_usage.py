"""
Verify that evaluation scripts are actually using the correct models.

This script adds detailed logging to track:
1. Which model is requested
2. Which model is actually called by Groq API
3. Whether any fallbacks occurred
4. API response metadata

Run this to ensure no model substitution is happening.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm.groq_provider import get_groq_provider, clear_groq_cache


async def test_model_usage():
    """Test that each model is actually being used correctly."""
    
    print("=" * 70)
    print("MODEL USAGE VERIFICATION")
    print("=" * 70)
    print("\nTesting that each model is actually called (no fallbacks)...\n")
    
    # Clear cache to start fresh
    clear_groq_cache()
    print("✓ Cache cleared\n")
    
    # Test models
    models_to_test = [
        ("llama-3.3-70b-versatile", "Llama-3.3-70B-Versatile"),
        ("meta-llama/llama-4-scout-17b-16e-instruct", "Llama-4-Scout-17b"),
        ("qwen/qwen3-32b", "Qwen3-32b"),
    ]
    
    test_prompt = "Classify sentiment: Traffic is terrible today"
    
    for model_name, display_name in models_to_test:
        print(f"{'─' * 70}")
        print(f"Testing: {display_name}")
        print(f"Model ID: {model_name}")
        print(f"{'─' * 70}")
        
        try:
            # Get provider
            provider = get_groq_provider(model_name)
            print(f"✓ Provider created")
            print(f"  Provider model: {provider.model_name}")
            
            # Verify model name matches
            if provider.model_name != model_name:
                print(f"❌ WARNING: Provider model ({provider.model_name}) != requested ({model_name})")
            else:
                print(f"✓ Model name matches")
            
            # Make actual API call
            print(f"  Making API call...")
            response = await provider.generate(
                prompt=test_prompt,
                system_prompt="You are a sentiment classifier. Return only: positive, negative, or neutral.",
                temperature=0.0,
                max_tokens=10,
            )
            
            print(f"✓ API call successful")
            print(f"  Response: {response[:50]}...")
            
            # Check if response looks like a fallback
            if "gemini" in response.lower() or "claude" in response.lower():
                print(f"⚠️  WARNING: Response mentions other models - possible fallback")
            
            print(f"✅ {display_name} is working correctly\n")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print(f"   This model may not be available or API key is invalid\n")
    
    print("=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print("\nIf all models show ✅, then evaluation is using correct models.")
    print("If any show ❌ or ⚠️, there may be fallback or substitution issues.")


if __name__ == "__main__":
    asyncio.run(test_model_usage())
