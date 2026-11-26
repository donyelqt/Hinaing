"""Regression test: a theme agent sees every document it was given.

Guards the silent truncation where `_build_theme_context` showed only the
first 10 documents, so a theme with 15 answered about 10.
"""
from app.services.insights import nodes


def _docs(count: int) -> list[dict]:
    return [
        {"title": f"Doc {i}", "snippet": f"Snippet {i}", "url": f"https://e.gov/{i}"}
        for i in range(count)
    ]


def test_all_documents_reach_the_context():
    docs = _docs(15)

    context = nodes._build_theme_context(docs)

    for i in range(15):
        assert f"Doc {i}" in context, i


def test_context_never_exceeds_the_citation_menu_cap():
    docs = _docs(60)

    context = nodes._build_theme_context(docs)

    shown = [line for line in context.splitlines() if line.startswith("- ")]
    assert len(shown) == nodes.THEME_CONTEXT_DOC_LIMIT