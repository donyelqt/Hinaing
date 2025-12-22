"""
BCB-100 Dataset Builder (Baguio Civic Benchmark)

This script scrapes real data from Reddit/Facebook via the RetrievalAgent 
and freezes it into a JSON file. This ensures our thesis evaluation 
is reproducible and not dependent on live internet changes.

Categories:
- Infrastructure
- Health
- Safety
- Tourism
- Economy

Output: backend/benchmarks/data/bcb_100_raw.json
"""

import asyncio
import json
import os
import logging
from datetime import datetime

# Adjust path to import backend modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables

from app.services.insights.agents import RetrievalAgent
from app.schemas.snapshot import SnapshotRequest

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dataset_builder")

CATEGORIES = ["infrastructure", "health", "safety", "tourism", "economy"]
TARGET_PER_CATEGORY = 20

async def build_dataset():
    agent = RetrievalAgent()
    dataset = []
    
    logger.info("🚀 Starting BCB-100 Dataset Collection...")
    
    for category in CATEGORIES:
        logger.info(f"📥 Collecting category: {category}...")
        
        # Create a request for this specific category
        request = SnapshotRequest(
            focus_areas=[category],
            time_window="7d", 
            platforms=["web"] # Scrape LangSearch ONLY
        )
        
        # We manually construct a 'query_plan' object structure 
        # because RetrievalAgent usually expects one for Reddit
        # Mocking a simple plan to guide the diverse search
        class MockTask:
            def __init__(self, q, t):
                self.query = q
                self.topic = t

        class MockPlan:
            queries = [
                MockTask(f"Baguio City {category} issues", "general"),
                MockTask(f"Baguio City {category} complaints", "complaints"),
                MockTask(f"Baguio City {category} news", "news")
            ]
        
        try:
            # 1. Fetch real documents
            docs = await agent.run(request, query_plan=MockPlan())
            
            # 2. Filter & Clean
            valid_docs = []
            for doc in docs:
                # Basic validation
                if not doc.snippet or len(doc.snippet) < 50:
                    continue
                valid_docs.append(doc.model_dump())
            
            # 3. Select top 20
            selected = valid_docs[:TARGET_PER_CATEGORY]
            logger.info(f"   ✅ Collected {len(selected)} valid docs for {category}")
            
            # 4. Add to dataset
            for item in selected:
                dataset.append({
                    "id": f"{category}_{datetime.now().microsecond}",
                    "category": category,
                    "source_url": item.get("url"),
                    "title": item.get("title"),
                    "text": item.get("snippet"),
                    "published_at": str(item.get("published_at")),
                    "metadata": item.get("metadata"),
                    # These fields will be manually labeled later
                    "gold_sentiment": None,
                    "gold_insight": None
                })
                
        except Exception as e:
            logger.error(f"❌ Failed category {category}: {e}")

    # Save to file
    output_path = "backend/benchmarks/data/bcb_100_raw.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    logger.info(f"🎉 Dataset saved to {output_path}")
    logger.info(f"Total Records: {len(dataset)}")

if __name__ == "__main__":
    asyncio.run(build_dataset())
