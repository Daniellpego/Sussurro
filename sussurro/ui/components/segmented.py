"""Segmented control (estilo iOS/macOS) — trilho inset, segmento ativo elevado.

Usado pro seletor de tema (Sistema · Claro · Escuro). Pintado pra controlar o
realce do segmento ativo (fundo surface elevado sobre trilho inset).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme

_H = 34
_PAD = 3
_SEG_PAD_H = 16


class SegmentedControl(QWidget):
    changed = Signal(str)   # value selecionado

    def __init__(self, options: list[tuple[str, str]], value: str | None = None,
                 parent: QWidget | None = None) -> None:
        """options = [(value, label), ...]"""
        super().__init__(parent)
        self._options = options
        self._value = value or (options[0][0] if options else "")
        self._font = theme.qfont(12.5, theme.W_MEDIUM)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(_H)
        self._recompute_width()

    def _recompute_width(self) -> None:
        fm = QFontMetrics(self._font)
        seg_w = max((fm.horizontalAdvance(lbl) for _, lbl in self._options),
                    default=40) + _SEG_PAD_H * 2
        self._seg_w = seg_w
        self.setFixedWidth(seg_w * len(self._options) + _PAD * 2)

    def value(self) -> str:
        return self._value

    def set_value(self, value: str, *, emit: bool = False) -> None:
        if value == self._value:
            return
        self._value = value
        self.update()
        if emit:
            self.changed.emit(value)

    def apply_theme(self) -> None:
        self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() != Qt.MouseButton.LeftButton:
            return
        idx = int((e.position().x() - _PAD) // self._seg_w)
        idx = max(0, min(len(self._options) - 1, idx))
        val = self._options[idx][0]
        if val != self._value:
            self._value = val
            self.update()
            self.changed.emit(val)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)

        # trilho
        track = QRectF(0, 0, self.width(), self.height())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(pal.inset))
        p.drawRoundedRect(track, theme.RADIUS_INPUT, theme.RADIUS_INPUT)

        for i, (val, label) in enumerate(self._options):
            x = _PAD + i * self._seg_w
            seg = QRectF(x, _PAD, self._seg_w, self.height() - 2 * _PAD)
            if val == self._value:
                p.setBrush(theme.qcolor(pal.surface))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(seg.adjusted(1, 0, -1, 0), 8, 8)
                p.setPen(theme.qcolor(pal.text_primary))
            else:
                p.setPen(theme.qcolor(pal.text_secondary))
            p.drawText(seg, Qt.AlignmentFlag.AlignCenter, label)
