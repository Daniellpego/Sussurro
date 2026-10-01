from __future__ import annotations

import pytest

from sussurro.hotkey import presets
from sussurro.storage.config import Config


def _listener_module():
    try:
        from sussurro.hotkey import listener
    except Exception as exc:  # noqa: BLE001 - pynput precisa de display fora do Windows
        pytest.skip(f"pynput indisponível: {exc}")
    return listener


def _ptt(listener, hotkey, monkeypatch):
    ptt = listener.PushToTalkListener(hotkey)
    monkeypatch.setattr(ptt, "_physically_down", lambda vks: True)
    events: list[str] = []
    ptt.pressed.connect(lambda _t: events.append("pressed"))
    ptt.released.connect(lambda _t: events.append("released"))
    ptt.cancelled.connect(lambda: events.append("cancelled"))
    return ptt, events


def test_unknown_hotkey_falls_back_to_default() -> None:
    assert presets.normalize_hotkey("Ctrl+Alt") == "Ctrl+Alt"
    assert presets.normalize_hotkey("F13") == "Ctrl+Win"
    assert presets.normalize_hotkey(None) == "Ctrl+Win"
    assert presets.keycap_labels("Ctrl+Shift") == ["Ctrl", "Shift"]
    assert presets.keycap_labels("Ctrl direito") == ["Ctrl direito"]


def test_trigger_label_uses_the_chosen_hotkey() -> None:
    cfg = Config(hotkey_label="Ctrl+Shift", mouse_button="none")
    assert cfg.trigger_label == "Ctrl+Shift"
    assert Config(hotkey_label="lixo").trigger_label == "Ctrl+Win"


def test_every_preset_has_keys() -> None:
    listener = _listener_module()
    assert listener.HOTKEYS.keys() == presets.HOTKEY_LABELS.keys()


@pytest.mark.parametrize("hotkey, first, second", [
    ("Ctrl+Win", "ctrl_l", "cmd"),
    ("Ctrl+Shift", "ctrl_l", "shift"),
    ("Ctrl+Alt", "ctrl_r", "alt_l"),
])
def test_combo_starts_and_stops_recording(monkeypatch, hotkey, first, second) -> None:
    listener = _listener_module()
    key = listener.keyboard.Key
    ptt, events = _ptt(listener, hotkey, monkeypatch)
    ptt._on_press(getattr(key, first))
    assert events == []
    ptt._on_press(getattr(key, second))
    assert events == ["pressed"]
    ptt._on_release(getattr(key, first))
    assert events == ["pressed", "released"]


def test_right_ctrl_alone_records_and_left_ctrl_does_not(monkeypatch) -> None:
    listener = _listener_module()
    key = listener.keyboard.Key
    ptt, events = _ptt(listener, "Ctrl direito", monkeypatch)
    ptt._on_press(key.ctrl_l)
    ptt._on_release(key.ctrl_l)
    assert events == []
    ptt._on_press(key.ctrl_r)
    ptt._on_release(key.ctrl_r)
    assert events == ["pressed", "released"]


def test_altgr_does_not_trigger_ctrl_alt(monkeypatch) -> None:
    listener = _listener_module()
    key = listener.keyboard.Key
    ptt, events = _ptt(listener, "Ctrl+Alt", monkeypatch)
    # AltGr chega como Ctrl esquerdo + AltGr
    ptt._on_press(key.ctrl_l)
    ptt._on_press(key.alt_gr)
    assert events == []


def test_other_key_cancels_the_new_hotkey(monkeypatch) -> None:
    listener = _listener_module()
    key = listener.keyboard.Key
    ptt, events = _ptt(listener, "Ctrl+Shift", monkeypatch)
    ptt._on_press(key.ctrl_l)
    ptt._on_press(key.shift)
    ptt._on_press(listener.keyboard.KeyCode.from_char("t"))
    assert events == ["pressed", "cancelled"]


def test_switching_hotkey_at_runtime(monkeypatch) -> None:
    listener = _listener_module()
    key = listener.keyboard.Key
    ptt, events = _ptt(listener, "Ctrl+Win", monkeypatch)
    ptt._on_press(key.ctrl_l)
    ptt._on_press(key.cmd)
    ptt.set_hotkey("Ctrl+Shift")
    assert events == ["pressed", "cancelled"]
    ptt._on_release(key.cmd)
    ptt._on_release(key.ctrl_l)
    events.clear()
    ptt._on_press(key.ctrl_l)
    ptt._on_press(key.cmd)  # o atalho antigo não grava mais
    assert events == []
    ptt._on_release(key.cmd)
    ptt._on_press(key.shift)
    assert events == ["pressed"]
