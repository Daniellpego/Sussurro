"""Title bar custom (frameless) — wordmark OU titulo + botoes.

Main window: wordmark "sussurro" (mono uppercase) + [engrenagem opcional] +
minimizar + fechar. Dialogos (Historico/Ajustes/Editor): titulo + fechar.
Arrastavel (move a janela top-level). Palette-driven.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from sussurro.ui import icons, theme


class WindowTitleBar(QWidget):
    minimize_requested = Signal()
    close_requested = Signal()
    settings_requested = Signal()

    def __init__(self, title: str | None = None, *, wordmark: bool = False,
                 show_minimize: bool = True, show_settings: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(theme.TITLEBAR_HEIGHT)
        self._wordmark = wordmark
        self._title_text = title or ("sussurro" if wordmark else "")
        self._drag_pos = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 10, 0)
        lay.setSpacing(8)

        self._label = QLabel(self._title_text, self)
        self._label.setObjectName("TitleWordmark" if wordmark else "TitleText")
        lay.addWidget(self._label)
        lay.addStretch(1)

        self._btn_settings = self._mk("settings") if show_settings else None
        if self._btn_settings:
            self._btn_settings.clicked.connect(self.settings_requested.emit)
            lay.addWidget(self._btn_settings)

        self._btn_min = self._mk("minimize") if show_minimize else None
        if self._btn_min:
            self._btn_min.clicked.connect(self.minimize_requested.emit)
            lay.addWidget(self._btn_min)

        self._btn_close = self._mk("close", is_close=True)
        self._btn_close.clicked.connect(self.close_requested.emit)
        lay.addWidget(self._btn_close)

        self.apply_theme()

    def _mk(self, icon_name: str, is_close: bool = False) -> QPushButton:
        btn = QPushButton(self)
        btn.setObjectName("TitleClose" if is_close else "TitleBtn")
        btn.setProperty("iconName", icon_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(24, 24)
        btn.setIconSize(QSize(14, 14))
        return btn

    def set_title(self, text: str) -> None:
        self._title_text = text
        self._label.setText(text)

    def apply_theme(self) -> None:
        pal = theme.palette()
        # icones recolorem conforme tema
        for btn in (self._btn_settings, self._btn_min, self._btn_close):
            if btn is not None:
                name = btn.property("iconName")
                btn.setIcon(icons.icon(name, color=pal.text_tertiary, size=14))

        if self._wordmark:
            self._label.setFont(theme.qfont(11, theme.W_SEMIBOLD, mono=True,
                                            tracking=theme.TRACK_WORDMARK))
            self._label.setStyleSheet(
                f"color: {pal.text_tertiary}; background: transparent;")
        else:
            self._label.setFont(theme.qfont(13, theme.W_SEMIBOLD))
            self._label.setStyleSheet(
                f"color: {pal.text_primary}; background: transparent;")

        self.setStyleSheet(f"""
        QWidget#TitleBar {{ background: transparent; }}
        QPushButton#TitleBtn, QPushButton#TitleClose {{
            background: transparent; border: none; border-radius: {theme.RADIUS_TILE_BTN}px;
        }}
        QPushButton#TitleBtn:hover {{ background: {pal.hover}; }}
        QPushButton#TitleClose:hover {{ background: {theme.rgba(theme.ERROR.dark, 0.9)}; }}
        """)

    # --- arrastar a janela ---
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_pos is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        delta = event.globalPosition().toPoint() - self._drag_pos
        win = self.window()
        if win is not None:
            win.move(win.pos() + delta)
        self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_pos = None
