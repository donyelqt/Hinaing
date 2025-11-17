"""Facebook ingestion utilities.

These functions define the interfaces used to pull public posts from Facebook
Graph API. For now, the implementation is mocked so that the rest of the system
can be exercised before API credentials are wired in.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from ...schemas.social import LocationContext, RawSocialPost, SourcePlatform


async def fetch_public_posts(region_keywords: Iterable[str]) -> list[RawSocialPost]:
    """Fetch posts from Facebook public sources matching the provided keywords.

    NOTE: Replace this stub with actual Facebook Graph API calls.
    """
    # TODO: Implement Facebook Graph API query using region_keywords filters.
    sample_posts = [
        RawSocialPost(
            platform=SourcePlatform(name="facebook", identifier="sample-page"),
            post_id="fb_001",
            author="Barangay Updates",
            content="Road repair along Session Road causing traffic delays."
            " Please deploy traffic aides.",
            created_at=datetime.utcnow(),
            url=None,
            location=LocationContext(),
            metadata={"keywords": list(region_keywords)},
        )
    ]
    return sample_posts
