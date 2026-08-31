"""Brand mark — 5 barras (forma de onda) com o sweep da marca, num squircle.

Alturas crescente->decrescente, alinhadas pelo centro, sobre squircle escuro
`#14171D` (mesmo no light). Cores = theme.BRAND_SWEEP (5 cores distintas, nao
um gradiente). Tamanhos do README: 46 (janela), 70 (onboarding), 28 (bandeja).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme


def _bars_for(size: int) -> tuple[tuple[int, ...], float, float, float]:
    """(alturas, largura_barra, gap, raio_squircle) por tamanho de mark."""
    if size >= 70:
        return theme.BRAND_BARS_70, 3.0, 4.0, theme.RADIUS_BRAND_70
    if size <= 28:
        return theme.BRAND_BARS_28, 2.0, 2.0, 6.0
    return theme.BRAND_BARS_46, 3.0, 3.0, theme.RADIUS_BRAND_46


def _paint(p: QPainter, size: int) -> None:
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    heights, bar_w, gap, radius = _bars_for(size)

    # squircle de fundo
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(theme.qcolor(theme.BRAND_SQUIRCLE_BG))
    p.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    n = len(heights)
    total_w = n * bar_w + (n - 1) * gap
    x0 = (size - total_w) / 2
    cy = size / 2
    br = bar_w / 2
    for i, h in enumerate(heights):
        x = x0 + i * (bar_w + gap)
        y = cy - h / 2
        p.setBrush(theme.qcolor(theme.BRAND_SWEEP[i]))
        p.drawRoundedRect(QRectF(x, y, bar_w, h), br, br)


def brand_pixmap(size: int = 46) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    _paint(p, size)
    p.end()
    return pix


def brand_icon() -> QIcon:
    ic = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        ic.addPixmap(brand_pixmap(s))
    return ic


class BrandMark(QWidget):
    """Brand mark como widget (escala pra `size`)."""

    def __init__(self, size: int = 46, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        _paint(p, self._size)
