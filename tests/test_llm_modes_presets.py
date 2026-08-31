from __future__ import annotations

from pathlib import Path

from sussurro.llm import modes as modes_mod
from sussurro.llm.modes import ModeStore


def test_modes_contain_new_specialized_presets(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(modes_mod, "app_data_dir", lambda: tmp_path)

    store = ModeStore.load()
    assert store.exists("email_corp")
    assert store.exists("laudo_birads")
    assert store.exists("peticao_inicial")

    email_corp = store.get("email_corp")
    assert "E-mail Corporativo" in email_corp.prompt
    assert email_corp.builtin is True

    laudo = store.get("laudo_birads")
    assert "BI-RADS" in laudo.prompt
    assert "CATEGORIA BI-RADS" in laudo.prompt

    peticao = store.get("peticao_inicial")
    assert "Petição Inicial" in peticao.prompt
    assert "DOS FATOS" in peticao.prompt
