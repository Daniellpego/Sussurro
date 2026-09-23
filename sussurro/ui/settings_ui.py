"""Ajustes (tela 05) — janela com sidebar de abas + conteúdo.

Geral e Modos são funcionais de verdade; as outras abas fiam nos controles de
config que JÁ existem (modelo Whisper, microfone, botão do mouse) e marcam o
resto honestamente como "em breve" — nada de controle decorativo.

Troca de tema (Aparência) é tratada pelo app (re-tematiza TODAS as janelas).
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sussurro import __version__
from sussurro.audio.capture import list_input_devices
from sussurro.llm.modes import ModeStore
from sussurro.storage.config import Config
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components import nav_icons
from sussurro.ui.components.window_frame import FramelessWindow
from sussurro.ui.modes_ui import ModeEditor, ModesManager

# (key, label, cor do tile: (dark, light) ou "gradient")
_TABS = (
    ("geral",      "Geral",      ("#7A7D86", "#9498A2")),
    ("modelos",    "Modelos",    ("#7C84FF", "#7C84FF")),
    ("modos",      "Modos",      "gradient"),
    ("audio",      "Áudio",      ("#30D158", "#34C759")),
    ("atalhos",    "Atalhos",    ("#0A84FF", "#0A84FF")),
    ("dicionario", "Dicionário", ("#FBBF24", "#F5A623")),
    ("sobre",      "Sobre",      ("#52555D", "#9DA0A8")),
)

_WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo")
_MOUSE_LABELS = {
    "none": "Nenhum", "middle": "Botão do meio",
    "x1": "Lateral (voltar)", "x2": "Lateral (avançar)",
}


def _glyph_color(hexc: str) -> QColor:
    """Branco em tiles escuros, escuro em tiles claros (ex.: amarelo)."""
    c = QColor(hexc)
    lum = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
    return QColor("#0E0F12") if lum > 0.62 else QColor("#FFFFFF")


class _TabTile(QWidget):
    SIZE = 24

    def __init__(self, key: str, color, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self._color = color
        self.setFixedSize(self.SIZE, self.SIZE)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        s = self.SIZE
        rect = QRectF(0, 0, s, s)
        if self._color == "gradient":
            g = QLinearGradient(0, 0, s, s)
            g.setColorAt(0, theme.qcolor(theme.GRAD_A))
            g.setColorAt(1, theme.qcolor(theme.GRAD_B))
            p.setBrush(g)
            glyph = QColor("#FFFFFF")
        else:
            hexc = self._color[1] if not theme.is_dark() else self._color[0]
            p.setBrush(theme.qcolor(hexc))
            glyph = _glyph_color(hexc)
        p.drawRoundedRect(rect, 7.5, 7.5)
        inset = 5.0
        nav_icons.paint(
            p, self._key, QRectF(inset, inset, s - 2 * inset, s - 2 * inset),
            glyph, 1.7)


class _TabRow(QWidget):
    clicked = Signal(str)

    def __init__(self, key: str, label: str, color, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self._active = False
        self.setObjectName("TabRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)
        lay.addWidget(_TabTile(key, color), 0, Qt.AlignmentFlag.AlignVCenter)
        self._label = QLabel(label)
        self._label.setFont(theme.qfont(13, theme.W_MEDIUM))
        lay.addWidget(self._label)
        lay.addStretch(1)
        self.apply_theme()

    def set_active(self, v: bool) -> None:
        self._active = v
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        bg = pal.hover if self._active else "transparent"
        fg = pal.text_primary if self._active else pal.text_secondary
        self.setStyleSheet(
            f"QWidget#TabRow {{ background: {bg}; border-radius: 9px; }}"
            f"QWidget#TabRow:hover {{ background: {pal.hover}; }}")
        self._label.setStyleSheet(f"color: {fg}; background: transparent;")

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._key)


class SettingsWindow(FramelessWindow):
    config_changed = Signal()
    theme_changed = Signal(str)     # "system"|"light"|"dark"
    modes_changed = Signal()

    def __init__(self, config: Config, store: ModeStore,
                 active_mode_getter, dictionary=None, parent=None) -> None:
        super().__init__(width=720, parent=parent)
        self._cfg = config
        self._store = store
        self._active_mode_getter = active_mode_getter
        from sussurro.storage.dictionary import Dictionary
        self._dict = dictionary or Dictionary()
        self._current = "geral"
        self._editor = None
        self._build()

    # ----------------------------------------------------------------- build

    def _build(self) -> None:
        bar = kit.WindowTitleBar("Ajustes", show_minimize=False)
        bar.close_requested.connect(self.hide)
        self.body.addWidget(bar)

        split = QHBoxLayout()
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(0)
        self.body.addLayout(split, 1)

        # sidebar
        self._sidebar = self._build_sidebar()
        split.addWidget(self._sidebar)

        # conteúdo
        self._stack = QStackedWidget()
        self._panes: dict[str, int] = {}
        for key, _, _c in _TABS:
            pane = self._build_pane(key)
            idx = self._stack.addWidget(pane)
            self._panes[key] = idx
        split.addWidget(self._stack, 1)

        self._select_tab(self._current)
        self._root.setMinimumHeight(476)

    def _build_sidebar(self) -> QWidget:
        pal = theme.palette()
        side = QWidget()
        side.setObjectName("SettingsSidebar")
        side.setFixedWidth(186)
        side.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        side.setStyleSheet(
            f"QWidget#SettingsSidebar {{ background: {pal.chrome}; "
            f"border-right: 1px solid {pal.divider}; }}")
        lay = QVBoxLayout(side)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(2)
        self._tab_rows: dict[str, _TabRow] = {}
        for key, label, color in _TABS:
            row = _TabRow(key, label, color)
            row.clicked.connect(self._select_tab)
            lay.addWidget(row)
            self._tab_rows[key] = row
        lay.addStretch(1)
        return side

    def _select_tab(self, key: str) -> None:
        self._current = key
        for k, row in self._tab_rows.items():
            row.set_active(k == key)
        self._stack.setCurrentIndex(self._panes[key])

    # ------------------------------------------------------------- panes

    def _build_pane(self, key: str) -> QWidget:
        return {
            "geral": self._pane_geral,
            "modelos": self._pane_modelos,
            "modos": self._pane_modos,
            "audio": self._pane_audio,
            "atalhos": self._pane_atalhos,
            "dicionario": self._pane_dicionario,
            "sobre": self._pane_sobre,
        }[key]()

    def _scroll_pane(self, inner: QWidget) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(18)
        lay.addWidget(inner)
        lay.addStretch(1)
        return wrap

    def _section(self, title: str, card: QWidget) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lbl = QLabel(title.upper())
        lbl.setFont(theme.qfont(11, theme.W_SEMIBOLD, tracking=theme.TRACK_LABEL))
        lbl.setStyleSheet(f"color: {theme.palette().text_tertiary};")
        lay.addWidget(lbl)
        lay.addWidget(card)
        return w

    def _custom_row(self, label: str, right: QWidget) -> QWidget:
        pal = theme.palette()
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 11, 14, 11)
        lbl = QLabel(label)
        lbl.setFont(theme.qfont(13.5, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        lay.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    # --- Geral ---
    def _pane_geral(self) -> QWidget:
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(18)

        # Aparência (segmented) — primeiro
        seg = kit.SegmentedControl(
            [("system", "Sistema"), ("light", "Claro"), ("dark", "Escuro")],
            self._cfg.theme)
        seg.changed.connect(self._on_theme)
        appearance = kit.GroupCard()
        appearance.add_row(self._custom_row("Tema", seg))
        self._tg_glass = kit.ToggleRow(
            "Efeito vidro (experimental)", self._cfg.glass)
        self._tg_glass.toggled.connect(lambda v: self._set("glass", v))
        appearance.add_row(self._tg_glass)
        appearance.add_row(self._note_row(
            "Acrílico do Windows 11. Aplica ao reiniciar o app."))
        col.addWidget(self._section("Aparência", appearance))

        # Inicialização
        init = kit.GroupCard()
        self._tg_autostart = kit.ToggleRow("Iniciar com o Windows", self._cfg.autostart)
        self._tg_autostart.toggled.connect(lambda v: self._set("autostart", v))
        init.add_row(self._tg_autostart)
        self._tg_startmin = kit.ToggleRow(
            "Abrir minimizado na bandeja", self._cfg.start_minimized)
        self._tg_startmin.toggled.connect(lambda v: self._set("start_minimized", v))
        init.add_row(self._tg_startmin)
        col.addWidget(self._section("Inicialização", init))

        # Comportamento
        beh = kit.GroupCard()
        self._tg_paste = kit.ToggleRow(
            "Colar automaticamente", self._cfg.paste_after_transcribe)
        self._tg_paste.toggled.connect(
            lambda v: self._set("paste_after_transcribe", v))
        beh.add_row(self._tg_paste)
        self._tg_overlay = kit.ToggleRow("Mostrar overlay (HUD)", self._cfg.show_overlay)
        self._tg_overlay.toggled.connect(lambda v: self._set("show_overlay", v))
        beh.add_row(self._tg_overlay)
        self._tg_sound = kit.ToggleRow("Sons de feedback (gravar/concluir)", self._cfg.play_sound)
        self._tg_sound.toggled.connect(lambda v: self._set("play_sound", v))
        beh.add_row(self._tg_sound)
        self._tg_automode = kit.ToggleRow(
            "Modo automático pelo app em foco", self._cfg.auto_mode)
        self._tg_automode.toggled.connect(lambda v: self._set("auto_mode", v))
        beh.add_row(self._tg_automode)
        self._tg_vcmd = kit.ToggleRow(
            'Comandos de voz ("nova linha", "novo parágrafo"…)',
            self._cfg.voice_commands)
        self._tg_vcmd.toggled.connect(lambda v: self._set("voice_commands", v))
        beh.add_row(self._tg_vcmd)
        col.addWidget(self._section("Comportamento", beh))

        # Atualizações (versão real; auto-update é futuro)
        upd = kit.GroupCard()
        upd.add_row(self._version_row())
        col.addWidget(self._section("Atualizações", upd))

        return self._scroll_pane(inner)

    def _version_row(self) -> QWidget:
        pal = theme.palette()
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 11, 14, 11)
        col = QVBoxLayout(); col.setSpacing(2)
        v = QLabel(f"Versão {__version__}")
        v.setFont(theme.qfont(13.5, theme.W_MEDIUM))
        v.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        col.addWidget(v)
        sub = QLabel("verificação de atualizações em breve")
        sub.setFont(theme.qfont(11.5, theme.W_MEDIUM, mono=True))
        sub.setStyleSheet(f"color: {pal.text_mono_dim}; background: transparent;")
        col.addWidget(sub)
        lay.addLayout(col)
        lay.addStretch(1)
        lay.addWidget(self._soon_badge())
        return row

    # --- Modos (gerenciador plugado) ---
    def _pane_modos(self) -> QWidget:
        self._manager = ModesManager(self._store, self._active_mode_getter())
        self._manager.edit_requested.connect(self._open_editor)
        self._manager.new_requested.connect(lambda: self._open_editor(None))
        self._manager.changed.connect(self._on_modes_changed)
        return self._manager

    def _open_editor(self, mode_id) -> None:
        self._editor = ModeEditor(self._store, mode_id, parent=self)
        self._editor.saved.connect(lambda _id: self._on_modes_changed())
        self._editor.deleted.connect(lambda _id: self._on_modes_changed())
        self._editor.show()
        self._editor.raise_()

    def _on_modes_changed(self) -> None:
        if hasattr(self, "_manager"):
            self._manager.set_active_id(self._active_mode_getter())
        self.modes_changed.emit()

    # --- Modelos ---
    def _pane_modelos(self) -> QWidget:
        inner = QWidget()
        col = QVBoxLayout(inner); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(18)

        asr = kit.GroupCard()
        self._row_model = kit.ValueRow("Modelo Whisper", self._cfg.model_size)
        self._row_model.clicked.connect(self._pick_model)
        asr.add_row(self._row_model)
        _q_labels = {
            "quality": "Qualidade", "balanced": "Equilíbrio", "light": "Leve",
        }
        self._row_quality = kit.ValueRow(
            "Perfil de qualidade",
            _q_labels.get(self._cfg.quality_preset, "Qualidade"))
        self._row_quality.clicked.connect(self._pick_quality)
        asr.add_row(self._row_quality)
        asr.add_row(self._note_row(
            "Qualidade = melhor acento/termos. Leve = mais rápido. "
            "Se a GPU falhar, cai pra CPU sozinho."))
        col.addWidget(self._section("Reconhecimento (Whisper)", asr))

        llm = kit.GroupCard()
        llm.add_row(self._custom_row_soon("Modelo LLM (Ollama)"))
        llm.add_row(self._custom_row_soon("Detecção de GPU / VRAM"))
        col.addWidget(self._section("Processamento (LLM)", llm))

        # Desempenho / VRAM / RAM
        # Regra de ouro: NADA aqui troca o modelo Whisper por um pior.
        # Economia = quando carregar / descarregar, não o que reconhece.
        perf = kit.GroupCard()
        self._tg_smart = kit.ToggleRow(
            "Economia inteligente (sem perder qualidade)", self._cfg.smart_economy)
        self._tg_smart.toggled.connect(
            lambda v: self._set("smart_economy", v))
        perf.add_row(self._tg_smart)
        perf.add_row(self._note_row(
            "Mantém o mesmo modelo Whisper. Só evita prender o Qwen na VRAM "
            "quando você usa Raw ou fica ocioso. Texto = mesma qualidade."))

        self._tg_start_armed = kit.ToggleRow(
            "Já abrir ativo (pronto pra ditar)", self._cfg.start_armed)
        self._tg_start_armed.toggled.connect(
            lambda v: self._set("start_armed", v))
        perf.add_row(self._tg_start_armed)
        perf.add_row(self._note_row(
            "Ligado (padrão): abre pronto pra ditar. Desligado: abre em "
            "espera, quase sem VRAM, e você ativa na bandeja quando for usar."))

        self._tg_preload = kit.ToggleRow(
            "Pré-carregar Whisper ao ativar", self._cfg.preload_asr)
        self._tg_preload.toggled.connect(
            lambda v: self._set("preload_asr", v))
        perf.add_row(self._tg_preload)
        perf.add_row(self._note_row(
            "Ligado: ao ativar, já carrega ~3 GB VRAM (1ª fala rápida). "
            "Desligado: carrega só na primeira fala. Modelo = o mesmo."))

        self._tg_ollama_boot = kit.ToggleRow(
            "Abrir Ollama junto com o Sussurro", self._cfg.ollama_autostart)
        self._tg_ollama_boot.toggled.connect(
            lambda v: self._set("ollama_autostart", v))
        perf.add_row(self._tg_ollama_boot)
        perf.add_row(self._note_row(
            "Desligado (padrão): Ollama só sobe se você usar Clean/Email… "
            "Raw não precisa do Ollama."))

        self._tg_ollama_quit = kit.ToggleRow(
            "Descarregar IA da VRAM ao fechar", self._cfg.ollama_unload_on_quit)
        self._tg_ollama_quit.toggled.connect(
            lambda v: self._set("ollama_unload_on_quit", v))
        perf.add_row(self._tg_ollama_quit)

        _ka = {
            "0": "Na hora (recomendado)",
            "5m": "5 minutos",
            "10m": "10 minutos",
            "30m": "30 minutos",
        }
        self._row_keep = kit.ValueRow(
            "Manter Qwen na VRAM após Clean",
            _ka.get(self._cfg.ollama_keep_alive, self._cfg.ollama_keep_alive))
        self._row_keep.clicked.connect(self._pick_keep_alive)
        perf.add_row(self._row_keep)
        perf.add_row(self._note_row(
            "“Na hora” = solta ~5 GB depois do Clean. Próximo Clean recarrega "
            "(mais lento 1×). Qualidade do texto não muda."))

        self._tg_unload = kit.ToggleRow(
            "Liberar Whisper se ocioso (~10 min)", self._cfg.unload_idle)
        self._tg_unload.toggled.connect(self._on_unload_toggle)
        perf.add_row(self._tg_unload)
        perf.add_row(self._note_row(
            "Descarrega o Whisper após ~10 min sem ditar (e o Qwen aos 2 min). "
            "Bom pra jogar. Ao falar de novo, recarrega o mesmo modelo."))
        col.addWidget(self._section("Desempenho", perf))
        return self._scroll_pane(inner)

    def _on_unload_toggle(self, v: bool) -> None:
        self._cfg.unload_idle = v
        self._cfg.save()
        self.config_changed.emit()

    def _pick_keep_alive(self) -> None:
        opts = [
            ("0", "Na hora (recomendado)"),
            ("5m", "5 minutos"),
            ("10m", "10 minutos"),
            ("30m", "30 minutos"),
        ]
        self._menu(self._row_keep, opts, self._cfg.ollama_keep_alive,
                   self._set_keep_alive)

    def _set_keep_alive(self, value: str) -> None:
        self._cfg.ollama_keep_alive = value
        self._cfg.save()
        labels = {
            "0": "Na hora (recomendado)", "5m": "5 minutos",
            "10m": "10 minutos", "30m": "30 minutos",
        }
        self._row_keep.set_value(labels.get(value, value))
        self.config_changed.emit()

    # --- Áudio ---
    def _pane_audio(self) -> QWidget:
        inner = QWidget()
        col = QVBoxLayout(inner); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(18)
        card = kit.GroupCard()
        self._row_mic = kit.ValueRow(
            "Microfone", self._cfg.mic_device or "Padrão do sistema")
        self._row_mic.clicked.connect(self._pick_mic)
        card.add_row(self._row_mic)
        card.add_row(self._custom_row_soon("Sensibilidade / VAD"))
        col.addWidget(self._section("Entrada de áudio", card))
        return self._scroll_pane(inner)

    # --- Atalhos ---
    def _pane_atalhos(self) -> QWidget:
        inner = QWidget()
        col = QVBoxLayout(inner); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(18)
        card = kit.GroupCard()
        ptt = kit.ValueRow("Push-to-talk", self._cfg.hotkey_label)
        ptt.setEnabled(False)
        card.add_row(ptt)
        self._row_mouse = kit.ValueRow(
            "Botão do mouse", _MOUSE_LABELS.get(self._cfg.mouse_button, "Nenhum"))
        self._row_mouse.clicked.connect(self._pick_mouse)
        card.add_row(self._row_mouse)
        card.add_row(self._custom_row_soon("Atalho por modo"))
        col.addWidget(self._section("Gravação", card))
        return self._scroll_pane(inner)

    # --- Dicionário ---
    def _pane_dicionario(self) -> QWidget:
        pal = theme.palette()
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(12)

        desc = QLabel("Nomes próprios, ferramentas, jargão técnico. O "
                      "reconhecimento passa a acertar a grafia desses termos. "
                      "Já vem com uma semente de termos comuns de dev.")
        desc.setFont(theme.qfont(12.5))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {pal.text_secondary};")
        col.addWidget(desc)

        # adicionar
        add = QHBoxLayout(); add.setSpacing(8)
        self._dict_input = kit.LineEdit(
            placeholder="Adicionar termo, nome ou jargão…")
        self._dict_input.returnPressed.connect(self._add_dict_term)
        add.addWidget(self._dict_input, 1)
        btn = kit.PrimaryButton("Adicionar")
        btn.clicked.connect(self._add_dict_term)
        add.addWidget(btn)
        col.addLayout(add)

        # sugestões (preenchidas ao ditar)
        self._dict_sugg_wrap = QVBoxLayout()
        self._dict_sugg_wrap.setContentsMargins(0, 0, 0, 0)
        self._dict_sugg_wrap.setSpacing(8)
        col.addLayout(self._dict_sugg_wrap)

        # lista
        self._dict_list = QVBoxLayout()
        self._dict_list.setContentsMargins(0, 0, 0, 0)
        self._dict_list.setSpacing(8)
        col.addLayout(self._dict_list)
        self._refresh_dict_list()
        return self._scroll_pane(inner)

    def _refresh_dict_list(self) -> None:
        pal = theme.palette()
        # --- sugestões ---
        while self._dict_sugg_wrap.count():
            it = self._dict_sugg_wrap.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        sugg = self._dict.suggestions()
        if sugg:
            title = QLabel("Sugeridos (apareceram nas suas falas)")
            title.setFont(theme.qfont(11, theme.W_SEMIBOLD))
            title.setStyleSheet(
                f"color: {pal.text_tertiary}; letter-spacing: 0.3px;")
            self._dict_sugg_wrap.addWidget(title)
            scard = kit.GroupCard()
            for t in sugg[:12]:
                scard.add_row(self._dict_sugg_row(t))
            self._dict_sugg_wrap.addWidget(scard)

        # --- termos ---
        while self._dict_list.count():
            it = self._dict_list.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        terms = self._dict.all()
        if not terms:
            empty = QLabel("Nenhum termo ainda.")
            empty.setFont(theme.qfont(12.5))
            empty.setStyleSheet(
                f"color: {pal.text_tertiary}; padding: 14px 0;")
            self._dict_list.addWidget(empty)
            return
        card = kit.GroupCard()
        for t in terms:
            card.add_row(self._dict_term_row(t))
        self._dict_list.addWidget(card)

    def _dict_term_row(self, term: str) -> QWidget:
        pal = theme.palette()
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 10, 10, 10)
        lbl = QLabel(term)
        lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        rm = kit.GhostButton("remover")
        rm.clicked.connect(lambda: self._remove_dict_term(term))
        lay.addWidget(rm)
        return row

    def _dict_sugg_row(self, term: str) -> QWidget:
        pal = theme.palette()
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 10, 10, 10)
        lbl = QLabel(term)
        lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        add = kit.GhostButton("adicionar")
        add.clicked.connect(lambda: self._accept_sugg(term))
        lay.addWidget(add)
        skip = kit.GhostButton("ignorar")
        skip.clicked.connect(lambda: self._dismiss_sugg(term))
        lay.addWidget(skip)
        return row

    def _accept_sugg(self, term: str) -> None:
        self._dict.accept_suggestion(term)
        self._refresh_dict_list()

    def _dismiss_sugg(self, term: str) -> None:
        self._dict.dismiss_suggestion(term)
        self._refresh_dict_list()

    def _add_dict_term(self) -> None:
        term = self._dict_input.text()
        if self._dict.add(term):
            self._dict_input.clear()
            self._refresh_dict_list()

    def _remove_dict_term(self, term: str) -> None:
        self._dict.remove(term)
        self._refresh_dict_list()

    # --- Sobre ---
    def _pane_sobre(self) -> QWidget:
        pal = theme.palette()
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 30, 0, 0)
        col.setSpacing(12)
        col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(kit.BrandMark(70), 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel("Sussurro")
        name.setFont(theme.qfont(24, theme.W_SEMIBOLD, tracking=theme.TRACK_DISPLAY))
        name.setStyleSheet(f"color: {pal.text_primary};")
        col.addWidget(name, 0, Qt.AlignmentFlag.AlignHCenter)
        ver = QLabel(f"Versão {__version__}")
        ver.setFont(theme.qfont(12, theme.W_MEDIUM, mono=True))
        ver.setStyleSheet(f"color: {pal.text_secondary};")
        col.addWidget(ver, 0, Qt.AlignmentFlag.AlignHCenter)
        tag = QLabel("Ditado por voz local. 100% no seu computador.")
        tag.setFont(theme.qfont(13))
        tag.setStyleSheet(f"color: {pal.text_secondary};")
        col.addWidget(tag, 0, Qt.AlignmentFlag.AlignHCenter)
        return self._scroll_pane(inner)

    # --- placeholders / soon ---
    def _pane_placeholder(self, title: str, subtitle: str) -> QWidget:
        pal = theme.palette()
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 40, 0, 0)
        col.setSpacing(8)
        col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t = QLabel(title)
        t.setFont(theme.qfont(16, theme.W_SEMIBOLD))
        t.setStyleSheet(f"color: {pal.text_secondary};")
        col.addWidget(t, 0, Qt.AlignmentFlag.AlignHCenter)
        s = QLabel(subtitle + "  ·  em breve")
        s.setFont(theme.qfont(12.5))
        s.setStyleSheet(f"color: {pal.text_tertiary};")
        col.addWidget(s, 0, Qt.AlignmentFlag.AlignHCenter)
        return self._scroll_pane(inner)

    def _soon_badge(self) -> QLabel:
        pal = theme.palette()
        b = QLabel("em breve")
        b.setFont(theme.qfont(10, theme.W_SEMIBOLD, mono=True))
        b.setStyleSheet(
            f"color: {pal.text_tertiary}; background: {pal.inset}; "
            f"border-radius: 6px; padding: 3px 8px;")
        return b

    def _custom_row_soon(self, label: str) -> QWidget:
        return self._custom_row(label, self._soon_badge())

    def _note_row(self, text: str) -> QWidget:
        pal = theme.palette()
        row = QWidget(); row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row); lay.setContentsMargins(14, 9, 14, 11)
        lbl = QLabel(text)
        lbl.setFont(theme.qfont(11.5))
        lbl.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(lbl)
        return row

    # ------------------------------------------------------------- handlers

    def _set(self, attr: str, value) -> None:
        setattr(self._cfg, attr, value)
        self._cfg.save()
        self.config_changed.emit()

    def _on_theme(self, pref: str) -> None:
        self.theme_changed.emit(pref)

    def _menu(self, anchor, options, current, on_pick) -> None:
        pal = theme.palette()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
        QMenu {{ background: {pal.surface}; border: 1px solid {pal.border_strong};
            border-radius: 10px; padding: 6px; color: {pal.text_primary};
            font-size: 13px; }}
        QMenu::item {{ padding: 7px 26px 7px 12px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {pal.hover}; }}
        """)
        for value, label in options:
            act = menu.addAction(label); act.setData(value)
            if value == current:
                act.setCheckable(True); act.setChecked(True)
        chosen = menu.exec(anchor.mapToGlobal(QPoint(0, anchor.height())))
        if chosen is not None:
            on_pick(chosen.data())

    def _pick_model(self) -> None:
        self._menu(self._row_model, [(m, m) for m in _WHISPER_MODELS],
                   self._cfg.model_size, self._set_model)

    def _set_model(self, m: str) -> None:
        self._cfg.model_size = m
        self._cfg.save()
        self._row_model.set_value(m)
        self.config_changed.emit()

    def _pick_quality(self) -> None:
        opts = [
            ("quality", "Qualidade"),
            ("balanced", "Equilíbrio"),
            ("light", "Leve"),
        ]
        self._menu(self._row_quality, opts, self._cfg.quality_preset,
                   self._set_quality)

    def _set_quality(self, value: str) -> None:
        self._cfg.quality_preset = value
        self._cfg.save()
        labels = {
            "quality": "Qualidade", "balanced": "Equilíbrio", "light": "Leve",
        }
        self._row_quality.set_value(labels.get(value, "Qualidade"))
        self.config_changed.emit()

    def _pick_mic(self) -> None:
        opts = [(None, "Padrão do sistema")]
        opts.extend((name, name) for name in list_input_devices())
        self._menu(self._row_mic, opts, self._cfg.mic_device, self._set_mic)

    def _set_mic(self, value) -> None:
        self._cfg.mic_device = value
        self._cfg.save()
        self._row_mic.set_value(value or "Padrão do sistema")
        self.config_changed.emit()

    def _pick_mouse(self) -> None:
        self._menu(self._row_mouse, list(_MOUSE_LABELS.items()),
                   self._cfg.mouse_button, self._set_mouse)

    def _set_mouse(self, value: str) -> None:
        self._cfg.mouse_button = value
        self._cfg.save()
        self._row_mouse.set_value(_MOUSE_LABELS.get(value, "Nenhum"))
        self.config_changed.emit()

    # ------------------------------------------------------------- sync/retheme

    def sync_from_config(self) -> None:
        """Re-sincroniza os toggles com a config (sem emitir)."""
        for tg, attr in (
            (getattr(self, "_tg_autostart", None), "autostart"),
            (getattr(self, "_tg_startmin", None), "start_minimized"),
            (getattr(self, "_tg_paste", None), "paste_after_transcribe"),
            (getattr(self, "_tg_overlay", None), "show_overlay"),
            (getattr(self, "_tg_sound", None), "play_sound"),
            (getattr(self, "_tg_automode", None), "auto_mode"),
            (getattr(self, "_tg_vcmd", None), "voice_commands"),
            (getattr(self, "_tg_glass", None), "glass"),
            (getattr(self, "_tg_smart", None), "smart_economy"),
            (getattr(self, "_tg_start_armed", None), "start_armed"),
            (getattr(self, "_tg_preload", None), "preload_asr"),
            (getattr(self, "_tg_ollama_boot", None), "ollama_autostart"),
            (getattr(self, "_tg_ollama_quit", None), "ollama_unload_on_quit"),
            (getattr(self, "_tg_unload", None), "unload_idle"),
        ):
            if tg is not None:
                tg.set_checked(getattr(self._cfg, attr), animate=False)

    def retheme(self) -> None:
        cur = self._current
        super().apply_theme()
        # limpa o body e reconstrói (rebuild garante re-tema completo)
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _clear_layout(item.layout())
        self._current = cur
        self._build()


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())
