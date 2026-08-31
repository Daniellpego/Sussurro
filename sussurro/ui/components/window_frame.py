"""Janela frameless com cantos arredondados (16px) + sombra suave.

Base reutilizavel: janela principal, Historico, Ajustes, Editor de modo. O
top-level e translucido; o "card" interno (#WindowRoot) tem bg + borda + raio
e ganha a sombra via QGraphicsDropShadowEffect (QSS nao tem box-shadow). Uma
margem externa reserva espaco pra sombra nao ser cortada.

Adicione conteudo em `self.body` (QVBoxLayout do root).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QVBoxLayout,
    QWidget,
)

from sussurro.ui import theme

_SHADOW_MARGIN = 30

# Efeito vidro (acrílico do Windows 11) — opt-in. Quando ligado, a janela vira o
# próprio card (sem margem/sombra manual) pra o blur do DWM preencher limpo.
_GLASS = False
GLASS_BG_ALPHA = 0.62  # opacidade do card sobre o acrílico (afinável)


def set_glass(enabled: bool) -> None:
    """Liga/desliga o efeito vidro pra novas janelas (lido no __init__)."""
    global _GLASS
    _GLASS = bool(enabled)


def glass_enabled() -> bool:
    return _GLASS


class FramelessWindow(QWidget):
    def __init__(self, *, width: int | None = None, dialog: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._glass = _GLASS  # fixa o modo na criação (estável p/ esta janela)
        flags = Qt.WindowType.FramelessWindowHint
        flags |= Qt.WindowType.Dialog if dialog else Qt.WindowType.Window
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        # sem vidro: margem reserva espaço pra sombra manual. com vidro: a janela
        # é o card (DWM dá sombra + cantos), então margem zero.
        m = 0 if self._glass else _SHADOW_MARGIN
        outer.setContentsMargins(m, m, m, m)
        outer.setSpacing(0)

        self._root = QFrame(self)
        self._root.setObjectName("WindowRoot")
        if width is not None:
            self._root.setFixedWidth(width)
        outer.addWidget(self._root)

        if self._glass:
            self._shadow = None  # DWM cuida da sombra
        else:
            self._shadow = QGraphicsDropShadowEffect(self)
            self._shadow.setBlurRadius(40)
            self._shadow.setOffset(0, 16)
            self._root.setGraphicsEffect(self._shadow)

        self.body = QVBoxLayout(self._root)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)

        self.apply_theme()

    def showEvent(self, e) -> None:  # noqa: N802
        super().showEvent(e)
        self._apply_backdrop()

    def _apply_backdrop(self) -> None:
        if not self._glass:
            return
        from sussurro.ui import win_backdrop
        win_backdrop.apply_backdrop(
            int(self.winId()), dark=theme.is_dark(),
            kind=win_backdrop.BACKDROP_ACRYLIC)

    def apply_theme(self) -> None:
        pal = theme.palette()
        if self._glass:
            # card semi-transparente pra o acrílico aparecer; sombra/cantos = DWM
            bg = theme.rgba(pal.window, GLASS_BG_ALPHA)
            self._root.setStyleSheet(f"""
            QFrame#WindowRoot {{
                background: {bg};
                border: 1px solid {pal.border_subtle};
                border-radius: {theme.RADIUS_WINDOW}px;
            }}
            """)
            self._apply_backdrop()  # reaplica tint dark/light se já visível
            return
        sh = theme.SHADOWS["window_dark" if pal.is_dark else "window_light"]
        self._shadow.setColor(theme.qcolor(
            f"rgba({sh.color[0]},{sh.color[1]},{sh.color[2]},{sh.color[3] / 255:.3f})"))
        self._root.setStyleSheet(f"""
        QFrame#WindowRoot {{
            background: {pal.window};
            border: 1px solid {pal.border_subtle};
            border-radius: {theme.RADIUS_WINDOW}px;
        }}
        """)
