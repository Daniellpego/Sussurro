"""Chevron `›` — quadrado 6px com border-right + border-top 1.5px rotate(45deg).

No HTML e um span com duas bordas rotacionado; aqui pintamos as duas hastes
do "v deitado" apontando pra direita.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme


class Chevron(QWidget):
    """Seta `›` apontando pra direita. `arm` = tamanho do lado (px)."""

    def __init__(self, arm: int = 6, width: float = 1.5,
                 color: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._arm = arm
        self._w = width
        self._color = color
        # caixa com folga pro stroke nao cortar
        pad = 4
        self.setFixedSize(arm + pad, arm * 2 + pad)

    def set_color(self, color: str | None) -> None:
        self._color = color
        self.update()

    def _resolved(self) -> str:
        return self._color or theme.palette().text_tertiary

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(theme.qcolor(self._resolved()))
        pen.setWidthF(self._w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        cx = self.width() / 2 - self._arm / 2 + 1
        cy = self.height() / 2
        a = self._arm
        # ">" : sobe-desce a partir da ponta direita
        p.drawLine(int(cx), int(cy - a), int(cx + a), int(cy))
        p.drawLine(int(cx + a), int(cy), int(cx), int(cy + a))
