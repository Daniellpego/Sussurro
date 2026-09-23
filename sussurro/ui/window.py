"""Janela principal (tela 01) — hub compacto, design "Sussurro Quiet".

Frameless ~420px: title bar (wordmark) · hero (brand + status + atalho) ·
grupo Configuração (Modo/Microfone/Idioma/Colar) · grupo de toggles · Recentes
(clique copia) · footer (modelos + logs). O histórico completo abre num dialogo.

Contrato com app.py preservado: construtor (config, history, mode_store=),
signals close_to_tray/config_changed, métodos set_status/refresh_history.
"""
from __future__ import annotations

import pyperclip
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QCloseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from sussurro.audio.capture import list_input_devices
from sussurro.llm import modes as M
from sussurro.llm.modes import ModeStore
from sussurro.storage.config import Config
from sussurro.storage.history import History
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components.window_frame import FramelessWindow

_LANG_LABELS: dict[str, str] = {
    "pt": "Português", "en": "English", "auto": "Detectar",
}
_PASTE_LABELS: dict[str, str] = {
    "auto": "Automático",
    "ctrl+v": "Ctrl + V",
    "shift+insert": "Shift + Insert",
    "type": "Digitar",
}
_QUALITY_LABELS: dict[str, str] = {
    "quality": "Qualidade",
    "balanced": "Equilíbrio",
    "light": "Leve",
}

# kind do set_status -> (token de estado | cor fixa)
_STATUS_STATE = {
    "loading": theme.WARNING,
    "ready": theme.READY,
    "error": theme.ERROR,
    "paused": theme.WARNING,  # em espera / economizando VRAM
}


class _StatusDot(QWidget):
    """Bolinha de estado 6px com glow suave."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = theme.READY.dark
        self.setFixedSize(16, 16)

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme.qcolor(self._color)
        # glow
        glow = theme.qcolor(self._color); glow.setAlphaF(0.35)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QRectF(2, 2, 12, 12))
        p.setBrush(c)
        p.drawEllipse(QRectF(5, 5, 6, 6))


class _SectionLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text.upper(), parent)
        self.setFont(theme.qfont(11, theme.W_SEMIBOLD, tracking=theme.TRACK_LABEL))
        self.apply_theme()

    def apply_theme(self) -> None:
        self.setStyleSheet(
            f"color: {theme.palette().text_tertiary}; background: transparent;")


class _RecentRow(QWidget):
    """Linha clicavel: dot do modo + texto truncado + timestamp. Clique copia."""

    def __init__(self, text: str, when: str, mode_key: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full = text
        self.setObjectName("GroupRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clique para copiar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        pal = theme.palette()
        dot_color = theme.mode_swatch(M.get(mode_key).color, not pal.is_dark)
        self._dot = _MiniDot(dot_color)
        lay.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        snippet = text.strip().replace("\n", " ")
        self._body = _ElidedLabel(snippet, pal.text_body_card, self)
        self._body.setFont(theme.qfont(13, theme.W_REGULAR))
        lay.addWidget(self._body, 1)

        self._ts = QLabel(when, self)
        self._ts.setFont(theme.qfont(11, theme.W_MEDIUM, mono=True))
        self._ts.setStyleSheet(
            f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(self._ts, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setStyleSheet(
            f"QWidget#GroupRow {{ background: transparent; }}"
            f"QWidget#GroupRow:hover {{ background: {pal.hover}; }}"
        )

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                pyperclip.copy(self._full)
            except Exception:  # noqa: BLE001
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(self._full)


class _ElidedLabel(QLabel):
    """QLabel que trunca por largura com '…' (estilo text-overflow:ellipsis)."""

    def __init__(self, text: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full = text
        self._color = color
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        from PySide6.QtGui import QFontMetrics
        p = QPainter(self)
        p.setFont(self.font())
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(self._full, Qt.TextElideMode.ElideRight, self.width())
        p.setPen(theme.qcolor(self._color))
        p.drawText(self.rect(),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   elided)


class _MiniDot(QWidget):
    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(6, 6)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._color))
        p.drawEllipse(self.rect())


class MainWindow(FramelessWindow):
    close_to_tray = Signal()
    config_changed = Signal()
    settings_requested = Signal()

    def __init__(self, config: Config, history: History,
                 mode_store: ModeStore | None = None) -> None:
        super().__init__(width=420)
        self._cfg = config
        self._history = history
        self._mode_store = mode_store or ModeStore.load()
        self._history_dialog = None

        if config.window_x is not None and config.window_y is not None:
            self.move(config.window_x, config.window_y)

        self._build()

    # ----------------------------------------------------------------- build

    def _build(self) -> None:
        # title bar (wordmark) + engrenagem -> abre Ajustes
        self._title = kit.WindowTitleBar(
            wordmark=True, show_minimize=True, show_settings=True)
        self._title.minimize_requested.connect(self.showMinimized)
        self._title.close_requested.connect(self._on_close_clicked)
        self._title.settings_requested.connect(self.settings_requested.emit)
        self.body.addWidget(self._title)

        content = QVBoxLayout()
        content.setContentsMargins(16, 2, 16, 0)
        content.setSpacing(0)
        self.body.addLayout(content)

        content.addWidget(self._build_hero())
        content.addSpacing(18)

        content.addWidget(_SectionLabel("Configuração"))
        content.addSpacing(6)
        content.addWidget(self._build_config_group())
        content.addSpacing(16)

        content.addWidget(self._build_toggles_group())
        content.addSpacing(16)

        # Recentes header (label + link histórico)
        rec_head = QHBoxLayout()
        rec_head.setContentsMargins(0, 0, 0, 0)
        rec_head.addWidget(_SectionLabel("Recentes"))
        rec_head.addStretch(1)
        hist_link = kit.GhostButton("histórico", accent=True)
        hist_link.clicked.connect(self._open_history)
        rec_head.addWidget(hist_link)
        content.addLayout(rec_head)
        content.addSpacing(6)

        self._recent_card = kit.GroupCard()
        content.addWidget(self._recent_card)
        content.addSpacing(8)

        content.addWidget(self._build_footer())

        self.refresh_history()
        self._root.adjustSize()
        self.adjustSize()

    def _build_hero(self) -> QWidget:
        pal = theme.palette()
        card = QWidget()
        card.setObjectName("HeroCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
        QWidget#HeroCard {{
            background: {pal.surface};
            border: 1px solid {pal.border_subtle};
            border-radius: {theme.RADIUS_CARD_LG}px;
        }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 22, 20, 22)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lay.addWidget(kit.BrandMark(46), 0, Qt.AlignmentFlag.AlignHCenter)

        # nome + status
        head = QVBoxLayout()
        head.setSpacing(5)
        head.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name = QLabel("Sussurro")
        name.setFont(theme.qfont(19, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        name.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        head.addWidget(name, 0, Qt.AlignmentFlag.AlignHCenter)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._status_dot = _StatusDot()
        status_row.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        self._status_lbl = QLabel("carregando…")
        self._status_lbl.setFont(theme.qfont(12, theme.W_MEDIUM))
        self._status_lbl.setStyleSheet(
            f"color: {pal.text_secondary}; background: transparent;")
        status_row.addWidget(self._status_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        sr = QWidget(); sr.setLayout(status_row)
        head.addWidget(sr, 0, Qt.AlignmentFlag.AlignHCenter)
        hw = QWidget(); hw.setLayout(head)
        lay.addWidget(hw, 0, Qt.AlignmentFlag.AlignHCenter)

        # keycaps
        keys = QHBoxLayout()
        keys.setSpacing(7)
        keys.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        keys.addWidget(kit.Keycap("Ctrl"))
        plus = QLabel("+")
        plus.setFont(theme.qfont(12))
        plus.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        keys.addWidget(plus)
        keys.addWidget(kit.Keycap("Win"))
        hint = QLabel("segure pra falar")
        hint.setFont(theme.qfont(12))
        hint.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        keys.addSpacing(6)
        keys.addWidget(hint)
        kw = QWidget(); kw.setLayout(keys)
        lay.addWidget(kw, 0, Qt.AlignmentFlag.AlignHCenter)

        return card

    def _build_config_group(self) -> QWidget:
        pal = theme.palette()
        card = kit.GroupCard()

        mode = self._mode_store.get(self._cfg.default_mode)
        self._mode_row = kit.ValueRow(
            "Modo", mode.name,
            dot_color=theme.mode_swatch(mode.color, not pal.is_dark))
        self._mode_row.clicked.connect(self._pick_mode)
        card.add_row(self._mode_row)

        self._mic_row = kit.ValueRow("Microfone", self._mic_label())
        self._mic_row.clicked.connect(self._pick_mic)
        card.add_row(self._mic_row)

        self._lang_row = kit.ValueRow(
            "Idioma", _LANG_LABELS.get(self._cfg.language, "Detectar"))
        self._lang_row.clicked.connect(self._pick_lang)
        card.add_row(self._lang_row)

        self._paste_row = kit.ValueRow(
            "Colar", _PASTE_LABELS.get(self._cfg.paste_method, "Automático"))
        self._paste_row.clicked.connect(self._pick_paste)
        card.add_row(self._paste_row)

        self._quality_row = kit.ValueRow(
            "Qualidade ASR",
            _QUALITY_LABELS.get(self._cfg.quality_preset, "Qualidade"))
        self._quality_row.clicked.connect(self._pick_quality)
        card.add_row(self._quality_row)

        return card

    def _build_toggles_group(self) -> QWidget:
        card = kit.GroupCard()
        self._tg_autostart = kit.ToggleRow(
            "Iniciar com o Windows", self._cfg.autostart)
        self._tg_autostart.toggled.connect(self._on_autostart)
        card.add_row(self._tg_autostart)

        self._tg_paste = kit.ToggleRow(
            "Colar automaticamente", self._cfg.paste_after_transcribe)
        self._tg_paste.toggled.connect(self._on_paste_toggle)
        card.add_row(self._tg_paste)

        self._tg_overlay = kit.ToggleRow(
            "Mostrar overlay", self._cfg.show_overlay)
        self._tg_overlay.toggled.connect(self._on_overlay_toggle)
        card.add_row(self._tg_overlay)
        return card

    def _build_footer(self) -> QWidget:
        pal = theme.palette()
        foot = QWidget()
        foot.setObjectName("Footer")
        foot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        foot.setStyleSheet(
            f"QWidget#Footer {{ background: transparent; "
            f"border-top: 1px solid {pal.divider}; }}")
        lay = QHBoxLayout(foot)
        lay.setContentsMargins(0, 12, 0, 12)
        models = QLabel(f"{self._cfg.model_size} · qwen2.5")
        models.setFont(theme.qfont(11, theme.W_MEDIUM, mono=True))
        models.setStyleSheet(
            f"color: {pal.text_mono_dim}; background: transparent;")
        lay.addWidget(models)
        lay.addStretch(1)
        logs = kit.GhostButton("logs")
        logs.clicked.connect(self._open_logs)
        lay.addWidget(logs)
        return foot

    # ------------------------------------------------------------------- API

    def set_status(self, kind: str, message: str) -> None:
        pal = theme.palette()
        if kind == "recording":
            color = theme.INDIGO
        else:
            st = _STATUS_STATE.get(kind)
            color = pal.state(st) if st else pal.text_tertiary
        self._status_dot.set_color(color)
        self._status_lbl.setText(message)

    def refresh_history(self) -> None:
        self._recent_card.clear()
        entries = self._history.all()[:3]
        if not entries:
            empty = QLabel("Nada ainda. Ative na bandeja e segure Ctrl+Win.")
            empty.setFont(theme.qfont(12))
            empty.setStyleSheet(
                f"color: {theme.palette().text_tertiary}; "
                f"background: transparent; padding: 12px 14px;")
            self._recent_card.add_row(empty)
        else:
            for e in entries:
                self._recent_card.add_row(_RecentRow(e.text, e.when_label, e.mode))

        if self._history_dialog is not None and self._history_dialog.isVisible():
            self._history_dialog.refresh()

    # --------------------------------------------------------------- pickers

    def _mic_label(self) -> str:
        return self._cfg.mic_device or "Padrão do sistema"

    def _menu(self, anchor: QWidget, options, current, on_pick) -> None:
        pal = theme.palette()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
        QMenu {{
            background: {pal.surface};
            border: 1px solid {pal.border_strong};
            border-radius: 10px;
            padding: 6px;
            color: {pal.text_primary};
            font-size: 13px;
        }}
        QMenu::item {{
            padding: 7px 26px 7px 12px;
            border-radius: 7px;
        }}
        QMenu::item:selected {{ background: {pal.hover}; }}
        """)
        for value, label in options:
            act = menu.addAction(label)
            act.setData(value)
            if value == current:
                act.setCheckable(True)
                act.setChecked(True)
        chosen = menu.exec(anchor.mapToGlobal(QPoint(0, anchor.height())))
        if chosen is not None:
            on_pick(chosen.data())

    def _pick_mode(self) -> None:
        opts = [(m.id, m.name) for m in self._mode_store.active_modes()]
        self._menu(self._mode_row, opts, self._cfg.default_mode, self._set_mode)

    def _set_mode(self, key: str) -> None:
        self._cfg.default_mode = key
        self._cfg.save()
        m = self._mode_store.get(key)
        self._mode_row.set_value(
            m.name, theme.mode_swatch(m.color, not theme.is_dark()))
        self.config_changed.emit()

    def refresh_modes(self) -> None:
        """Reflete mudanças no store (após editar/deletar no gerenciador)."""
        # garante modo ativo válido
        valid = self._mode_store.fallback_id(self._cfg.default_mode)
        if valid != self._cfg.default_mode:
            self._cfg.default_mode = valid
            self._cfg.save()
        m = self._mode_store.get(self._cfg.default_mode)
        self._mode_row.set_value(
            m.name, theme.mode_swatch(m.color, not theme.is_dark()))

    def sync_from_config(self) -> None:
        """Re-sincroniza os 3 toggles rápidos com a config (sem emitir)."""
        self._tg_autostart.set_checked(self._cfg.autostart, animate=False)
        self._tg_paste.set_checked(self._cfg.paste_after_transcribe, animate=False)
        self._tg_overlay.set_checked(self._cfg.show_overlay, animate=False)

    def retheme(self) -> None:
        """Re-tematiza a janela inteira (rebuild garante re-tema completo)."""
        super().apply_theme()
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _clear_layout(item.layout())
        self._build()

    def _pick_mic(self) -> None:
        opts = [(None, "Padrão do sistema")]
        opts.extend((name, name) for name in list_input_devices())
        self._menu(self._mic_row, opts, self._cfg.mic_device, self._set_mic)

    def _set_mic(self, value) -> None:
        self._cfg.mic_device = value
        self._cfg.save()
        self._mic_row.set_value(self._mic_label())
        self.config_changed.emit()

    def _pick_lang(self) -> None:
        opts = list(_LANG_LABELS.items())
        self._menu(self._lang_row, opts, self._cfg.language, self._set_lang)

    def _set_lang(self, value: str) -> None:
        self._cfg.language = value
        self._cfg.save()
        self._lang_row.set_value(_LANG_LABELS.get(value, "Detectar"))
        self.config_changed.emit()

    def _pick_paste(self) -> None:
        opts = list(_PASTE_LABELS.items())
        self._menu(self._paste_row, opts, self._cfg.paste_method, self._set_paste)

    def _set_paste(self, value: str) -> None:
        self._cfg.paste_method = value
        self._cfg.save()
        self._paste_row.set_value(_PASTE_LABELS.get(value, "Automático"))
        self.config_changed.emit()

    def _pick_quality(self) -> None:
        opts = list(_QUALITY_LABELS.items())
        self._menu(self._quality_row, opts, self._cfg.quality_preset,
                   self._set_quality)

    def _set_quality(self, value: str) -> None:
        self._cfg.quality_preset = value
        self._cfg.save()
        self._quality_row.set_value(_QUALITY_LABELS.get(value, "Qualidade"))
        self.config_changed.emit()

    # --------------------------------------------------------------- toggles

    def _on_autostart(self, checked: bool) -> None:
        from sussurro.storage import autostart
        autostart.set_enabled(checked)
        self._cfg.autostart = checked
        self._cfg.save()
        self.config_changed.emit()

    def _on_paste_toggle(self, checked: bool) -> None:
        self._cfg.paste_after_transcribe = checked
        self._cfg.save()
        self.config_changed.emit()

    def _on_overlay_toggle(self, checked: bool) -> None:
        self._cfg.show_overlay = checked
        self._cfg.save()
        self.config_changed.emit()

    # ---------------------------------------------------------------- dialogs

    def _open_history(self) -> None:
        from sussurro.ui.history_ui import HistoryWindow
        if self._history_dialog is None:
            self._history_dialog = HistoryWindow(self._history, parent=self)
        self._history_dialog.refresh()
        self._history_dialog.show()
        self._history_dialog.raise_()
        self._history_dialog.activateWindow()

    def _open_logs(self) -> None:
        import subprocess

        from sussurro.storage.paths import app_data_dir
        try:
            subprocess.Popen(["explorer", str(app_data_dir())])
        except Exception:  # noqa: BLE001
            pass

    # ----------------------------------------------------------------- close

    def _on_close_clicked(self) -> None:
        self._cfg.window_x = self.x()
        self._cfg.window_y = self.y()
        self._cfg.save()
        self.hide()
        self.close_to_tray.emit()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        event.ignore()
        self._on_close_clicked()


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())
