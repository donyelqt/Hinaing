"""Regression test: every theme's strongest document leads the citation order.

Guards the prod run where a single global credibility sort made one document
the citation for all six themes, so every narrative paragraph cited source 1.
"""
from app.schemas.snapshot import WebDocument
from app.services.insights import nodes

THEMES = ("economy", "environment", "health", "infrastructure", "safety", "tourism")


def _doc(title: str, score: float, url: str) -> WebDocument:
    return WebDocument(
        title=title, snippet="s", url=url, metadata={"credibility_score": score}
    )


def _state_with_two_docs_per_theme():
    state = {"theme_documents": {}}
    docs = []
    for index, theme in enumerate(THEMES):
        strong = _doc(f"{theme} strong", 0.9 - index * 0.05, f"https://s{index}.gov/1")
        weak = _doc(f"{theme} weak", 0.2, f"https://w{index}.gov/2")
        state["theme_documents"][theme] = [weak, strong]
        docs.extend([weak, strong])
    return state, docs


def test_every_theme_leader_is_inside_the_citation_menu():
    state, docs = _state_with_two_docs_per_theme()

    ordered = nodes._order_docs_by_theme(state, docs)

    leaders = [doc.title for doc in ordered[: len(THEMES)]]
    assert all("weak" not in title for title in leaders), leaders
    assert len(leaders) == len(THEMES)


def test_a_theme_strongest_doc_precedes_its_own_weakest():
    state, docs = _state_with_two_docs_per_theme()

    ordered = [doc.title for doc in nodes._order_docs_by_theme(state, docs)]

    for theme in THEMES:
        assert ordered.index(f"{theme} strong") < ordered.index(f"{theme} weak")


def test_missing_credibility_score_does_not_break_ordering():
    unscored = WebDocument(title="unscored", snippet="s", url="https://u.gov/1")
    scored = _doc("scored", 0.5, "https://g.gov/1")
    state = {"theme_documents": {"health": [unscored, scored]}}

    ordered = nodes._order_docs_by_theme(state, [unscored, scored])

    assert [doc.title for doc in ordered] == ["scored", "unscored"]