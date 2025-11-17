from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

SentimentLabel = Literal["positive", "neutral", "negative"]


class SourcePlatform(BaseModel):
    name: Literal["facebook", "reddit"]
    identifier: str


class LocationContext(BaseModel):
    city: str = "Baguio"
    region: Optional[str] = "Cordillera Administrative Region"
    country: str = "Philippines"


class RawSocialPost(BaseModel):
    platform: SourcePlatform
    post_id: str
    author: str
    content: str
    url: Optional[HttpUrl] = None
    created_at: datetime
    location: Optional[LocationContext] = None
    metadata: dict = Field(default_factory=dict)


class ClassifiedSentiment(BaseModel):
    post: RawSocialPost
    sentiment: SentimentLabel
    confidence: float | None = None
    themes: list[str] = Field(default_factory=list)
    actionable_insights: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
