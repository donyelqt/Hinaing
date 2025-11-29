"""Shared helper utilities for insight agents and filters."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ...schemas.snapshot import SnapshotRequest, WebDocument

logger = logging.getLogger(__name__)

CONCERN_MODIFIERS = ["problem", "issue", "concern", "complaint", "crisis"]

FOCUS_CONCERN_KEYWORDS: dict[str, list[str]] = {
    "infrastructure": [
        "Baguio road problem",
        "Baguio traffic issue",
        "Baguio water problem",
        "Baguio power outage",
        "Baguio pothole complaint",
        "Kennon Road problem",
        "Baguio jeepney concern",
        "Baguio garbage issue",
        "Session Road traffic",
    ],
    "health": [
        "Baguio hospital problem",
        "Baguio health concern",
        "Baguio disease issue",
        "Baguio sanitation problem",
        "Baguio medical complaint",
    ],
    "safety": [
        "Baguio crime problem",
        "Baguio flood concern",
        "Baguio landslide issue",
        "Baguio fire problem",
        "Baguio accident concern",
        "Baguio safety issue",
    ],
    "tourism": [
        "Baguio tourist complaint",
        "Baguio overcrowding problem",
        "Burnham Park issue",
        "Baguio hotel complaint",
        "Baguio tourism concern",
    ],
    "economy": [
        "Baguio vendor problem",
        "Baguio market issue",
        "Baguio business concern",
        "Baguio livelihood problem",
        "Baguio employment issue",
        "Baguio market mallification",
        "Baguio public market mallification",
        "Baguio mallification protest",
        "Baguio public market redevelopment",
        "Baguio PPP market redevelopment",
        "SM Prime Baguio market",
        "Baguio vendor displacement",
    ],
    "environment": [
        "Baguio pollution problem",
        "Baguio air quality concern",
        "Baguio waste issue",
        "Baguio flooding problem",
        "Baguio environmental concern",
    ],
}

BAGUIO_LOCATION_TERMS = {
    "baguio",
    "benguet",
    "cordillera",
    "session road",
    "burnham park",
    "kennon road",
    "marcos highway",
    "la trinidad",
    "panagbenga",
    "camp john hay",
    "mines view",
    "wright park",
    "baguio general hospital",
    "bgh",
    "summer capital",
    "city of pines",
    "governor pack",
    "abanao",
    "porta vaga",
}

EXCLUDED_DOMAINS = {
    "wikipedia.org",
    "wikimedia.org",
    "wikidata.org",
    "britannica.com",
    "dictionary.com",
    "quora.com",
    "tripadvisor.com",
    "booking.com",
    "agoda.com",
    "expedia.com",
    "airbnb.com",
    "pinterest.com",
}


def build_focus_query(request: SnapshotRequest) -> str:
    """Construct a LangSearch-ready query based on selected focus areas."""
    if request.focus_areas:
        all_terms: list[str] = []
        for area in request.focus_areas:
            area_lower = area.lower()
            terms = FOCUS_CONCERN_KEYWORDS.get(area_lower)
            if terms:
                all_terms.extend(terms)
            else:
                all_terms.append(f"Baguio {area} problem")
                all_terms.append(f"Baguio {area} concern")
        unique_terms = list(dict.fromkeys(all_terms))
        terms_query = " OR ".join(f'"{term}"' for term in unique_terms)
        return f"({terms_query})"

    concern_terms = " OR ".join(CONCERN_MODIFIERS)
    return f'"Baguio City" AND ({concern_terms})'


def get_window_timedelta(time_window: str | None) -> timedelta | None:
    if not time_window:
        return None
    mapping: dict[str, timedelta] = {
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "3d": timedelta(days=3),
        "7d": timedelta(days=7),
    }
    return mapping.get(time_window)


def filter_by_time_window(documents: list[WebDocument], time_window: str | None) -> list[WebDocument]:
    delta = get_window_timedelta(time_window)
    if not delta:
        return documents

    now = datetime.now(timezone.utc)
    cutoff = now - delta
    filtered = [doc for doc in documents if doc.published_at and doc.published_at >= cutoff]
    return filtered or documents


def filter_by_location(documents: list[WebDocument]) -> list[WebDocument]:
    filtered: list[WebDocument] = []
    for doc in documents:
        url_str = str(doc.url) if doc.url else ""
        searchable = f"{doc.title} {doc.snippet} {url_str}".lower()
        if any(term in searchable for term in BAGUIO_LOCATION_TERMS):
            filtered.append(doc)
        else:
            logger.debug(
                "Filtered out non-Baguio document: %s",
                doc.title[:50] if doc.title else "Untitled",
            )
    return filtered


def filter_excluded_sources(documents: list[WebDocument]) -> list[WebDocument]:
    filtered: list[WebDocument] = []
    for doc in documents:
        url = str(doc.url).lower() if doc.url else ""
        if any(domain in url for domain in EXCLUDED_DOMAINS):
            logger.debug("Filtered out excluded source: %s", doc.url)
            continue
        filtered.append(doc)
    return filtered
