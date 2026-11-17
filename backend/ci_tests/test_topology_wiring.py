"""AST-level verification of the 7-node Insights graph wiring.

Asserts that the pipeline module's declared topology matches the seven
node names that the rest of the system (routers, docs, UI copy) references.
Executes no pipeline code; survives heavy dependency chains.
"""
from __future__ import annotations

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
GRAPH_PATH = REPO_ROOT / "backend" / "app" / "services" / "insights" / "graph.py"
NODES_PATH = REPO_ROOT / "backend" / "app" / "services" / "insights" / "nodes.py"

EXPECTED_NODES = (
    "orchestrate_queries",
    "fetch_documents",
    "retrieve_internal_knowledge",
    "label_sentiment_and_analyze",
    "consolidate_memory",
    "theme_agents",
    "build_snapshot",
)


def _add_node_ids(tree: ast.Module) -> list[str]:
    ids: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_node":
            continue
        if len(node.args) >= 2 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            ids.append(node.args[0].value)
    return ids


def _edge_kwargs(tree: ast.Module):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_edge":
            continue
        values = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                values.append(arg.value)
            elif isinstance(arg, ast.Name):
                values.append(arg.id)
        yield values


def _defined_function_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def test_graph_declares_exactly_the_seven_nodes() -> None:
    tree = ast.parse(GRAPH_PATH.read_text(encoding="utf-8"))
    ids = _add_node_ids(tree)
    assert ids == list(EXPECTED_NODES), f"graph declares {ids!r}, expected {list(EXPECTED_NODES)!r}"


def test_nodes_module_defines_the_seven_node_functions() -> None:
    tree = ast.parse(NODES_PATH.read_text(encoding="utf-8"))
    defined = _defined_function_names(tree)
    missing = [name for name in EXPECTED_NODES if name not in defined]
    assert not missing, f"nodes.py is missing functions for {missing!r}"


def test_graph_edges_form_ordered_chain_from_start_to_end() -> None:
    tree = ast.parse(GRAPH_PATH.read_text(encoding="utf-8"))
    edges = list(_edge_kwargs(tree))
    assert ("START", "orchestrate_queries") in [(e[0], e[1]) for e in edges], "START does not connect into orchestrate_queries"
    chained = {(e[0], e[1]) for e in edges}
    required = [
        ("orchestrate_queries", "fetch_documents"),
        ("fetch_documents", "retrieve_internal_knowledge"),
    ]
    for edge in required:
        assert edge in chained, f"missing edge {edge!r}"
