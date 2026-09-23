"""Layout das janelas: conteúdo longo rola ou é resumido, nunca se sobrepõe."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QScrollArea


def test_every_settings_tab_scrolls(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from sussurro.llm.modes import ModeStore
    from sussurro.storage.config import Config
    from sussurro.storage.dictionary import Dictionary
    from sussurro.ui.settings_ui import _TABS, SettingsWindow

    win = SettingsWindow(Config(), ModeStore.load(),
                         active_mode_getter=lambda: "raw", dictionary=Dictionary())
    try:
        for key, _label, _color in _TABS:
            pane = win._stack.widget(win._panes[key])  # noqa: SLF001
            assert isinstance(pane, QScrollArea), key
    finally:
        win.close()


def test_settings_notes_wrap_instead_of_being_cut(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from sussurro.llm.modes import ModeStore
    from sussurro.storage.config import Config
    from sussurro.ui.settings_ui import SettingsWindow

    win = SettingsWindow(Config(), ModeStore.load(), active_mode_getter=lambda: "raw")
    try:
        note = win._note_row("texto longo " * 30)  # noqa: SLF001
        assert note.findChild(QLabel).wordWrap()
    finally:
        win.close()


def test_history_preview_is_short_and_single_paragraph() -> None:
    from sussurro.ui.history_ui import _PREVIEW_CHARS, _preview

    assert _preview("curto") == "curto"
    assert _preview("linha um\n\nlinha   dois") == "linha um linha dois"
    long = "palavra " * 100
    out = _preview(long)
    assert out.endswith("…")
    assert len(out) <= _PREVIEW_CHARS + 1
