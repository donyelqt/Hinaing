"""Regression test: the theme prompt must not demand more than the docs allow.

Guards the live 6h run where Infrastructure held 4 documents and returned
`{"insights": []}` because the prompt demanded exactly 3 recommendations.
"""
from app.services.insights import nodes


def test_demand_never_exceeds_the_document_count():
    for count in (1, 2, 4, 15):
        prompt = nodes._build_theme_prompt("Infrastructure", "focus", "ctx", count)
        allowed = min(3, count)
        assert f"AT MOST {allowed}" in prompt, (count, allowed)
        assert "EXACTLY 3" not in prompt, count


def test_prompt_allows_a_single_recommendation():
    prompt = nodes._build_theme_prompt("Environment", "focus", "ctx", 1)

    assert "AT MOST 1" in prompt
    assert "RECOMMENDATION for government action" in prompt


def test_empty_is_only_for_documents_with_nothing_relevant():
    prompt = nodes._build_theme_prompt("Environment", "focus", "ctx", 2)

    assert "ONLY when the documents contain nothing related" in prompt