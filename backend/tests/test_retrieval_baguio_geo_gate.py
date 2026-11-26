"""Retrieval must never return a document that is not about Baguio City.

The demo and the live pipeline both failed the same way: LangSearch answers a
bare topic query with national and foreign news, and ``filter_by_location``
kept every one of those documents because the host was a PH civic domain.
"""
from __future__ import annotations

from app.schemas.snapshot import WebDocument
from app.services.insights.agent_tools import filter_by_location


def _doc(url: str, title: str, snippet: str) -> WebDocument:
    return WebDocument(title=title, snippet=snippet, url=url)


NYC_BIKE = _doc(
    "https://www.manilatimes.net/news/national/bike-crash-nyc",
    "Bike crash in New York City",
    "A cyclist was struck by a delivery van in Manhattan on Tuesday.",
)
DAVAO_FLOOD = _doc(
    "https://www.sunstar.com.ph/davao/davao-city-flood-control",
    "Davao City flood control project flagged",
    "COA flagged the Davao City drainage project for review.",
)
CALOOCAN = _doc(
    "https://tribune.net.ph/caloocan-mayor-probe",
    "Caloocan mayor orders probe",
    "The Caloocan city government opened an inquiry.",
)
DHSUD = _doc(
    "https://pia.gov.ph/dhsud-budget-2027",
    "DHSUD submits 2027 budget",
    "The housing department submitted its budget proposal.",
)
PSEI = _doc(
    "https://www.bworldonline.com/stock-index-record",
    "Stock index hits record high",
    "The PSEi closed at an all-time high on Monday.",
)
BAGUIO_SESSION_ROAD = _doc(
    "https://baguioheraldexpressonline.com/session-road-reroute",
    "Session Road rerouted for repair",
    "Baguio commuters were rerouted around the Session Road works.",
)
BAGUIO_PH_MIRROR = _doc(
    "https://newsinfo.inquirer.net/1/baguio-water-shortage",
    "Baguio water shortage deepens",
    "Baguio City households reported low water pressure this week.",
)


def test_foreign_and_non_baguio_documents_are_rejected() -> None:
    kept = filter_by_location([NYC_BIKE, DAVAO_FLOOD, CALOOCAN, DHSUD, PSEI])

    assert kept == []


def test_baguio_documents_are_kept() -> None:
    kept = filter_by_location([BAGUIO_SESSION_ROAD, BAGUIO_PH_MIRROR])

    assert [doc.url for doc in kept] == [
        BAGUIO_SESSION_ROAD.url,
        BAGUIO_PH_MIRROR.url,
    ]


def test_a_mixed_batch_keeps_only_the_baguio_documents() -> None:
    kept = filter_by_location(
        [NYC_BIKE, BAGUIO_SESSION_ROAD, DAVAO_FLOOD, BAGUIO_PH_MIRROR, CALOOCAN]
    )

    assert [doc.url for doc in kept] == [
        BAGUIO_SESSION_ROAD.url,
        BAGUIO_PH_MIRROR.url,
    ]