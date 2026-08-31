"""Keycap — tecla fisica em Geist Mono, com sombra inferior solida (0 2px 0).

QSS nao tem box-shadow, entao pintamos: um retangulo escuro deslocado dy abaixo
(a "sombra dura") + o corpo da tecla por cima + o glyph centralizado. Dois
tamanhos: normal (atalhos inline) e large (onboarding/atalho).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme


class Keycap(QWidget):
    def __init__(self, text: str, large: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        if large:
            self._pad_h, self._pad_v = 20, 16
            self._radius = theme.RADIUS_KEYCAP_LG
            self._fs = 19
            self._dy = 3
        else:
            self._pad_h, self._pad_v = 11, 7
            self._radius = theme.RADIUS_KEYCAP
            self._fs = 13
            self._dy = 2
        self._font = theme.qfont(self._fs, theme.W_SEMIBOLD, mono=True)
        fm = QFontMetrics(self._font)
        w = fm.horizontalAdvance(text) + self._pad_h * 2
        h = fm.height() + self._pad_v * 2
        self.setFixedSize(w, h + self._dy)

    def apply_theme(self) -> None:
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        body = QRectF(0, 0, self.width(), self.height() - self._dy)

        # sombra dura (sem blur) deslocada dy
        shadow = theme.qcolor("#000000")
        shadow.setAlphaF(0.25 if pal.is_dark else 0.0)
        if not pal.is_dark:
            shadow = theme.qcolor("#141628")
            shadow.setAlphaF(0.06)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(shadow)
        p.drawRoundedRect(body.translated(0, self._dy), self._radius, self._radius)

        # corpo
        bg = theme.qcolor(pal.hover if pal.is_dark else "#FFFFFF")
        p.setBrush(bg)
        p.drawRoundedRect(body, self._radius, self._radius)
        # borda forte
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(theme.qcolor(pal.border_strong))
        p.drawRoundedRect(body.adjusted(0.5, 0.5, -0.5, -0.5),
                          self._radius, self._radius)

        # texto
        p.setFont(self._font)
        p.setPen(theme.qcolor(pal.text_primary))
        p.drawText(body, Qt.AlignmentFlag.AlignCenter, self._text)
