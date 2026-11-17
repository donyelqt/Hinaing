"""AST registry of the specialist agent workforce.

The paper counts the implementation as 18 asserted specialist modules plus
the optional FaithfulnessAgent = 19 when the verity pipeline runs.
Boundary-level subscriptions below — agent may be a thin wrapper or the
backing class that actually executes; both layers are checked so a reader
can see exactly which file owns which behavior:

  Core 7 (pipeline order)                 class                 backing impl
  1. Node 1 query orchestration       QueryOrchestratorAgent  (self-contained)
  2. Node 2 retrieval                 RetrievalAgent          (insights/agents.py
                                                              wraps app.services
                                                              .agents' retrieval)
  3. Node 3 internal RAG recall     ContextAugmentationAgent  (self-contained,
                                                              wraps app.services
                                                              .rag.*)
  4. Node 4 sentiment + credibility  SentimentAgent           backs to
                                                              EnsembleSentimentAgent
                                                              (RoBERTa + LLM ensemble);
                                                              CredibilityAgent backs to
                                                              services/agents/credibility
  6. Node 6 theme routing           ThemeRouterAgent          backs to
                                                              SemanticThemeRouterAgent
                                                              (embeddings + keywords)
  7. Node 7 coordination           CoordinatorAgent           self-contained
                                                              (Node 7 runs it)

  Cred 5 (Node 4 credibility workers, services/agents/credibility_agent.py):
      DomainTrustAgent · CrossReferenceAgent · FactCheckAgent ·
      LLMAnalysisAgent · TavilyAgent
  Theme 6 (Node 6 synthesis sub-agents, services/agents/theme_agent.py):
      InfrastructureAgent · HealthAgent · SafetyAgent · TourismAgent ·
      EconomyAgent · EnvironmentAgent

  Optional verity pipeline: FaithfulnessAgent (services/agents/faithfulness_agent.py),
      making the workforce 18 + 1 = 19 when enabled.

Every entry below is an existence assertion at the module level (AST) — no LLM call, no network.
"""
from __future__ import annotations

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = REPO_ROOT / "backend" / "app" / "services"
AGENTS = APP / "agents"
INSIGHTS = APP / "insights"


def _classes_in(path: pathlib.Path) -> set[str]:
    assert path.is_file(), f"expected agent module missing: {path}"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _functions_in(path: pathlib.Path) -> set[str]:
    assert path.is_file(), f"expected module missing: {path}"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def test_core_pipeline_agents_exist_at_node_boundary() -> None:
    checks = [
        (AGENTS / "query_orchestrator.py", {"QueryOrchestratorAgent"}),
        (INSIGHTS / "agents.py", {"RetrievalAgent", "SentimentAgent", "CredibilityAgent", "ThemeRouterAgent"}),
        (AGENTS / "context_agent.py", {"ContextAugmentationAgent"}),
        (AGENTS / "coordinator_agent.py", {"CoordinatorAgent"}),
    ]
    missing = []
    for path, classes in checks:
        found = _classes_in(path)
        missing += [f"{path.name}:{cls}" for cls in sorted(classes - found)]
    assert not missing, f"core pipeline agents missing: {missing}"


def test_node4_sentiment_backing_class_exists() -> None:
    classes = _classes_in(AGENTS / "sentiment_agent.py")
    assert "EnsembleSentimentAgent" in classes, (
        "Node 4 sentiment path backs to EnsembleSentimentAgent (RoBERTa + LLM ensemble); "
        "not found in sentiment_agent.py"
    )
    functions = _functions_in(AGENTS / "sentiment_agent.py")
    assert "get_sentiment_agent" in functions, "lazy factory get_sentiment_agent not defined"


def test_node4_credibility_backing_class_and_five_workers_exist() -> None:
    classes = _classes_in(AGENTS / "credibility_agent.py")
    expected_backing = {"CredibilityAgent", "DomainTrustAgent", "CrossReferenceAgent", "FactCheckAgent", "LLMAnalysisAgent", "TavilyAgent"}
    missing = expected_backing - classes
    assert not missing, f"credibility backing/sub-agents missing: {sorted(missing)}"


def test_node6_theme_routing_backing_class_exists() -> None:
    classes = _classes_in(AGENTS / "theme_router_agent.py")
    assert "SemanticThemeRouterAgent" in classes
    functions = _functions_in(AGENTS / "theme_router_agent.py")
    assert "get_theme_router_agent" in functions, "lazy factory get_theme_router_agent not defined"


def test_six_theme_sub_agents_exist_at_module_level() -> None:
    classes = _classes_in(AGENTS / "theme_agent.py")
    expected = {
        "InfrastructureAgent",
        "HealthAgent",
        "SafetyAgent",
        "TourismAgent",
        "EconomyAgent",
        "EnvironmentAgent",
    }
    missing = expected - classes
    assert not missing, f"theme sub-agents missing: {sorted(missing)}"
    assert len(expected) == 6


def test_optional_faithfulness_agent_exists_at_module_level() -> None:
    classes = _classes_in(AGENTS / "faithfulness_agent.py")
    assert "FaithfulnessAgent" in classes
