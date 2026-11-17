"""Factory and prompt contract of the six theme sub-agents.

The six theme sub-agents are the pipeline's Node 6 workforce. This file pins
their instantiation contract without calling any LLM: each factory key must
resolve to the matching BaseThemeAgent subclass and its prompt must carry the
domain label.
"""
from __future__ import annotations

import sys
import types
from typing import Any

import pytest


def _stub_snapshot_schema() -> None:
    if "app.schemas.snapshot" in sys.modules:
        return
    from dataclasses import dataclass

    stub = types.ModuleType("app.schemas.snapshot")

    @dataclass
    class WebDocument:
        title: str = ""
        snippet: str = ""
        url: str | None = None
        content: str = ""

    stub.WebDocument = WebDocument
    sys.modules["app.schemas.snapshot"] = stub


_stub_snapshot_schema()

from app.services.agents import theme_agent  # noqa: E402

THEME_KEYS = (
    ("infrastructure", theme_agent.InfrastructureAgent, "Infrastructure"),
    ("health", theme_agent.HealthAgent, "Health & Wellness"),
    ("safety", theme_agent.SafetyAgent, "Public Safety"),
    ("tourism", theme_agent.TourismAgent, "Tourism & Events"),
    ("economy", theme_agent.EconomyAgent, "Business & Economy"),
    ("environment", theme_agent.EnvironmentAgent, "Environment"),
)


@pytest.mark.parametrize("key,expected_class,_", THEME_KEYS)
def test_factory_returns_the_six_domain_sub_agents(
    key: str,
    expected_class: type[Any],
    _: str,
) -> None:
    agent = theme_agent.get_theme_agent(key)
    assert isinstance(agent, expected_class)
    assert agent.theme_focus, "theme focus must carry a competency string"


@pytest.mark.parametrize("key,_,label", THEME_KEYS)
def test_prompt_carries_the_domain_label_and_count(
    key: str,
    _: type[Any],
    label: str,
) -> None:
    agent = theme_agent.get_theme_agent(key)
    prompt = agent._build_prompt(
        label,
        agent.theme_focus,
        "- [Session Road](https://example.com): traffic update",
        1,
    )
    assert label in prompt
    assert "1" in prompt or "Documents" in prompt
