"""Fix Qdrant indexes for focus_area and topic filtering.

Run this script if you see errors like:
"Index required but not found for 'focus_area'"

This will create the necessary keyword indexes in Qdrant.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag.vector_store import get_vector_store

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Recreate Qdrant payload indexes."""
    logger.info("=" * 60)
    logger.info("Qdrant Index Fix Script")
    logger.info("=" * 60)
    
    try:
        # Get vector store instance
        logger.info("Connecting to Qdrant...")
        vector_store = get_vector_store()
        
        # Get current stats
        stats = vector_store.get_stats()
        logger.info(f"Collection: {stats.get('name')}")
        logger.info(f"Documents: {stats.get('vector_count', 0)}")
        logger.info(f"Cloud mode: {stats.get('is_cloud', False)}")
        
        # Recreate indexes
        logger.info("\nRecreating payload indexes...")
        vector_store.recreate_indexes()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Index fix complete!")
        logger.info("=" * 60)
        logger.info("\nIndexes created:")
        logger.info("  - focus_area (keyword)")
        logger.info("  - topic (keyword)")
        logger.info("\nYou can now use focus_area_filter in searches.")
        
    except Exception as e:
        logger.error(f"\n✗ Failed to fix indexes: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
