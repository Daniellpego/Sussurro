from __future__ import annotations

from sussurro.storage import autostart


def test_apply_does_not_touch_registry_when_state_matches(monkeypatch) -> None:
    writes: list[bool] = []
    monkeypatch.setattr(autostart, "is_enabled", lambda: True)
    monkeypatch.setattr(autostart, "set_enabled", lambda enabled: writes.append(enabled) or True)

    assert autostart.apply(True) is True
    assert writes == []


def test_apply_writes_when_state_differs(monkeypatch) -> None:
    writes: list[bool] = []
    monkeypatch.setattr(autostart, "is_enabled", lambda: True)
    monkeypatch.setattr(autostart, "set_enabled", lambda enabled: writes.append(enabled) or True)

    assert autostart.apply(False) is True
    assert writes == [False]
