import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_notes  # noqa: E402

CHANGELOG = """# Changelog

## [Não lançado]

- Algo novo.

## [0.2.0] - 2026-10-01

### Adicionado

- Recurso B.

## [0.1.0] - 2026-08-31

- Recurso A.

[Não lançado]: https://example.com/compare
[0.2.0]: https://example.com/0.2.0
"""


def test_extracts_only_requested_section():
    notes = release_notes.changelog_section(CHANGELOG, "0.2.0")
    assert notes == "### Adicionado\n\n- Recurso B.\n"


def test_last_section_stops_before_link_definitions():
    notes = release_notes.changelog_section(CHANGELOG, "0.1.0")
    assert notes == "- Recurso A.\n"


def test_missing_version_raises():
    with pytest.raises(ValueError):
        release_notes.changelog_section(CHANGELOG, "9.9.9")


def test_package_version_matches_pyproject_and_changelog():
    version = release_notes.package_version()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(rf'^version = "{re.escape(version)}"', pyproject, re.MULTILINE)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert release_notes.changelog_section(changelog, version)
