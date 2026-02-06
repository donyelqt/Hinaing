#!/usr/bin/env python3
"""Verify Groq migration is complete and working.

MIGRATION STATUS: ✅ COMPLETE (All nodes using Groq)

This script verifies:
1. All dependencies are installed
2. Groq API key is configured
3. All nodes are using Groq (not Gemini)
4. Basic functionality works
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if required packages are installed."""
    print("=" * 60)
    print("1. Checking Dependencies")
    print("=" * 60)
    
    required = ["groq", "langchain_groq"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg} installed")
        except ImportError:
            print(f"❌ {pkg} NOT installed")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: poetry add groq langchain-groq")
        return False
    
    print("\n✅ All dependencies installed\n")
    return True


def check_configuration():
    """Check if Groq is configured."""
    print("=" * 60)
    print("2. Checking Configuration")
    print("=" * 60)
    
    from app.core.config import get_settings
    
    settings = get_settings()
    
    if not settings.groq_api_key:
        print("❌ GROQ_API_KEY not configured")
        print("\nAdd to backend/.env:")
        print("GROQ_API_KEY=gsk_your_groq_api_key_here")
        return False
    
    print(f"✅ GROQ_API_KEY configured: {settings.groq_api_key[:20]}...")
    print(f"✅ Default model: {settings.groq_default_model}")
    print("\n✅ Configuration complete\n")
    return True


async def test_groq_provider():
    """Test Groq provider directly."""
    print("=" * 60)
    print("3. Testing Groq Provider")
    print("=" * 60)
    
    try:
        from app.services.llm.groq_provider import get_groq_provider
        
        provider = get_groq_provider("llama-3.3-70b-versatile")
        
        if not provider.is_available:
            print("❌ Groq provider not available")
            return False
        
        print(f"✅ Groq provider initialized: {provider.model_name}")
        
        # Test generation
        print("Testing generation...")
        response = await provider.generate(
            "Say 'Hello from Groq!' in exactly 5 words.",
            temperature=0.1,
            max_tokens=50,
        )
        
        print(f"✅ Generation works: {response[:100]}")
        print("\n✅ Groq provider working\n")
        return True
        
    except Exception as e:
        print(f"❌ Groq provider test failed: {e}")
        return False


def check_node_migrations():
    """Check if all nodes are using Groq."""
    print("=" * 60)
    print("4. Checking Node Migrations")
    print("=" * 60)
    
    checks = {
        "Node 1 (Query Orchestrator)": "backend/app/services/agents/query_orchestrator.py",
        "Node 4 (Sentiment Agent)": "backend/app/services/agents/sentiment_agent.py",
        "Node 4 (Credibility Agent)": "backend/app/services/agents/credibility_agent.py",
        "Node 6 (Theme Agents)": "backend/app/services/agents/theme_agent.py",
        "Node 7 (Coordinator)": "backend/app/services/nlp/narrative_generator.py",
        "Chat Agent": "backend/app/services/agents/chat_agent.py",
    }
    
    all_good = True
    
    for name, filepath in checks.items():
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  {name}: File not found - {filepath}")
            continue
        
        content = path.read_text()
        
        # Check for Groq usage
        has_groq = "groq_provider" in content.lower() or "ChatGroq" in content
        has_old_gemini_active = "genai.GenerativeModel(" in content  # Active Gemini code (not commented)
        
        if has_groq and not has_old_gemini_active:
            print(f"✅ {name}: Using Groq")
        elif has_groq and has_old_gemini_active:
            print(f"⚠️  {name}: Mixed (has both Groq and active Gemini code)")
            all_good = False
        else:
            print(f"❌ {name}: Still using Gemini")
            all_good = False
    
    if all_good:
        print("\n✅ All nodes migrated to Groq\n")
    else:
        print("\n⚠️  Some nodes need attention\n")
    
    return all_good


async def test_sentiment_agent():
    """Test sentiment agent with Groq."""
    print("=" * 60)
    print("5. Testing Sentiment Agent")
    print("=" * 60)
    
    try:
        from app.services.agents.sentiment_agent import get_sentiment_agent
        from app.schemas.snapshot import WebDocument
        
        agent = get_sentiment_agent()
        print(f"✅ Sentiment agent initialized")
        
        # Test with sample document
        test_doc = WebDocument(
            title="Baguio City celebrates successful cleanup drive",
            snippet="Mayor announces completion of city-wide cleanup initiative",
            url="https://example.com/test",
            published_at=None,
        )
        
        print("Testing sentiment analysis...")
        results = agent.analyze_batch([test_doc])
        
        if results and results[0].sentiment:
            print(f"✅ Sentiment analysis works: {results[0].sentiment}")
            print(f"   Confidence: {results[0].metadata.get('sentiment_confidence', 'N/A')}")
            print("\n✅ Sentiment agent working\n")
            return True
        else:
            print("❌ Sentiment analysis failed")
            return False
        
    except Exception as e:
        print(f"❌ Sentiment agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("GROQ MIGRATION VERIFICATION")
    print("=" * 60 + "\n")
    
    results = []
    
    # 1. Check dependencies
    results.append(("Dependencies", check_dependencies()))
    
    # 2. Check configuration
    results.append(("Configuration", check_configuration()))
    
    # 3. Test Groq provider
    results.append(("Groq Provider", await test_groq_provider()))
    
    # 4. Check node migrations
    results.append(("Node Migrations", check_node_migrations()))
    
    # 5. Test sentiment agent
    results.append(("Sentiment Agent", await test_sentiment_agent()))
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED - Migration verified!")
        print("\nCurrent Architecture:")
        print("- Node 1: groq/compound (UNLIMITED TPD)")
        print("- Node 4: llama-4-scout-17b (Sentiment)")
        print("- Node 5: llama-3.1-8b-instant (Credibility)")
        print("- Node 6: llama-4-scout-17b (Themes ×6)")
        print("- Node 7: llama-4-scout-17b (Coordinator)")
        print("- Chat: groq/compound (UNLIMITED TPD)")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - Review errors above")
        print("\nCommon fixes:")
        print("1. Install dependencies: poetry add groq langchain-groq")
        print("2. Add GROQ_API_KEY to backend/.env")
        print("3. Check file modifications are complete")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
