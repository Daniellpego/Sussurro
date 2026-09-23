"""Arquivos ilegíveis são preservados antes de os padrões os sobrescreverem."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sussurro.llm import modes as modes_mod
from sussurro.storage import config as config_mod
from sussurro.storage import dictionary as dict_mod
from sussurro.storage import history as history_mod


def _backups(folder: Path, name: str) -> list[Path]:
    return sorted(folder.glob(f"{name}.corrupt-*"))


def test_corrupt_config_is_preserved(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('first_run_done = true\nlanguage = "pt"\n[broken', encoding="utf-8")
    monkeypatch.setattr(config_mod, "config_path", lambda: path)

    cfg = config_mod.Config.load()
    assert cfg == config_mod.Config()
    backups = _backups(tmp_path, "config.toml")
    assert len(backups) == 1
    assert "first_run_done = true" in backups[0].read_text(encoding="utf-8")


@pytest.mark.parametrize("content", ["{not json", json.dumps({"a": 1})])
def test_corrupt_history_is_preserved(monkeypatch, tmp_path: Path, content: str) -> None:
    path = tmp_path / "history.json"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(history_mod, "history_path", lambda: path)

    history = history_mod.History()
    assert history.all() == []
    assert _backups(tmp_path, "history.json")[0].read_text(encoding="utf-8") == content


def test_corrupt_modes_are_preserved(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(modes_mod, "app_data_dir", lambda: tmp_path)
    path = modes_mod._store_path()
    path.write_text('[{"id": "meu-modo", "prompt": "...', encoding="utf-8")

    store = modes_mod.ModeStore.load()
    assert store.modes  # voltou aos modos padrão
    assert len(_backups(tmp_path, path.name)) == 1


def test_corrupt_dictionary_and_macros_are_preserved(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dict_mod, "app_data_dir", lambda: tmp_path)
    d = dict_mod.Dictionary()  # cria os arquivos iniciais
    terms_path, macros_path = d._path(), d._macros_path()
    terms_path.write_text("{quebrado", encoding="utf-8")
    macros_path.write_text("[1, 2", encoding="utf-8")

    dict_mod.Dictionary()
    assert len(_backups(tmp_path, terms_path.name)) == 1
    assert len(_backups(tmp_path, macros_path.name)) == 1


def test_valid_files_are_left_alone(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(history_mod, "history_path", lambda: path)
    history_mod.History()
    assert _backups(tmp_path, "history.json") == []
