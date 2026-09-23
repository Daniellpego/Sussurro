"""Garante que os assets que o instalador exige estão versionados."""
from __future__ import annotations

import wave
from pathlib import Path

import pytest

ASSETS = Path(__file__).resolve().parents[1] / "sussurro" / "assets"


@pytest.mark.parametrize("name", ["Geist.ttf", "GeistMono.ttf", "OFL.txt"])
def test_fonts_are_bundled(name: str) -> None:
    assert (ASSETS / "fonts" / name).stat().st_size > 0


@pytest.mark.parametrize("name", ["start", "done"])
def test_feedback_sounds_are_valid_wav(name: str) -> None:
    with wave.open(str(ASSETS / "sounds" / f"{name}.wav"), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getnframes() / wav.getframerate() < 0.5  # curtos
