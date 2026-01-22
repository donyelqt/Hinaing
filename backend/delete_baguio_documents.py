#!/usr/bin/env python3
"""Script to delete the Baguio documents collection from Qdrant."""

import sys
import os
import asyncio

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag.vector_store import get_vector_store

def main():
    """Delete the Baguio documents collection."""
    try:
        # Initialize the vector store
        vector_store = get_vector_store()
        
        # Delete the Baguio documents collection
        asyncio.run(vector_store.clear())
        
        # Verify that the collection was deleted
        stats = vector_store.get_stats()
        if stats.get("vector_count", 0) == 0:
            print("Baguio documents collection deleted successfully.")
        else:
            print("Error: Baguio documents collection still exists.")
            sys.exit(1)
    except Exception as e:
        print(f"Error deleting Baguio documents collection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()