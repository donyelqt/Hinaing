"""Schemas for sentiment snapshot generation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


def _sanitize_text(text: str | None) -> str:
    """Remove Unicode surrogates that break JSON serialization."""
    if not text:
        return ""
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', text)
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned


class SnapshotRequest(BaseModel):
    """Payload coming from the frontend sentiment generator."""

    platforms: list[str] = Field(default_factory=list, description="Selected data sources")
    time_window: str = Field(default="24h", description="Relative time window filter")
    focus_areas: list[str] = Field(default_factory=list, description="User-selected themes")
    include_alerts: bool = True
    mode: str = Field(default="full", description="Analysis mode: full, sentiment, or credibility")
    include_sentiment: bool = Field(default=True, description="Include sentiment analysis")
    include_credibility: bool = Field(default=True, description="Include credibility scoring")


class WebDocument(BaseModel):
    """Minimal representation of a fetched web/post document."""

    title: str
    snippet: str
    url: HttpUrl | None = None
    published_at: datetime | None = None
    sentiment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "snippet", mode="before")
    @classmethod
    def sanitize_text_fields(cls, value: str | None) -> str:
        """Remove surrogates from text fields to prevent JSON serialization errors."""
        return _sanitize_text(value) if value else ""

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

    @field_validator("label", "summary", mode="before")
    @classmethod
    def sanitize_text_fields(cls, value: str | None) -> str:
        return _sanitize_text(value) if value else ""


class Insight(BaseModel):
    category: str
    title: str
    detail: str
    evidence: list[str] = Field(default_factory=list)

    @field_validator("category", "title", "detail", mode="before")
    @classmethod
    def sanitize_text_fields(cls, value: str | None) -> str:
        return _sanitize_text(value) if value else ""

    @field_validator("evidence", mode="before")
    @classmethod
    def sanitize_evidence(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        return [_sanitize_text(v) for v in value if v]


class SnapshotResponse(BaseModel):
    overall_sentiment: SentimentBreakdown
    actionable_insights: list[Insight]
    alerts: list[str] | None = None
    sources: list[WebDocument] | None = None

    @field_validator("alerts", mode="before")
    @classmethod
    def sanitize_alerts(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return value
        return [_sanitize_text(v) for v in value if v]
