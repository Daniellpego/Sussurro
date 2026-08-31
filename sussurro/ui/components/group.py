"""Grupo estilo Ajustes Apple — card com linhas divididas.

GroupCard: container surface, raio 12, borda sutil, linhas empilhadas com
divisor entre elas (exceto a ultima). Linhas:
- ValueRow: label esquerda + (dot opcional + valor + chevron). Clicavel.
- ToggleRow: label esquerda + IOSToggle a direita.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from sussurro.ui import theme
from sussurro.ui.components.chevron import Chevron
from sussurro.ui.components.toggle import IOSToggle


class _Divider(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), theme.qcolor(theme.palette().divider))


class _Dot(QWidget):
    def __init__(self, color: str, d: int = 7, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self._d = d
        self.setFixedSize(d, d)

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._color))
        p.drawEllipse(QRectF(0, 0, self._d, self._d))


class _ValueLabel(QWidget):
    """Valor da ValueRow: [dot opcional] + texto, alinhado à direita, com
    ELIDE (…) quando longo — evita clipar/colidir com o label (ex.: nome de
    mic comprido). Ocupa o espaço do meio (stretch) e ancora à direita."""

    _DOT = 7
    _DOT_GAP = 7

    def __init__(self, text: str = "", dot_color: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self._dot_color = dot_color
        self._color = theme.palette().text_secondary
        self._font = theme.qfont(13, theme.W_MEDIUM)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(24)

    def set_value(self, text: str, dot_color: str | None = None) -> None:
        self._text = text
        self._dot_color = dot_color
        self.update()

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def set_font_(self, font) -> None:
        self._font = font
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = QFontMetrics(self._font)
        return QSize(24, fm.height())

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)
        fm = QFontMetrics(self._font)
        dot_w = (self._DOT + self._DOT_GAP) if self._dot_color else 0
        elided = fm.elidedText(self._text, Qt.TextElideMode.ElideRight,
                               max(10, self.width() - dot_w))
        tw = fm.horizontalAdvance(elided)
        cy = self.height() / 2
        x = self.width() - tw - dot_w   # ancora à direita
        if self._dot_color:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(theme.qcolor(self._dot_color))
            p.drawEllipse(QRectF(x, cy - self._DOT / 2, self._DOT, self._DOT))
            x += self._DOT + self._DOT_GAP
        p.setPen(theme.qcolor(self._color))
        p.drawText(QRectF(x, 0, tw + 2, self.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   elided)


class _Row(QWidget):
    """Base: bg transparente + hover styled. Padding horizontal 14px."""

    def __init__(self, pad_v: int = 13, hover: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._hover = hover
        self.setObjectName("GroupRow")
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(14, pad_v, 14, pad_v)
        self._lay.setSpacing(7)
        self._apply_row_style()

    def _apply_row_style(self) -> None:
        pal = theme.palette()
        if self._hover:
            self.setStyleSheet(
                f"QWidget#GroupRow {{ background: transparent; }}"
                f"QWidget#GroupRow:hover {{ background: {pal.hover}; }}"
            )
        else:
            self.setStyleSheet("QWidget#GroupRow { background: transparent; }")

    def apply_theme(self) -> None:
        self._apply_row_style()
        for ch in self.findChildren(QWidget):
            fn = getattr(ch, "apply_theme", None)
            if callable(fn):
                fn()


class ValueRow(_Row):
    """Linha label -> valor + chevron. Clique emite `clicked`."""

    clicked = Signal()

    def __init__(self, label: str, value: str = "", dot_color: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(pad_v=13, hover=True, parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._label = QLabel(label)
        self._label.setObjectName("RowLabel")
        self._label.setSizePolicy(QSizePolicy.Policy.Maximum,
                                  QSizePolicy.Policy.Preferred)
        self._lay.addWidget(self._label)

        self._value = _ValueLabel(value, dot_color)
        self._lay.addWidget(self._value, 1)   # ocupa o meio + elide à direita
        self._chevron = Chevron()
        self._lay.addWidget(self._chevron, 0, Qt.AlignmentFlag.AlignVCenter)
        self.apply_theme()

    def set_value(self, value: str, dot_color: str | None = None) -> None:
        self._value.set_value(value, dot_color)

    def apply_theme(self) -> None:
        super().apply_theme()
        pal = theme.palette()
        self._label.setFont(theme.qfont(13.5, theme.W_MEDIUM))
        self._label.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        if hasattr(self, "_value"):
            self._value.set_font_(theme.qfont(13, theme.W_MEDIUM))
            self._value.set_color(pal.text_secondary)
            self._chevron.set_color(pal.text_tertiary)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()


class ToggleRow(_Row):
    """Linha label -> toggle iOS. `toggled(bool)` repassa o estado."""

    toggled = Signal(bool)

    def __init__(self, label: str, checked: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(pad_v=11, hover=False, parent=parent)
        self._label = QLabel(label)
        self._label.setObjectName("RowLabel")
        self._lay.addWidget(self._label)
        self._lay.addStretch(1)
        self._toggle = IOSToggle(checked)
        self._toggle.toggled.connect(self.toggled.emit)
        self._lay.addWidget(self._toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        self.apply_theme()

    def is_checked(self) -> bool:
        return self._toggle.is_checked()

    def set_checked(self, checked: bool, *, animate: bool = False) -> None:
        self._toggle.set_checked(checked, animate=animate)

    def apply_theme(self) -> None:
        super().apply_theme()
        pal = theme.palette()
        self._label.setFont(theme.qfont(13.5, theme.W_MEDIUM))
        self._label.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")


class GroupCard(QFrame):
    """Container de linhas (com divisores). Use add_row()."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GroupCard")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)
        self._rows: list[QWidget] = []
        self.apply_theme()

    def add_row(self, row: QWidget) -> QWidget:
        if self._rows:
            self._lay.addWidget(_Divider(self))
        self._lay.addWidget(row)
        self._rows.append(row)
        return row

    def clear(self) -> None:
        """Remove todas as linhas e divisores."""
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._rows = []

    def apply_theme(self) -> None:
        pal = theme.palette()
        self.setStyleSheet(f"""
        QFrame#GroupCard {{
            background: {pal.surface};
            border: 1px solid {pal.border_subtle};
            border-radius: {theme.RADIUS_CARD}px;
        }}
        """)
        for ch in self.findChildren(QWidget):
            if ch is self:
                continue
            fn = getattr(ch, "apply_theme", None)
            if callable(fn):
                fn()
