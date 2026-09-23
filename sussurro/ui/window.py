"""Janela principal (tela 01) — hub compacto, design "Sussurro Quiet".

Frameless ~420px: title bar (wordmark) — hero (brand + status + atalho) —
grupo Configuração (Modo/Gravação/Modelo Whisper/Microfone/Idioma/Colar/Qualidade) —
grupo de toggles — Segundo Cérebro (DropZone para ingestão de áudio) — Recentes
(clique copia) — footer (modelos + logs). O histórico completo abre num diálogo.

Contrato com app.py preservado: construtor (config, history, mode_store=),
signals close_to_tray/config_changed, métodos set_status/refresh_history.
"""
from __future__ import annotations

from pathlib import Path

import pyperclip
import sounddevice as sd
from PySide6.QtCore import QObject, QPoint, QRectF, Qt, QThread, Signal
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

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
_RECORDING_MODE_LABELS: dict[str, str] = {
    "push_to_talk": "Push-to-Talk (segurar)",
    "toggle": "Hands-Free (toque alterna)",
}
_MODEL_LABELS: dict[str, str] = {
    "large-v3-turbo": "large-v3-turbo (Melhor Precisão)",
    "small": "small (Rápido e Leve)",
    "base": "base (Ultraleve)",
    "tiny": "tiny (Instantâneo / CPU)",
}

# kind do set_status -> (token de estado | cor fixa)
_STATUS_STATE = {
    "loading": theme.WARNING,
    "ready": theme.READY,
    "error": theme.ERROR,
    "paused": theme.WARNING,  # em espera / economizando VRAM
}


class FileTranscriptionWorker(QThread):
    """Worker em thread separada para transcrever arquivos de áudio sem travar a UI."""
    started_file = Signal(str)
    finished_file = Signal(str, str)
    error_file = Signal(str, str)

    def __init__(
        self,
        audio_path: Path,
        model_size: str = "large-v3-turbo",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._audio_path = audio_path
        self._model_size = model_size

    def run(self) -> None:
        try:
            self.started_file.emit(self._audio_path.name)
            from sussurro.transcribe_file import transcribe_file

            out_file = transcribe_file(
                audio_path=self._audio_path,
                model_size=self._model_size,
            )
            self.finished_file.emit(self._audio_path.name, str(out_file))
        except Exception as exc:  # noqa: BLE001
            self.error_file.emit(self._audio_path.name, str(exc))


class _StatusDot(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color: str = theme.state_color(theme.READY)
        self.setFixedSize(7, 7)

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._color))
        r = QRectF(0.5, 0.5, 6, 6)
        p.drawEllipse(r)
        p.end()


class _SectionLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFont(theme.qfont(10, theme.W_SEMIBOLD, tracking=theme.TRACK_LABEL))
        self.apply_theme()

    def apply_theme(self) -> None:
        c = theme.palette().text_tertiary
        self.setStyleSheet(f"color: {c}; text-transform: uppercase; background: transparent;")


class _RecentRow(QWidget):
    clicked = Signal(str)

    def __init__(self, text: str, when: str, mode_key: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        pal = theme.palette()

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        # dot do modo
        mode = M.get_mode(mode_key)
        dot_color = theme.mode_swatch(mode.color, not pal.is_dark) if mode else pal.border_strong
        lay.addWidget(_MiniDot(dot_color), 0, Qt.AlignmentFlag.AlignVCenter)

        # texto truncado elegantemente
        one_line = " ".join(text.replace("\n", " ").split())
        self._lbl = _ElidedLabel(one_line, pal.text_primary)
        lay.addWidget(self._lbl, 1, Qt.AlignmentFlag.AlignVCenter)

        # tempo
        time_lbl = QLabel(when)
        time_lbl.setFont(theme.qfont(11))
        time_lbl.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._text)
        super().mouseReleaseEvent(event)


class _ElidedLabel(QLabel):
    """QLabel que faz elide no texto caso nao caiba."""

    def __init__(self, text: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self._color = color
        self.setFont(theme.qfont(12))
        self.setStyleSheet(f"color: {color}; background: transparent;")

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setPen(theme.qcolor(self._color))
        p.setFont(self.font())
        fm = p.fontMetrics()
        elided = fm.elidedText(self._text, Qt.TextElideMode.ElideRight, self.width())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)
        p.end()


class _MiniDot(QWidget):
    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(5, 5)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._color))
        p.drawEllipse(QRectF(0, 0, 5, 5))
        p.end()


class _DropZoneCard(QWidget):
    """Área visual de arrastar e soltar arquivos de áudio para o Segundo Cérebro."""
    file_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False
        self._build()

    def _build(self) -> None:
        pal = theme.palette()
        self.setObjectName("DropZoneCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._update_style()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_title = QLabel("📥 Arraste um áudio aqui para o Segundo Cérebro")
        self._lbl_title.setFont(theme.qfont(12, theme.W_SEMIBOLD))
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_title.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(self._lbl_title)

        self._lbl_sub = QLabel(".mp3, .m4a, .wav, .ogg — transcrição para RAW/ (ou clique para escolher)")
        self._lbl_sub.setFont(theme.qfont(10))
        self._lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_sub.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(self._lbl_sub)

    def _update_style(self) -> None:
        pal = theme.palette()
        border_color = pal.link if self._active else pal.border_strong
        bg_color = pal.hover if self._active else pal.surface
        self.setStyleSheet(f"""
        QWidget#DropZoneCard {{
            background: {bg_color};
            border: 1px dashed {border_color};
            border-radius: {theme.RADIUS_CARD}px;
        }}
        QWidget#DropZoneCard:hover {{
            background: {pal.hover};
            border: 1px dashed {pal.link};
        }}
        """)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._update_style()

    def set_status(self, title: str, subtitle: str | None = None) -> None:
        pal = theme.palette()
        self._lbl_title.setText(title)
        if subtitle:
            self._lbl_sub.setText(subtitle)
        self._lbl_title.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar Áudio para o Segundo Cérebro",
                "",
                "Áudios (*.mp3 *.m4a *.wav *.ogg *.flac *.aac *.opus *.wma);;Todos os Arquivos (*.*)",
            )
            if file_path:
                self.file_selected.emit(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = Path(url.toLocalFile()).suffix.lower()
                if ext in {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma"}:
                    event.acceptProposedAction()
                    self.set_active(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.set_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self.set_active(False)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = Path(url.toLocalFile())
                if local_path.suffix.lower() in {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma"}:
                    event.acceptProposedAction()
                    self.file_selected.emit(str(local_path))
                    return


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
        self._file_worker: FileTranscriptionWorker | None = None

        self.setAcceptDrops(True)

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

        # Segundo Cérebro drop zone card
        content.addWidget(_SectionLabel("Segundo Cérebro"))
        content.addSpacing(6)
        self._drop_zone = _DropZoneCard(parent=self)
        self._drop_zone.file_selected.connect(self._handle_audio_file)
        content.addWidget(self._drop_zone)
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
        sr = QWidget()
        sr.setLayout(status_row)
        head.addWidget(sr, 0, Qt.AlignmentFlag.AlignHCenter)
        hw = QWidget()
        hw.setLayout(head)
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

        hint_text = "toque pra falar (hands-free)" if self._cfg.recording_mode == "toggle" else "segure pra falar"
        self._hero_hint = QLabel(hint_text)
        self._hero_hint.setFont(theme.qfont(12))
        self._hero_hint.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        keys.addSpacing(6)
        keys.addWidget(self._hero_hint)
        kw = QWidget()
        kw.setLayout(keys)
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

        self._record_row = kit.ValueRow(
            "Gravação", _RECORDING_MODE_LABELS.get(self._cfg.recording_mode, "Push-to-Talk (segurar)")
        )
        self._record_row.clicked.connect(self._pick_recording_mode)
        card.add_row(self._record_row)

        self._whisper_model_row = kit.ValueRow(
            "Modelo Whisper", _MODEL_LABELS.get(self._cfg.model_size, self._cfg.model_size)
        )
        self._whisper_model_row.clicked.connect(self._pick_whisper_model)
        card.add_row(self._whisper_model_row)

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
            f"background: transparent; border-top: 1px solid {pal.border_subtle};")
        lay = QHBoxLayout(foot)
        lay.setContentsMargins(4, 10, 4, 10)
        lay.setSpacing(6)

        left = QLabel("Whisper + Qwen local")
        left.setFont(theme.qfont(11))
        left.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(left)

        lay.addStretch(1)

        logs_btn = kit.GhostButton("logs")
        logs_btn.clicked.connect(self._open_logs)
        lay.addWidget(logs_btn)
        return foot

    # ----------------------------------------------------------------- state

    def set_status(self, kind: str, message: str) -> None:
        """kind: 'loading' | 'ready' | 'error' | 'paused'."""
        state = _STATUS_STATE.get(kind, theme.READY)
        dot_color = theme.state_color(state)
        self._status_dot.set_color(dot_color)
        self._status_lbl.setText(message)

    def refresh_history(self) -> None:
        """Renderiza os 3 itens mais recentes no GroupCard compacto."""
        self._recent_card.clear_rows()
        items = self._history.recent(limit=3)
        if not items:
            pal = theme.palette()
            empty = QLabel("Nenhum ditado ainda")
            empty.setFont(theme.qfont(12))
            empty.setStyleSheet(f"color: {pal.text_tertiary}; padding: 10px 14px;")
            self._recent_card.add_row(empty)
            return

        for item in items:
            row = _RecentRow(
                text=item["text"],
                when=item.get("when", ""),
                mode_key=item.get("mode", "raw"),
            )
            row.clicked.connect(self._on_copy_recent)
            self._recent_card.add_row(row)

    def _on_copy_recent(self, text: str) -> None:
        pyperclip.copy(text)
        self.set_status("ready", "copiado para a área de transferência!")

    # --------------------------------------------------------------- pickers

    def _mic_label(self) -> str:
        if not self._cfg.mic_device:
            return "Padrão do sistema"
        d = self._cfg.mic_device
        return d if len(d) <= 22 else d[:20] + "…"

    def _menu(self, anchor: QWidget, options: list[tuple[object, str]],
              current: object, on_pick) -> None:
        pal = theme.palette()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
        QMenu {{
            background: {pal.surface};
            border: 1px solid {pal.border_subtle};
            border-radius: {theme.RADIUS_MENU}px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 12px;
            color: {pal.text_primary};
            font-size: 12px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {pal.hover};
            color: {pal.text_primary};
        }}
        """)
        for val, label in options:
            prefix = "✓ " if val == current else "   "
            act = menu.addAction(prefix + label)
            act.triggered.connect(lambda _chk=False, v=val: on_pick(v))
        pt = anchor.mapToGlobal(QPoint(0, anchor.height() + 4))
        menu.exec(pt)

    def _pick_mode(self) -> None:
        opts = [(m.id, m.name) for m in self._mode_store.list_all()]
        self._menu(self._mode_row, opts, self._cfg.default_mode, self._set_mode)

    def _set_mode(self, key: str) -> None:
        self._cfg.default_mode = key
        self._cfg.save()
        m = self._mode_store.get(key)
        self._mode_row.set_value(
            m.name, theme.mode_swatch(m.color, not theme.is_dark()))
        self.config_changed.emit()

    def _pick_recording_mode(self) -> None:
        opts = list(_RECORDING_MODE_LABELS.items())
        self._menu(self._record_row, opts, self._cfg.recording_mode, self._set_recording_mode)

    def _set_recording_mode(self, value: str) -> None:
        self._cfg.recording_mode = value
        self._cfg.save()
        self._record_row.set_value(_RECORDING_MODE_LABELS.get(value, "Push-to-Talk"))
        hint_text = "toque pra falar (hands-free)" if value == "toggle" else "segure pra falar"
        if hasattr(self, "_hero_hint"):
            self._hero_hint.setText(hint_text)
        self.config_changed.emit()

    def _pick_whisper_model(self) -> None:
        opts = list(_MODEL_LABELS.items())
        self._menu(self._whisper_model_row, opts, self._cfg.model_size, self._set_whisper_model)

    def _set_whisper_model(self, value: str) -> None:
        self._cfg.model_size = value
        self._cfg.save()
        self._whisper_model_row.set_value(_MODEL_LABELS.get(value, value))
        self.config_changed.emit()

    def refresh_modes(self) -> None:
        """Recarrega os modos a partir do ModeStore e atualiza a UI."""
        self._mode_store = ModeStore.load()
        if not self._mode_store.has(self._cfg.default_mode):
            self._cfg.default_mode = self._mode_store.fallback_id()
            self._cfg.save()
        m = self._mode_store.get(self._cfg.default_mode)
        self._mode_row.set_value(
            m.name, theme.mode_swatch(m.color, not theme.is_dark()))

    def sync_from_config(self) -> None:
        """Re-sincroniza os toggles rápidos e rows com a config (sem emitir)."""
        self._tg_autostart.set_checked(self._cfg.autostart, animate=False)
        self._tg_paste.set_checked(self._cfg.paste_after_transcribe, animate=False)
        self._tg_overlay.set_checked(self._cfg.show_overlay, animate=False)
        if hasattr(self, "_record_row"):
            self._record_row.set_value(
                _RECORDING_MODE_LABELS.get(self._cfg.recording_mode, "Push-to-Talk")
            )
        if hasattr(self, "_whisper_model_row"):
            self._whisper_model_row.set_value(
                _MODEL_LABELS.get(self._cfg.model_size, self._cfg.model_size)
            )
        if hasattr(self, "_hero_hint"):
            hint_text = "toque pra falar (hands-free)" if self._cfg.recording_mode == "toggle" else "segure pra falar"
            self._hero_hint.setText(hint_text)

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
        try:
            for dev in sd.query_devices():
                if dev.get("max_input_channels", 0) > 0:
                    opts.append((dev["name"], dev["name"]))
        except Exception:  # noqa: BLE001
            pass
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

    # --------------------------------------------------------------- audio ingestion

    def _handle_audio_file(self, file_path_str: str) -> None:
        p = Path(file_path_str)
        if not p.exists():
            return
        if self._file_worker is not None and self._file_worker.isRunning():
            self.set_status("paused", "Já há uma transcrição em andamento.")
            return

        self._drop_zone.set_status(
            f"Transcrevendo '{p.name}'...",
            "Whisper processando e exportando para E:/Dados/RAW/..."
        )
        self.set_status("loading", f"transcrevendo {p.name}...")

        self._file_worker = FileTranscriptionWorker(p, model_size=self._cfg.model_size, parent=self)
        self._file_worker.finished_file.connect(self._on_file_transcription_finished)
        self._file_worker.error_file.connect(self._on_file_transcription_error)
        self._file_worker.start()

    def _on_file_transcription_finished(self, name: str, out_path: str) -> None:
        self._drop_zone.set_status(
            f"✓ Transcrito: {name}",
            f"Salvo em {Path(out_path).name} (RAW do Obsidian)"
        )
        self.set_status("ready", f"Áudio {name} salvo em RAW/")
        try:
            self._history.append(
                text=f"[Arquivo Transcrito: {name}] Salvo em RAW/{Path(out_path).name}",
                mode_key="segundo_cerebro",
                latency_ms=0,
            )
            self.refresh_history()
        except Exception:  # noqa: BLE001
            pass

    def _on_file_transcription_error(self, name: str, err: str) -> None:
        self._drop_zone.set_status(
            f"Erro ao transcrever: {name}",
            f"{err[:50]}..." if len(err) > 50 else err
        )
        self.set_status("error", f"Erro no áudio: {err[:35]}")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = Path(url.toLocalFile()).suffix.lower()
                if ext in {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma"}:
                    event.acceptProposedAction()
                    self._drop_zone.set_active(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._drop_zone.set_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self._drop_zone.set_active(False)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = Path(url.toLocalFile())
                if local_path.suffix.lower() in {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma"}:
                    event.acceptProposedAction()
                    self._handle_audio_file(str(local_path))
                    return

    # ----------------------------------------------------------------- dialogs

    def _open_history(self) -> None:
        from sussurro.ui.history_dialog import HistoryDialog
        if self._history_dialog is None:
            self._history_dialog = HistoryDialog(self._history, parent=self)
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
