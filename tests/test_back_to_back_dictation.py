"""Ditados em sequência: HUD, fila de colagem, atalho e microfone."""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest

from sussurro.audio import capture
from sussurro.inject import paste

# --------------------------------------------------------------------- HUD

def test_new_recording_cancels_pending_fade_out(qt_app) -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.0)
    overlay.show_done(ok=True)
    assert overlay._auto_hide.isActive()

    # "Colado" começou a sumir e o usuário já apertou o atalho de novo
    overlay._fade_out()
    assert overlay._hide_timer.isActive()
    overlay.show_recording("raw")

    assert not overlay._auto_hide.isActive()
    assert not overlay._hide_timer.isActive()
    assert overlay.windowOpacity() == 1.0
    overlay.close()


def test_new_recording_cancels_auto_hide(qt_app) -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.0)
    overlay.show_error("erro na transcrição")
    assert overlay._auto_hide.isActive()
    overlay.show_recording("raw")
    assert not overlay._auto_hide.isActive()
    overlay.close()


# ------------------------------------------------------------ fila de colagem

def test_paste_waits_for_recording_and_keys() -> None:
    state = {"recording": True, "keys": True}
    order: list[str] = []

    def release_later() -> None:
        time.sleep(0.05)
        order.append("recording-stopped")
        state["recording"] = False
        time.sleep(0.05)
        order.append("keys-released")
        state["keys"] = False

    threading.Thread(target=release_later).start()
    paste.wait_until_keyboard_free(
        lambda: state["recording"],
        recording_timeout=5, keys_timeout=5,
        keys_held=lambda: state["keys"], poll=0.005,
    )
    order.append("paste")
    assert order == ["recording-stopped", "keys-released", "paste"]


def test_paste_wait_gives_up_after_timeout() -> None:
    start = time.monotonic()
    paste.wait_until_keyboard_free(
        lambda: True, recording_timeout=0.05, keys_timeout=0.05,
        keys_held=lambda: True, poll=0.005,
    )
    assert time.monotonic() - start < 1


# ------------------------------------------------------------------ atalho

def _listener_module():
    try:
        from sussurro.hotkey import listener
    except Exception as exc:  # noqa: BLE001 - pynput precisa de display fora do Windows
        pytest.skip(f"pynput indisponível: {exc}")
    return listener


def test_injected_keys_are_ignored() -> None:
    listener = _listener_module()
    ptt = listener.PushToTalkListener()
    assert ptt._win32_filter(0x100, SimpleNamespace(flags=0x10)) is False
    assert ptt._win32_filter(0x100, SimpleNamespace(flags=0)) is True


def test_stuck_win_key_does_not_start_recording(monkeypatch) -> None:
    listener = _listener_module()
    ptt = listener.PushToTalkListener()
    started: list[float] = []
    ptt.pressed.connect(started.append)
    # o soltar do Win se perdeu (ex.: Win+L); fisicamente ele está solto
    ptt._win = True
    monkeypatch.setattr(ptt, "_physically_down", lambda vks: False)
    ptt._on_press(listener.keyboard.Key.ctrl_l)
    assert started == []
    assert ptt._win is False


# -------------------------------------------------------------- microfone

class _SlowStream:
    opened = 0

    def __init__(self, **kwargs) -> None:
        type(self).opened += 1
        self._callback = kwargs["callback"]
        self.active = True
        self.closed = False

    def start(self) -> None:
        time.sleep(0.05)  # abertura lenta, como um driver real
        self._callback(np.zeros((capture.BLOCK_SIZE, 1), dtype=np.float32), 0, None, None)

    def stop(self) -> None:
        self.active = False

    def close(self) -> None:
        self.closed = True


def test_concurrent_prepare_opens_a_single_stream(monkeypatch) -> None:
    _SlowStream.opened = 0
    monkeypatch.setattr(capture.sd, "InputStream", _SlowStream, raising=False)
    recorder = capture.Recorder()
    threads = [threading.Thread(target=recorder.prepare) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert _SlowStream.opened == 1
    recorder.close()


def test_stopped_stream_is_reopened(monkeypatch) -> None:
    _SlowStream.opened = 0
    monkeypatch.setattr(capture.sd, "InputStream", _SlowStream, raising=False)
    recorder = capture.Recorder()
    recorder.prepare()
    first = recorder._stream
    first.active = False  # microfone desconectado
    recorder.prepare()
    assert first.closed
    assert recorder._stream is not first
    assert _SlowStream.opened == 2
    recorder.close()


def test_message_shown_from_hidden_hud_still_auto_hides(qt_app) -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.0)
    assert not overlay.isVisible()
    overlay.show_error("microfone indisponível")
    assert overlay._auto_hide.isActive()
    overlay.hide()
    overlay.show_done(ok=True)
    assert overlay._auto_hide.isActive()
    overlay.close()


def test_saved_window_position_must_be_on_a_screen(qt_app) -> None:
    from PySide6.QtCore import QRect

    from sussurro.ui.window import position_is_on_screen

    screens = [QRect(0, 0, 1920, 1040)]
    assert position_is_on_screen(100, 100, screens)
    # posição salva num segundo monitor que foi desconectado
    assert not position_is_on_screen(2500, 300, screens)
    assert position_is_on_screen(2500, 300, screens + [QRect(1920, 0, 2560, 1400)])


def test_loading_notice_goes_away_when_model_is_ready() -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.0)
    overlay.show_loading_model()
    assert not overlay._auto_hide.isActive()  # noqa: SLF001 - fica até ficar pronto
    overlay.dismiss_loading()
    assert overlay._hide_timer.isActive()  # noqa: SLF001
    overlay.close()


def test_dismiss_loading_leaves_other_states_alone() -> None:
    from sussurro.ui.overlay import Overlay

    overlay = Overlay(level_source=lambda: 0.0)
    overlay.show_recording("raw")
    overlay.dismiss_loading()
    assert not overlay._hide_timer.isActive()  # noqa: SLF001 - gravando continua
    overlay.close()
