from __future__ import annotations

from pathlib import Path

from sussurro.storage import dictionary as dict_mod
from sussurro.storage.dictionary import Dictionary


def test_dictionary_macros_crud(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dict_mod, "app_data_dir", lambda: tmp_path)

    d = Dictionary()
    assert "esse tê efe" in d.all_macros()
    assert d.all_macros()["esse tê efe"] == "STF"

    # Adiciona macro personalizada
    d.add_macro("habeas corpus", "HC")
    assert d.all_macros()["habeas corpus"] == "HC"

    applied = d.apply_macros("impetrou um habeas corpus perante o esse tê efe")
    assert applied == "impetrou um HC perante o STF"

    # Remove macro
    d.remove_macro("habeas corpus")
    assert "habeas corpus" not in d.all_macros()
