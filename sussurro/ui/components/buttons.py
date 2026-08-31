"""Botoes — primario (gradiente + glow), secundario e ghost.

O primario usa o gradiente da marca + glow (QGraphicsDropShadowEffect, ja que
QSS nao tem box-shadow). Desabilitado: fundo inset, texto dim. Secundario/ghost
derivam da palette ativa. Chamar `apply_theme()` ao trocar de tema.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPushButton, QWidget

from sussurro.ui import theme


class PrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setOffset(0, 8)
        self._glow.setBlurRadius(24)
        self.setGraphicsEffect(self._glow)
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        sh = theme.SHADOWS["btn_glow_dark" if pal.is_dark else "btn_glow_light"]
        self._glow.setColor(theme.qcolor(theme.INDIGO).lighter(100))
        c = theme.qcolor(theme.INDIGO)
        c.setAlpha(sh.color[3])
        self._glow.setColor(c)
        self._glow.setEnabled(self.isEnabled())
        self.setStyleSheet(f"""
        QPushButton#PrimaryButton {{
            background: {theme.GRADIENT};
            color: #FFFFFF;
            border: none;
            border-radius: {theme.RADIUS_INPUT}px;
            padding: 12px 18px;
            font-size: 14px;
            font-weight: {theme.W_SEMIBOLD};
        }}
        QPushButton#PrimaryButton:hover {{
            background: {theme.GRADIENT_HOVER};
        }}
        QPushButton#PrimaryButton:disabled {{
            background: {pal.inset};
            color: {pal.text_tertiary};
        }}
        """)

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        super().setEnabled(enabled)
        if self.graphicsEffect():
            self._glow.setEnabled(enabled)


class SecondaryButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("SecondaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        self.setStyleSheet(f"""
        QPushButton#SecondaryButton {{
            background: {pal.surface};
            color: {pal.text_primary};
            border: 1px solid {pal.border_strong};
            border-radius: {theme.RADIUS_INPUT}px;
            padding: 11px 16px;
            font-size: 13px;
            font-weight: {theme.W_MEDIUM};
        }}
        QPushButton#SecondaryButton:hover {{
            background: {pal.hover};
        }}
        """)


class GhostButton(QPushButton):
    """Texto-link discreto (secundario, sem fundo)."""

    def __init__(self, text: str = "", accent: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("GhostButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._accent = accent
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        color = pal.link if self._accent else pal.text_secondary
        self.setStyleSheet(f"""
        QPushButton#GhostButton {{
            background: transparent;
            color: {color};
            border: none;
            padding: 6px 8px;
            font-size: 12px;
            font-weight: {theme.W_MEDIUM};
        }}
        QPushButton#GhostButton:hover {{
            color: {pal.text_primary if not self._accent else theme.LAVENDER};
        }}
        """)
