"""Extrai as notas de uma versão do CHANGELOG e confere a versão do pacote.

Uso:
    python scripts/release_notes.py v0.1.1 --out RELEASE_NOTES.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package_version() -> str:
    text = (ROOT / "sussurro" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"', text, re.MULTILINE)
    if not match:
        raise ValueError("__version__ não encontrado em sussurro/__init__.py")
    return match.group(1)


def changelog_section(changelog: str, version: str) -> str:
    """Retorna o corpo da seção `## [version]`, sem o título."""
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)"
    match = re.search(pattern, changelog, re.MULTILINE | re.DOTALL)
    if not match or not match.group(1).strip():
        raise ValueError(f"seção [{version}] ausente ou vazia no CHANGELOG.md")
    return match.group(1).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", help="tag da release, por exemplo v0.1.1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    version = args.tag.removeprefix("v")
    try:
        current = package_version()
        if current != version:
            raise ValueError(
                f"a tag {args.tag} não corresponde a __version__ = {current!r}"
            )
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        notes = changelog_section(changelog, version)
    except ValueError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(notes, encoding="utf-8")
    print(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
