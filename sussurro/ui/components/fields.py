"""Inputs do kit — LineEdit e TextArea, palette-driven.

Fundo inset, borda input, raio 10, foco com borda de acento (link da palette).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QWidget

from sussurro.ui import theme


def _input_qss(obj: str, pal) -> str:
    return f"""
    {obj} {{
        background: {pal.inset};
        border: 1px solid {pal.input_border};
        border-radius: {theme.RADIUS_INPUT}px;
        padding: 9px 12px;
        color: {pal.text_primary};
        font-size: 13px;
        selection-background-color: {theme.rgba(theme.INDIGO, 0.30)};
    }}
    {obj}:focus {{ border: 1px solid {pal.link}; }}
    """


class LineEdit(QLineEdit):
    def __init__(self, text: str = "", placeholder: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("KitLineEdit")
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setFont(theme.qfont(13, theme.W_MEDIUM))
        self.apply_theme()

    def apply_theme(self) -> None:
        self.setStyleSheet(_input_qss("QLineEdit#KitLineEdit", theme.palette()))


class TextArea(QPlainTextEdit):
    def __init__(self, text: str = "", placeholder: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("KitTextArea")
        if text:
            self.setPlainText(text)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setFont(theme.qfont(13, theme.W_REGULAR))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.apply_theme()

    def apply_theme(self) -> None:
        self.setStyleSheet(_input_qss("QPlainTextEdit#KitTextArea", theme.palette()))
