"""Data models for RAG system."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class DocumentChunk:
    """A semantic chunk of a document for RAG retrieval."""
    
    chunk_id: str
    source_url: str
    source_title: str
    content: str
    chunk_index: int
    total_chunks: int
    published_at: datetime | None
    metadata: dict[str, Any]
    embedding: list[float] | None = None


class AugmentedContext(BaseModel):
    """RAG-augmented context for theme analysis."""
    
    theme: str = Field(description="Theme label")
    relevant_chunks: list[DocumentChunk] = Field(description="Top-k relevant chunks")
    context_summary: str = Field(description="Condensed context summary")
    temporal_range: tuple[datetime, datetime] | None = Field(description="Time range of context")
    spatial_context: str = Field(default="Baguio City", description="Spatial context")
    relevance_scores: list[float] = Field(description="Relevance score for each chunk")
    total_documents: int = Field(description="Total source documents")
    
    class Config:
        arbitrary_types_allowed = True


class RetrievalResult(BaseModel):
    """Result from vector similarity search."""
    
    chunk: DocumentChunk
    score: float
    rank: int
    
    class Config:
        arbitrary_types_allowed = True
