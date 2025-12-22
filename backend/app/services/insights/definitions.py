"""State and Configuration definitions for the Insights Graph."""
from __future__ import annotations

import os
import asyncio
from typing import TypedDict, Any
from ...schemas.snapshot import (
    Insight,
    SnapshotRequest,
    SnapshotResponse,
    WebDocument,
)
from ...schemas.rag import AugmentedContext
from ...schemas.query import QueryPlan

class SnapshotState(TypedDict, total=False):
    """State management for the 7-Node Graph."""
    request: SnapshotRequest
    documents: list[WebDocument]  # Combined External + Internal
    internal_documents: list[WebDocument] # Internal Memory Recall
    external_documents: list[WebDocument] # Fresh External Retrieval
    enriched: list[WebDocument]
    theme_documents: dict[str, list[WebDocument]]
    augmented_contexts: dict[str, AugmentedContext]
    theme_insights: list[Insight]
    credibility_notes: dict[str, float]
    retrieval_plan: QueryPlan
    snapshot: SnapshotResponse
    rag_chunks_stored: int
    rag_relevance_scores: list[float]

# Concurrency configurations - Increased for 100x CTO Performance
_node4_max_concurrency = max(1, int(os.getenv("NODE4_MAX_CONCURRENCY", "2")))
node4_semaphore = asyncio.Semaphore(_node4_max_concurrency)
_node4_ml_max_concurrency = max(1, int(os.getenv("NODE4_ML_MAX_CONCURRENCY", "2")))
node4_ml_semaphore = asyncio.Semaphore(_node4_ml_max_concurrency)

# Theme Definitions
THEME_GROUPS = {
    "infrastructure": {
        "label": "Infrastructure",
        "focus_values": {"infrastructure"},
        "keywords": {
            "road", "traffic", "water", "power", "infrastructure", "bridge", "construction",
            "kennon", "session road", "bgh", "building", "outage", "substandard",
        },
    },
    "health": {
        "label": "Health & Wellness",
        "focus_values": {"health"},
        "keywords": {
            "hospital", "clinic", "health", "dengue", "covid", "medicine", "vaccine", "wellness",
            "bgh", "baguio general", "disease", "medical", "patient",
        },
    },
    "safety": {
        "label": "Public Safety",
        "focus_values": {"safety"},
        "keywords": {
            "crime", "police", "fire", "landslide", "safety", "accident", "emergency", "security",
            "flood", "walkout", "protest", "rally", "incident", "student walkout", "youth rally",
        },
    },
    "tourism": {
        "label": "Tourism & Events",
        "focus_values": {"tourism"},
        "keywords": {
            "tourism", "tourist", "hotel", "festival", "event", "panagbenga", "visitor",
            "burnham", "overcrowding", "mines view", "camp john hay", "wright park",
        },
    },
    "economy": {
        "label": "Business & Economy",
        "focus_values": {"economy", "business"},
        "keywords": {
            "market", "vendor", "livelihood", "economy", "business", "investment", "price",
            "mallification", "sm prime", "public market", "redevelopment", "displacement",
            "walkout", "protest", "students protest", "youth protest", "schools walkout",
        },
    },
    "environment": {
        "label": "Environment",
        "focus_values": {"environment"},
        "keywords": {
            "garbage", "pollution", "environment", "rain", "waste", "tree", "green",
            "air quality", "flooding", "climate",
        },
    },
}
