"""Indicador de gravação: só a onda, que segue a voz."""
from __future__ import annotations


def test_recording_shows_only_the_wave() -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.5)
    overlay.show_recording("raw")
    shown = [overlay._row.itemAt(i).widget()  # noqa: SLF001
             for i in range(overlay._row.count())]  # noqa: SLF001
    # sem texto ao vivo, ponto de gravação nem cronômetro: só a onda
    assert shown == [overlay._wave]  # noqa: SLF001
    content = overlay._content.geometry()  # noqa: SLF001
    assert content.height() == overlay._pill_h  # noqa: SLF001
    overlay.close()


def test_recording_keeps_mode_chip_for_non_default_modes() -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.5)
    overlay.show_recording("email")
    shown = [overlay._row.itemAt(i).widget()  # noqa: SLF001
             for i in range(overlay._row.count())]  # noqa: SLF001
    assert shown == [overlay._chip, overlay._wave]  # noqa: SLF001
    overlay.close()


def _run_frames(wave, frames: int) -> None:
    for _ in range(frames):
        wave._frame()  # noqa: SLF001


def test_wave_follows_voice_and_rests_in_silence() -> None:
    from sussurro.ui.overlay import _HudWaveform

    level = {"value": 0.0}
    wave = _HudWaveform(lambda: level["value"])
    wave.start()
    _run_frames(wave, 30)
    assert max(wave._heights) < 0.05  # noqa: SLF001 - silêncio: pontos

    level["value"] = 0.8
    _run_frames(wave, 30)
    heights = wave._heights  # noqa: SLF001
    assert max(heights) > 0.5
    assert all(0.0 <= h <= 1.0 for h in heights)
    # a barra central é a mais alta do perfil, como no logo
    assert wave._PROFILE[len(heights) // 2] == max(wave._PROFILE)  # noqa: SLF001

    level["value"] = 0.0
    _run_frames(wave, 60)
    assert max(wave._heights) < 0.1  # noqa: SLF001 - volta a repousar
    wave.stop()


def test_wave_survives_a_failing_level_source() -> None:
    from sussurro.ui.overlay import _HudWaveform

    def broken() -> float:
        raise RuntimeError("mic removido")

    wave = _HudWaveform(broken)
    wave.start()
    _run_frames(wave, 5)
    assert max(wave._heights) == 0.0  # noqa: SLF001
    wave.stop()
