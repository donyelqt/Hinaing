from app.services.rag.vector_store import get_vector_store
import asyncio

async def check():
    print("Initializing Vector Store...")
    vs = get_vector_store()
    stats = vs.get_stats()
    print(f"DB Stats: {stats}")
    
    # Try a broad search
    print("Testing Search for 'safety'...")
    results = await vs.search("safety", k=5)
    print(f"Found {len(results)} results.")
    for res in results:
        print(f" - [{res.score:.2f}] {res.chunk.source_title}")

if __name__ == "__main__":
    asyncio.run(check())
