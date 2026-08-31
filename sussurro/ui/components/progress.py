"""Barra de progresso — trilho 6px raio 3, preenchimento gradiente da marca.

Trilho: rgba(255,255,255,0.08) (dark) / #E4E5EA (light), via palette. Quando
`value` (0.0-1.0) e None ou 0 e o trilho fica vazio (estado "na fila").
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from sussurro.ui import theme

_H = 6


class ProgressBar(QWidget):
    def __init__(self, value: float = 0.0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = max(0.0, min(1.0, value))
        self.setFixedHeight(_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def apply_theme(self) -> None:
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = _H / 2

        track = QRectF(0, 0, self.width(), _H)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(pal.progress_track))
        p.drawRoundedRect(track, r, r)

        if self._value > 0.001:
            w = self.width() * self._value
            fill = QRectF(0, 0, max(w, _H), _H)
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0.0, theme.qcolor(theme.GRAD_A))
            grad.setColorAt(1.0, theme.qcolor(theme.GRAD_B))
            p.setBrush(grad)
            p.drawRoundedRect(fill, r, r)
