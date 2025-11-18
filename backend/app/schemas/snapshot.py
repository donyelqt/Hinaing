"""Schemas for sentiment snapshot generation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SnapshotRequest(BaseModel):
    """Payload coming from the frontend sentiment generator."""

    platforms: list[str] = Field(default_factory=list, description="Selected data sources")
    time_window: str = Field(default="24h", description="Relative time window filter")
    focus_areas: list[str] = Field(default_factory=list, description="User-selected themes")
    include_alerts: bool = True


class WebDocument(BaseModel):
    """Minimal representation of a fetched web/post document."""

    title: str
    snippet: str
    url: HttpUrl | None = None
    published_at: datetime | None = None
    sentiment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, value: str | None) -> str | None:
        if value is None:
            return value
        lowered = value.lower()
        if lowered not in {"positive", "neutral", "negative"}:
            raise ValueError("sentiment must be positive, neutral, or negative")
        return lowered


class SentimentBreakdown(BaseModel):
    label: str
    summary: str
    scores: dict[str, float]


class Insight(BaseModel):
    category: str
    title: str
    detail: str
    evidence: list[str] = Field(default_factory=list)


class SnapshotResponse(BaseModel):
    overall_sentiment: SentimentBreakdown
    actionable_insights: list[Insight]
    alerts: list[str] | None = None
    sources: list[WebDocument] | None = None
