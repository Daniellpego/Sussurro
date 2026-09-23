"""Testes unitários da fiação de qualidade (sem GPU / sem Ollama).

Roda: python -m pytest tests/test_asr_quality.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sussurro.asr.postprocess import (  # noqa: E402
    apply_dictionary_casing,
    capitalize_sentences,
    cleanup_transcript,
    postprocess,
)
from sussurro.asr.whisper import _resolve_language  # noqa: E402
from sussurro.commands import apply_commands  # noqa: E402
from sussurro.storage.dictionary import Dictionary  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_language_auto() -> None:
    _assert(_resolve_language("auto") is None, "auto -> None")
    _assert(_resolve_language("") is None, "vazio -> None")
    _assert(_resolve_language(None) is None, "None -> None")
    _assert(_resolve_language("pt") == "pt", "pt")
    _assert(_resolve_language("en") == "en", "en")


def test_cleanup() -> None:
    _assert(cleanup_transcript("olá  mundo ,  tudo bem") == "olá mundo, tudo bem",
            "espaços e vírgula")
    _assert(cleanup_transcript("fim...") == "fim…", "reticências")


def test_dictionary_casing() -> None:
    text = "usei o pyside6 e o github ontem"
    out = apply_dictionary_casing(text, ["PySide6", "GitHub"])
    _assert("PySide6" in out, f"PySide6 casing: {out}")
    _assert("GitHub" in out, f"GitHub casing: {out}")


def test_capitalize() -> None:
    out = capitalize_sentences("olá. tudo bem? sim")
    _assert(out.startswith("Olá"), f"cap start: {out}")
    _assert(". Tudo" in out or ". tudo" not in out, f"cap after period: {out}")


def test_postprocess_pipeline() -> None:
    out = postprocess(
        "olá  mundo , usei o ollama",
        terms=["Ollama"],
    )
    _assert("Ollama" in out, f"terms: {out}")
    _assert(out[0].isupper(), f"capitalized: {out}")
    _assert("  " not in out, f"no double space: {out}")


def test_style_prompt_always() -> None:
    d = Dictionary.__new__(Dictionary)
    d._terms = []
    p = d.to_prompt()
    _assert(p is not None and "português brasileiro" in p.lower()
            or "portugues brasileiro" in (p or "").lower()
            or "acentuação" in (p or "").lower()
            or "acentuacao" in (p or "").lower(),
            f"style prompt: {p}")
    d._terms = ["PySide6", "Claude"]
    p2 = d.to_prompt()
    _assert("PySide6" in (p2 or ""), f"terms in prompt: {p2}")
    hw = d.to_hotwords()
    _assert(hw is not None and "PySide6" in hw, f"hotwords: {hw}")


def test_voice_commands() -> None:
    out = apply_commands("olá vírgula mundo ponto final fim")
    _assert("," in out, f"virgula: {out}")
    _assert("." in out, f"ponto final: {out}")
    out2 = apply_commands("olá nova linha b")
    _assert("\n" in out2, f"nova linha: {out2}")
