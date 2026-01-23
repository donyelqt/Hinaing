"""Test script to measure credibility agent performance improvements."""
import asyncio
import time
import logging
from app.services.agents.credibility_agent import get_credibility_agent
from app.schemas.snapshot import WebDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_credibility_agent():
    """Test the credibility agent performance with dummy documents."""
    
    # Create dummy documents similar to real ones
    dummy_docs = [
        WebDocument(
            id=f"doc_{i}",
            title=f"Test Document {i}: Baguio City infrastructure project",
            snippet="This is a test document about Baguio City infrastructure development. "
                   "The city government announced plans to improve public transportation.",
            url=f"https://{['inquirer.net', 'gmanetwork.com', 'pia.gov.ph', 'facebook.com'][i % 4]}/news/story{i}",
            published_at=None,
            metadata={}
        )
        for i in range(20)
    ]
    
    logger.info(f"Testing credibility agent with {len(dummy_docs)} documents")
    
    # Initialize credibility agent
    agent = get_credibility_agent()
    
    # Run performance test
    start_time = time.time()
    
    try:
        results = await agent.run(dummy_docs)
        logger.info(f"Successfully processed {len(results)} documents")
        
        # Log key metrics
        scores = [doc.metadata.get('credibility_score', 0) for doc in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        verification_statuses = [doc.metadata.get('tavily_verification_status', 'unknown') for doc in results]
        status_counts = {}
        for status in verification_statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.info(f"Average credibility score: {avg_score:.3f}")
        logger.info(f"Verification status distribution: {status_counts}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"{'='*60}")
    logger.info(f"Performance Test Results:")
    logger.info(f"{'='*60}")
    logger.info(f"Total documents: {len(dummy_docs)}")
    logger.info(f"Total time: {total_time:.2f} seconds")
    logger.info(f"Time per document: {total_time/len(dummy_docs):.2f} seconds")
    
    return total_time

if __name__ == "__main__":
    # Run the test
    logger.info("Starting credibility agent performance test...")
    total_time = asyncio.run(test_credibility_agent())
    
    # Evaluate performance
    if total_time < 10:
        logger.info("\n✅ Excellent performance!")
    elif total_time < 20:
        logger.info("\n👍 Good performance")
    elif total_time < 30:
        logger.info("\n⚠️  Acceptable performance")
    else:
        logger.info("\n🚩 Performance needs improvement")