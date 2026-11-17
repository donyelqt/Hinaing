"""Every tracked Python file under backend/ must stay compilable.

Cheap regression net for syntax breakage. Relies on git to enumerate the
tracked sources rather than the working tree, so untracked local debris
cannot mask failures.
"""
from __future__ import annotations

import pathlib
import py_compile
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_tracked_backend_python_compiles(tmp_path) -> None:
    out = subprocess.run(
        ["git", "ls-files", "-z", "backend/"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    tracked = [p.decode() for p in out.split(b"\x00") if p.endswith(b".py")]
    assert tracked, "no tracked backend python files found"
    failures = []
    for rel in tracked:
        path = REPO_ROOT / rel
        try:
            py_compile.compile(str(path), cfile=str(tmp_path / (rel.replace("/", "_") + "c")), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{rel}: {exc}")
    assert not failures, "tracked python failed to compile:\n" + "\n".join(failures)
