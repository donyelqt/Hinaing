#!/usr/bin/env python3
"""Initialize Emerging Concerns Memory in Qdrant.

Creates 6 isolated collections and populates them with default concerns.
Run this once to set up the memory infrastructure.

Usage:
    python init_concerns_memory.py
"""
import logging
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

from app.services.agents.concerns_memory import (
    EmergingConcernsMemory,
    FOCUS_AREA_COLLECTIONS,
    DEFAULT_EMERGING_CONCERNS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Initialize all 6 concern collections in Qdrant."""
    print("=" * 60)
    print("INITIALIZING EMERGING CONCERNS MEMORY")
    print("=" * 60)
    
    memory = EmergingConcernsMemory()
    
    # Show which collections will be created
    print("\n📦 Collections to create:")
    for area, collection in FOCUS_AREA_COLLECTIONS.items():
        print(f"   - {collection}")
    
    # Step 1: Create all collections
    print("\n🔧 Creating collections...")
    for focus_area in FOCUS_AREA_COLLECTIONS.keys():
        try:
            collection_name = memory._ensure_collection(focus_area)
            print(f"   ✅ Created: {collection_name}")
        except Exception as e:
            print(f"   ❌ Failed: {focus_area} - {e}")
    
    # Step 2: Store default concerns
    print("\n💾 Storing default concerns...")
    try:
        stored = memory.store_concerns(
            concerns=DEFAULT_EMERGING_CONCERNS,
            source="default"
        )
        
        print("   📊 Storage results:")
        for area, count in stored.items():
            collection = FOCUS_AREA_COLLECTIONS.get(area, "unknown")
            print(f"      - {collection}: {count} clusters")
            
    except Exception as e:
        print(f"   ❌ Failed to store concerns: {e}")
        return
    
    # Step 3: Verify with stats
    print("\n📈 Verifying collections...")
    try:
        stats = memory.get_stats()
        print("   📊 Collection stats:")
        for area, stat in stats.items():
            if "error" in stat:
                print(f"      - {area}: ERROR - {stat['error']}")
            else:
                print(f"      - {area}: {stat['points_count']} points")
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")
    
    print("\n" + "=" * 60)
    print("✅ INITIALIZATION COMPLETE")
    print("=" * 60)
    print("""
The system will now:
1. Check memory (Qdrant) first for recent concerns
2. Only call LLM if memory is empty or stale (> 7 days)
3. Store new LLM concerns for future use
""")


if __name__ == "__main__":
    main()
