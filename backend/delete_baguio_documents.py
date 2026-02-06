#!/usr/bin/env python3
"""Script to delete ALL documents from the Baguio documents collection in Qdrant Cloud."""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import QdrantClient
from app.core.config import get_settings

def main():
    """Delete all points from the Baguio documents collection."""
    try:
        settings = get_settings()
        
        # Connect to Qdrant Cloud
        if not settings.qdrant_url:
            print("Error: QDRANT_URL not configured in .env")
            sys.exit(1)
        
        print(f"Connecting to Qdrant Cloud: {settings.qdrant_url[:60]}...")
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30.0,
        )
        
        collection_name = "baguio_documents"
        
        # Get current count
        collection_info = client.get_collection(collection_name)
        initial_count = collection_info.points_count
        print(f"Current points in collection: {initial_count}")
        
        if initial_count == 0:
            print("Collection is already empty.")
            return
        
        # Delete ALL points from the collection
        print(f"Deleting all {initial_count} points from '{collection_name}'...")
        
        # Method 1: Delete by filter (delete everything)
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        
        # This deletes ALL points (no filter = match all)
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    # Match any point (this will match everything)
                ]
            )
        )
        
        # Alternative: Delete the entire collection and recreate it
        # This is faster for large collections
        print("Recreating collection to ensure complete deletion...")
        client.delete_collection(collection_name)
        
        # Recreate the collection
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # BGE-small embedding dimension
                distance=Distance.COSINE
            )
        )
        
        # Verify deletion
        collection_info = client.get_collection(collection_name)
        final_count = collection_info.points_count
        
        print(f"\n✅ Success!")
        print(f"   Before: {initial_count} points")
        print(f"   After: {final_count} points")
        print(f"   Deleted: {initial_count - final_count} points")
        
        if final_count == 0:
            print("\n🎉 All Baguio documents deleted successfully!")
        else:
            print(f"\n⚠️  Warning: {final_count} points still remain")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error deleting Baguio documents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()