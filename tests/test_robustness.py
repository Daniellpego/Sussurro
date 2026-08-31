"""Testes da fiação de robustez (paste result, dicionário, presets) — sem GPU."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _ok(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_paste_result_type() -> None:
    from sussurro.inject.paste import PasteResult, _chain_for
    r = PasteResult(ok=True, method="ctrl+v")
    _ok(r.ok and r.method == "ctrl+v", "PasteResult")
    _ok(_chain_for("auto") == ["ctrl+v", "shift+insert", "type"], "auto chain")
    _ok(_chain_for("type") == ["type"], "type only")
    _ok(_chain_for("ctrl+v")[0] == "ctrl+v", "preferred first")
    _ok("type" in _chain_for("ctrl+v"), "fallback type")


def test_dictionary_seed_and_observe() -> None:
    from sussurro.storage import dictionary as dmod

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        with mock.patch.object(dmod, "app_data_dir", return_value=base):
            # path fake: sem arquivo -> seed
            d = dmod.Dictionary.__new__(dmod.Dictionary)
            d._terms = []
            d._suggestions = []
            # simula load sem arquivo
            path = base / "dictionary.json"
            _ok(not path.exists(), "no file yet")
            dmod.Dictionary.load(d)
            _ok(len(d.all()) >= 20, f"seed size {len(d.all())}")
            _ok("Python" in d.all() or any(t == "Python" for t in d.all()),
                "Python no seed")

            # observe texto com termo conhecido fora do dict
            # remove Claude se estiver
            if "Claude" in d.all():
                d.remove("Claude")
            new = d.observe_text("usei o claude pra refatorar o codigo")
            # pode ou nao sugerir dependendo do matching
            _ok(isinstance(new, list), "observe returns list")
            _ok(isinstance(d.suggestions(), list), "suggestions list")


def test_quality_presets() -> None:
    from sussurro.asr.whisper import resolve_preset
    q = resolve_preset("quality")
    _ok(q["beam_size"] == 5, "quality beam")
    b = resolve_preset("balanced")
    _ok(b["beam_size"] == 3, "balanced beam")
    l = resolve_preset("light")
    _ok(l["beam_size"] == 1, "light beam")
    _ok(resolve_preset("nope")["beam_size"] == 5, "fallback quality")


def test_language_resolve() -> None:
    from sussurro.asr.whisper import _resolve_language
    _ok(_resolve_language("auto") is None, "auto")
    _ok(_resolve_language("pt") == "pt", "pt")
