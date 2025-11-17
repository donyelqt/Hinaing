"""Reddit ingestion utilities.

Implements the interface to fetch Reddit submissions/comments relevant to the
Baguio locale. Currently mocked for scaffolding purposes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ...schemas.social import LocationContext, RawSocialPost, SourcePlatform


async def fetch_public_posts(region_keywords: Iterable[str]) -> list[RawSocialPost]:
    """Fetch Reddit posts matching the provided keywords.

    TODO: Hook into Reddit API (e.g., via PRAW or Reddit's REST endpoints).
    """
    sample_posts = [
        RawSocialPost(
            platform=SourcePlatform(name="reddit", identifier="r/Baguio"),
            post_id="reddit_001",
            author="u/baguiolocal",
            content="Water interruption again in Upper Session. Any updates from"
            " the city?",
            created_at=datetime.utcnow(),
            url=None,
            location=LocationContext(),
            metadata={"keywords": list(region_keywords)},
        )
    ]
    return sample_posts
