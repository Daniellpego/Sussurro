"""Tile de icone de modo — quadrado arredondado (raio 8) com a cor curada e o
glyph em Geist Mono (branco ou #0E0F12 conforme a cor).

Recebe (color_key, glyph) diretamente — desacoplado do registro de modo, então
serve tanto pros cards/HUD quanto pro seletor de ícone do editor.
Tamanhos: 28 (card), 44 (header do editor), 30 (seletor).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme


class ModeIconTile(QWidget):
    def __init__(self, color_key: str, glyph: str, size: int = 28,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color_key = color_key
        self._glyph = glyph
        self._size = size
        self.setFixedSize(size, size)

    def set_mode(self, color_key: str, glyph: str) -> None:
        self._color_key = color_key
        self._glyph = glyph
        self.update()

    def apply_theme(self) -> None:
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        light = not theme.is_dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self._size, self._size)
        radius = theme.RADIUS_TILE * (self._size / 28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(theme.mode_swatch(self._color_key, light)))
        p.drawRoundedRect(rect, radius, radius)

        glyph_fs = max(9, round(self._size * 0.42))
        p.setFont(theme.qfont(glyph_fs, theme.W_SEMIBOLD, mono=True))
        p.setPen(theme.qcolor(theme.mode_glyph_color(self._color_key)))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._glyph)
