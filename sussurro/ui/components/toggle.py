"""Toggle iOS — trilho com gradiente da marca quando ligado, bolinha branca.

Ligado: trilho gradiente indigo->rosa, bolinha a direita. Desligado: trilho
cinza (palette.toggle_off), bolinha a esquerda. A posicao da bolinha anima em
~150ms. Tres tamanhos: default / small / large (theme.TOGGLE_*).
"""
from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from sussurro.ui import theme


class IOSToggle(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, size: str = "default",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        track_w, track_h, radius, knob = {
            "default": theme.TOGGLE_DEFAULT,
            "small": theme.TOGGLE_SMALL,
            "large": theme.TOGGLE_LARGE,
        }.get(size, theme.TOGGLE_DEFAULT)
        self._tw, self._th, self._radius, self._knob = track_w, track_h, radius, knob
        self._pad = 2
        self._checked = checked
        self._t = 1.0 if checked else 0.0   # 0=esq, 1=dir

        self.setFixedSize(track_w, track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"slide", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    # --- propriedade animavel (posicao da bolinha) ---
    def _get_slide(self) -> float:
        return self._t

    def _set_slide(self, v: float) -> None:
        self._t = v
        self.update()

    slide = Property(float, _get_slide, _set_slide)

    # --- API ---
    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool, *, animate: bool = True) -> None:
        if checked == self._checked:
            return
        self._checked = checked
        target = 1.0 if checked else 0.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._t)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._set_slide(target)

    def toggle(self) -> None:
        self.set_checked(not self._checked)
        self.toggled.emit(self._checked)

    def apply_theme(self) -> None:
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = QRectF(0, 0, self._tw, self._th)
        p.setPen(Qt.PenStyle.NoPen)

        if self._t <= 0.001:
            p.setBrush(theme.qcolor(pal.toggle_off))
            p.drawRoundedRect(track, self._radius, self._radius)
        else:
            grad = QLinearGradient(0, 0, self._tw, self._th)
            grad.setColorAt(0.0, theme.qcolor(theme.GRAD_A))
            grad.setColorAt(1.0, theme.qcolor(theme.GRAD_B))
            if self._t < 0.999:
                # crossfade simples: pinta off, depois gradiente com alpha
                p.setBrush(theme.qcolor(pal.toggle_off))
                p.drawRoundedRect(track, self._radius, self._radius)
                p.setOpacity(self._t)
            p.setBrush(grad)
            p.drawRoundedRect(track, self._radius, self._radius)
            p.setOpacity(1.0)

        # bolinha
        travel = self._tw - 2 * self._pad - self._knob
        x = self._pad + travel * self._t
        y = self._pad
        p.setBrush(theme.qcolor("#FFFFFF"))
        p.drawEllipse(QRectF(x, y, self._knob, self._knob))
