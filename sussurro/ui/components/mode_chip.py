"""Chip de modo (no HUD) — fundo = cor do modo a ~16% alpha, texto = cor do
modo, Geist 600 11px. Aceita um registro de Mode ou um id (resolve via store).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme

_PAD_H = 8
_PAD_V = 3
_RADIUS = 7
_FS = 11


def _resolve(mode):
    """Aceita Mode, ou id (str). Retorna (label, color_key)."""
    if isinstance(mode, str):
        from sussurro.llm import modes as M
        mode = M.get(mode)
    return mode.name, mode.color


class ModeChip(QWidget):
    def __init__(self, mode="raw", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._font = theme.qfont(_FS, theme.W_SEMIBOLD)
        self.set_mode(mode)

    def set_mode(self, mode) -> None:
        self._label, self._color_key = _resolve(mode)  # title-case, como o mock
        fm = QFontMetrics(self._font)
        w = fm.horizontalAdvance(self._label) + _PAD_H * 2
        h = fm.height() + _PAD_V * 2
        self.setFixedSize(w, h)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        color = theme.mode_swatch(self._color_key, not theme.is_dark())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(theme.rgba(color, 0.16)))
        p.drawRoundedRect(rect, _RADIUS, _RADIUS)

        p.setFont(self._font)
        p.setPen(theme.qcolor(color))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._label)
