"""Diálogo de confirmação temático (reusa FramelessWindow)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components.window_frame import FramelessWindow


class ConfirmDialog(FramelessWindow):
    confirmed = Signal()

    def __init__(self, title: str, message: str, confirm_label: str = "Confirmar",
                 danger: bool = True, parent=None) -> None:
        super().__init__(width=340, dialog=True, parent=parent)
        pal = theme.palette()
        wrap = QVBoxLayout()
        wrap.setContentsMargins(22, 20, 22, 18)
        wrap.setSpacing(8)
        self.body.addLayout(wrap)

        t = QLabel(title)
        t.setFont(theme.qfont(16, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        t.setStyleSheet(f"color: {pal.text_primary};")
        wrap.addWidget(t)
        m = QLabel(message)
        m.setFont(theme.qfont(13))
        m.setWordWrap(True)
        m.setStyleSheet(f"color: {pal.text_secondary};")
        wrap.addWidget(m)
        wrap.addSpacing(8)

        foot = QHBoxLayout()
        foot.addStretch(1)
        cancel = kit.SecondaryButton("Cancelar")
        cancel.clicked.connect(self.close)
        foot.addWidget(cancel)
        ok = QPushButton(confirm_label)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        if danger:
            red = pal.state(theme.ERROR)
            ok.setStyleSheet(f"""
            QPushButton {{ background: {theme.rgba(red, 0.16)}; color: {red};
                border: 1px solid {theme.rgba(red, 0.30)}; border-radius: 10px;
                padding: 11px 18px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: {theme.rgba(red, 0.24)}; }}
            """)
        ok.clicked.connect(lambda: (self.confirmed.emit(), self.close()))
        foot.addWidget(ok)
        wrap.addLayout(foot)
