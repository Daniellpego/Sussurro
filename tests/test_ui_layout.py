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


def test_no_placeholder_features_in_the_ui() -> None:
    """Nada de controles "em breve": cada item da interface precisa funcionar."""
    from pathlib import Path

    ui = Path(__file__).resolve().parents[1] / "sussurro" / "ui"
    offenders = [
        f.name for f in ui.rglob("*.py")
        if "em breve" in f.read_text(encoding="utf-8").lower()
        and f.name != "settings_ui.py"  # só na docstring que explica a regra
    ]
    assert offenders == []


def test_read_only_value_row_ignores_clicks() -> None:
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from sussurro.ui.components import ValueRow

    row = ValueRow("Atalho de teclado", "Ctrl + Win", interactive=False)
    clicks: list[bool] = []
    row.clicked.connect(lambda: clicks.append(True))
    row.resize(300, 40)
    pos = QPointF(10, 10)
    event = QMouseEvent(QMouseEvent.Type.MouseButtonRelease, pos, pos,
                        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier)
    row.mouseReleaseEvent(event)
    assert clicks == []
    assert row._chevron.isHidden()  # noqa: SLF001


def test_main_window_reflects_changes_made_in_settings(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from sussurro.llm.modes import ModeStore
    from sussurro.storage.config import Config
    from sussurro.storage.history import History
    from sussurro.ui import labels
    from sussurro.ui.window import MainWindow

    cfg = Config()
    win = MainWindow(cfg, History(), ModeStore.load())
    try:
        cfg.mic_device = "Microfone (USB Audio Device)"
        cfg.language = "en"
        win.sync_from_config()
        assert "USB Audio" in win._mic_row._value._text  # noqa: SLF001
        assert win._lang_row._value._text == labels.LANGUAGE["en"]  # noqa: SLF001
    finally:
        win.close()


def test_mode_editor_saves_selected_ollama_model(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from sussurro.llm.modes import ModeStore
    from sussurro.llm.worker import LLMWorker
    from sussurro.ui.modes_ui import ModeEditor, QInputDialog

    store = ModeStore.load()
    editor = ModeEditor(store, "clean")
    try:
        monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("meu-modelo:latest", True))
        assert editor._model_row._interactive  # noqa: SLF001
        editor._pick_model()  # noqa: SLF001
        assert editor._model_row._value._text == "meu-modelo:latest"  # noqa: SLF001
        editor._save()  # noqa: SLF001
        assert ModeStore.load().get("clean").model == "meu-modelo:latest"
        assert LLMWorker(store)._resolve_model("clean") == "meu-modelo:latest"  # noqa: SLF001
    finally:
        editor.close()
