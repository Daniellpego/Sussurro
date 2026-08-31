from __future__ import annotations

import json
from pathlib import Path

from sussurro.storage import history as history_mod
from sussurro.storage.history import History


def test_history_skips_malformed_entries(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text(json.dumps([
        {
            "timestamp": 1.0,
            "mode": "raw",
            "text": "válida",
            "duration_audio": 1.2,
            "duration_infer": 0.4,
            "language": "pt",
            "future_field": "ignorar",
        },
        {"timestamp": 2.0, "text": "faltam campos"},
        "lixo",
    ]), encoding="utf-8")
    monkeypatch.setattr(history_mod, "history_path", lambda: path)

    history = History()
    assert history.count() == 1
    assert history.all()[0].text == "válida"
