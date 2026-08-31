"""System tray — ícone (brand mark) + popup rico custom (tela 08).

Clique simples/direito no ícone abre o popup; duplo-clique abre a janela.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QSystemTrayIcon

from sussurro.llm.modes import ModeStore
from sussurro.ui import theme
from sussurro.ui.components import brand_icon
from sussurro.ui.tray_popup import TrayPopup

# kind -> (texto, token de estado | "indigo")
_STATUS = {
    "ready":     ("Ativo", "ready"),
    "loading":   ("Carregando", "warning"),
    "recording": ("Ouvindo", "indigo"),
    "error":     ("Erro", "error"),
    "paused":    ("Em espera", "warning"),
}


class Tray(QObject):
    show_window_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()
    pause_toggled = Signal(bool)
    quit_requested = Signal()
    mode_selected = Signal(str)

    def __init__(self, store: ModeStore, active_mode_getter) -> None:
        super().__init__()
        self._store = store
        self._active_mode_getter = active_mode_getter
        self._icon: QIcon = brand_icon()
        self._tray = QSystemTrayIcon(self._icon)
        self._tray.setToolTip("Sussurro — segure Ctrl+Win pra falar")
        self._paused = False
        self._status_kind = "loading"
        self._popup: TrayPopup | None = None
        self._tray.activated.connect(self._on_activated)

    # ------------------------------------------------------------------- API

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def notify(self, title: str, message: str,
               kind: QSystemTrayIcon.MessageIcon | None = None) -> None:
        icon = kind or QSystemTrayIcon.MessageIcon.Information
        self._tray.showMessage(title, message, icon, 2500)

    def set_status(self, kind: str) -> None:
        self._status_kind = kind
        if kind == "paused":
            self._tray.setToolTip("Sussurro em espera — clique e ative pra falar")
        elif kind == "ready":
            self._tray.setToolTip("Sussurro ativo — segure Ctrl+Win pra falar")
        elif kind == "loading":
            self._tray.setToolTip("Sussurro — carregando modelo…")
        else:
            self._tray.setToolTip("Sussurro")

    def set_paused(self, paused: bool) -> None:
        """Sincroniza estado armado/espera (ex.: boot em standby)."""
        self._paused = paused
        self.set_status("paused" if paused else "ready")

    @property
    def is_paused(self) -> bool:
        return self._paused

    # --------------------------------------------------------------- interna

    def _status_tuple(self) -> tuple[str, str]:
        text, token = _STATUS.get(self._status_kind, ("Pronto", "ready"))
        if token == "indigo":
            color = theme.INDIGO
        elif token in ("ready", "warning", "error"):
            state = {"ready": theme.READY, "warning": theme.WARNING,
                     "error": theme.ERROR}[token]
            color = theme.palette().state(state)
        else:
            color = theme.palette().text_secondary
        return color, text

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
        elif reason in (QSystemTrayIcon.ActivationReason.Trigger,
                        QSystemTrayIcon.ActivationReason.Context):
            self._show_popup()

    def _show_popup(self) -> None:
        self._popup = TrayPopup(
            self._store, self._active_mode_getter(),
            self._status_tuple(), self._paused)
        self._popup.open_window.connect(self.show_window_requested.emit)
        self._popup.open_history.connect(self.history_requested.emit)
        self._popup.open_settings.connect(self.settings_requested.emit)
        self._popup.toggle_pause.connect(self._toggle_pause)
        self._popup.quit_app.connect(self.quit_requested.emit)
        self._popup.pick_mode.connect(self.mode_selected.emit)

        anchor = self._tray.geometry().center() if not self._tray.geometry().isEmpty() \
            else QCursor.pos()
        if isinstance(anchor, QPoint):
            self._popup.popup_at(anchor)
        else:
            self._popup.popup_at(QCursor.pos())

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self.set_status("paused" if self._paused else "ready")
        self.pause_toggled.emit(self._paused)
