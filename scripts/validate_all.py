"""Validação rápida pós-mudanças, sem exigir GPU, microfone ou Ollama online.

Uso:
    python scripts/validate_all.py
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _run(label: str, command: list[str]) -> bool:
    result = subprocess.run(command, cwd=ROOT, text=True)
    if result.returncode:
        print(f"FAIL {label} (exit={result.returncode})")
        return False
    print(f"  ok {label}")
    return True


def _syntax() -> None:
    for base in (ROOT / "sussurro", ROOT / "scripts", ROOT / "tests"):
        for path in base.rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def main() -> int:
    try:
        _syntax()
        print("  ok syntax")
    except (SyntaxError, OSError) as exc:
        print(f"FAIL syntax: {exc}")
        return 1

    checks = [
        ("imports", [sys.executable, "scripts/check_imports.py"]),
        ("tests", [sys.executable, "-m", "pytest", "tests"]),
    ]
    return 0 if all(_run(label, cmd) for label, cmd in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
