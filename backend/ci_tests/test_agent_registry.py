"""AST registry of the specialist agent workforce.

Pins down the exact composition the paper describes:

  7 core pipeline agents    QueryOrchestratorAgent, RetrievalAgent,
                            ContextAugmentationAgent, SentimentAgent,
                            CredibilityAgent, ThemeRouterAgent,
                            CoordinatorAgent
  5 credibility agents      DomainTrustAgent, CrossReferenceAgent,
                            FactCheckAgent, LLMAnalysisAgent,
                            TavilyAgent
  6 theme sub-agents        InfrastructureAgent, HealthAgent, SafetyAgent,
                            TourismAgent, EconomyAgent, EnvironmentAgent

Total: 18 agents, of which the paper counts 18+ with the optional
FaithfulnessAgent in the verity pipeline. Verification is structural
(AST), never executes LLM or network code.
"""
from __future__ import annotations

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = REPO_ROOT / "backend" / "app"

CORE_AGENTS = {
    "query_orchestrator.py": ("QueryOrchestratorAgent",),
    "insights/agents.py": ("RetrievalAgent", "SentimentAgent", "CredibilityAgent", "ThemeRouterAgent"),
    "context_agent.py": ("ContextAugmentationAgent",),
    "coordinator_agent.py": ("CoordinatorAgent",),
}

CREDIBILITY_AGENTS = {
    "credibility_agent.py": (
        "DomainTrustAgent",
        "CrossReferenceAgent",
        "FactCheckAgent",
        "LLMAnalysisAgent",
        "TavilyAgent",
    ),
}

THEME_AGENTS = {
    "theme_agent.py": (
        "InfrastructureAgent",
        "HealthAgent",
        "SafetyAgent",
        "TourismAgent",
        "EconomyAgent",
        "EnvironmentAgent",
    ),
}

OPTIONAL_AGENTS = {
    "faithfulness_agent.py": ("FaithfulnessAgent",),
}

BASE = APP / "services" / "agents"
INSIGHTS = APP / "services" / "insights"


def _classes_in(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _resolve(table: dict[str, tuple[str, ...]]) -> tuple[set[str], str]:
    found: set[str] = set()
    for rel, names in table.items():
        path = BASE / rel if rel != "insights/agents.py" else INSIGHTS / "agents.py"
        assert path.is_file(), f"expected agents module missing: {path}"
        found |= _classes_in(path)
    return found, path.name


def test_seven_core_pipeline_agents_exist() -> None:
    found, missing_path = _resolve(CORE_AGENTS)
    expected = {name for names in CORE_AGENTS.values() for name in names}
    missing = expected - found
    assert not missing, f"core agents not declared at module level near {missing_path}: {sorted(missing)}"
    assert len(expected) == 7


def test_five_credibility_agents_exist() -> None:
    found, missing_path = _resolve(CREDIBILITY_AGENTS)
    expected = set().union(*CREDIBILITY_AGENTS.values())
    missing = expected - found
    assert not missing, f"credibility agents not declared at module level in {missing_path}: {sorted(missing)}"
    assert len(expected) == 5


def test_six_theme_sub_agents_exist() -> None:
    found, missing_path = _resolve(THEME_AGENTS)
    expected = set().union(*THEME_AGENTS.values())
    missing = expected - found
    assert not missing, f"theme agents not declared at module level in {missing_path}: {sorted(missing)}"
    assert len(expected) == 6


def test_optional_faithfulness_agent_exists() -> None:
    found, missing_path = _resolve(OPTIONAL_AGENTS)
    expected = set().union(*OPTIONAL_AGENTS.values())
    missing = expected - found
    assert not missing, f"faithfulness agent not declared at module level in {missing_path}: {sorted(missing)}"
