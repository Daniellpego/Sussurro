from __future__ import annotations

from sussurro.inject import paste


def _patch_common(monkeypatch, *, non_text: bool):
    events: list[tuple[str, object]] = []
    monkeypatch.setattr(paste, "elevation_blocks_paste", lambda: False)
    monkeypatch.setattr(paste, "_clipboard_has_non_text", lambda: non_text)
    monkeypatch.setattr(paste, "_try_type", lambda text: events.append(("type", text)) or True)
    monkeypatch.setattr(paste, "_try_chord", lambda chord: events.append(("chord", chord)) or True)
    monkeypatch.setattr(paste, "_copy_to_clipboard", lambda text: events.append(("copy", text)) or True)
    monkeypatch.setattr(paste, "_restore_clipboard", lambda prev, text: events.append(("restore", prev)))
    monkeypatch.setattr(paste.pyperclip, "paste", lambda: "texto copiado antes")
    return events


def test_image_on_clipboard_is_preserved_by_typing(monkeypatch) -> None:
    events = _patch_common(monkeypatch, non_text=True)
    result = paste.paste_text("olá", method="auto")
    assert result.ok and result.method == "type"
    assert ("type", "olá") in events
    assert not any(kind == "copy" for kind, _ in events)
    # nada de "restaurar" um texto vazio por cima da imagem
    assert ("restore", "") not in events


def test_text_on_clipboard_still_uses_ctrl_v_and_restores(monkeypatch) -> None:
    events = _patch_common(monkeypatch, non_text=False)
    result = paste.paste_text("olá", method="auto")
    assert result.ok and result.method == "ctrl+v"
    assert events == [
        ("copy", "olá"),
        ("chord", "ctrl+v"),
        ("restore", "texto copiado antes"),
    ]


def test_forced_method_without_fallback_keeps_user_choice(monkeypatch) -> None:
    events = _patch_common(monkeypatch, non_text=True)
    result = paste.paste_text("olá", method="ctrl+v", auto_fallback=False)
    assert result.ok and result.method == "ctrl+v"
    assert events[:2] == [("copy", "olá"), ("chord", "ctrl+v")]


def test_typing_first_keeps_other_fallbacks() -> None:
    assert paste._typing_first(["ctrl+v", "shift+insert", "type"]) == [
        "type", "ctrl+v", "shift+insert",
    ]
    assert paste._typing_first(["ctrl+v"]) == ["ctrl+v"]
