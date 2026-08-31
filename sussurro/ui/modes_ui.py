"""Modos (tela 06) — gerenciador em grade + editor completo.

Standalone agora (diálogos próprios); no passo 6 o gerenciador vira o conteúdo
da aba "Modos" dos Ajustes. O editor reusa o FramelessWindow.

- Gerenciador: grade 2 colunas de cards (tile + toggle + nome + descrição); o
  modo ativo tem borda verde; último card = "Novo modo" tracejado.
- Editor: header (tile 44 + nome + "ativo · usado N vezes" + toggle grande),
  Nome, Cor (7 swatches), Ícone (glyphs), Modelo, Instrução (+ restaurar padrão
  só built-in), Atalho (DESABILITADO "em breve"), Pré-visualização (estática) e
  footer (Cancelar / Salvar).
"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from sussurro.llm import modes as M
from sussurro.llm.modes import DEFAULT_LLM_LABEL, Mode, ModeStore
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components.window_frame import FramelessWindow

# ===========================================================================
# Seletor de cor (7 swatches) e de ícone (glyphs)
# ===========================================================================

class _Swatch(QWidget):
    picked = Signal(str)

    def __init__(self, color_key: str, parent=None) -> None:
        super().__init__(parent)
        self._key = color_key
        self._selected = False
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, v: bool) -> None:
        self._selected = v
        self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._key)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        c = theme.qcolor(theme.mode_swatch(self._key, not pal.is_dark))
        cx = cy = 16
        if self._selected:
            # anel duplo: cor (r12) — gap surface — cor cheia (r8)
            p.setBrush(c)
            p.drawEllipse(QRectF(cx - 14, cy - 14, 28, 28))
            p.setBrush(theme.qcolor(pal.surface))
            p.drawEllipse(QRectF(cx - 11, cy - 11, 22, 22))
        p.setBrush(c)
        p.drawEllipse(QRectF(cx - 9, cy - 9, 18, 18))


class _ColorRow(QWidget):
    changed = Signal(str)

    def __init__(self, selected: str, parent=None) -> None:
        super().__init__(parent)
        self._selected = selected
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._swatches: list[_Swatch] = []
        for s in theme.MODE_PALETTE:
            sw = _Swatch(s.key, self)
            sw.set_selected(s.key == selected)
            sw.picked.connect(self._on_pick)
            lay.addWidget(sw)
            self._swatches.append(sw)

    def _on_pick(self, key: str) -> None:
        self._selected = key
        for sw in self._swatches:
            sw.set_selected(sw._key == key)  # noqa: SLF001
        self.changed.emit(key)

    def value(self) -> str:
        return self._selected


class _IconOption(QWidget):
    picked = Signal(str)

    def __init__(self, glyph: str, color_key: str, parent=None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self._color = color_key
        self._selected = False
        self.setFixedSize(38, 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color_key: str) -> None:
        self._color = color_key
        self.update()

    def set_selected(self, v: bool) -> None:
        self._selected = v
        self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._glyph)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        light = not theme.is_dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        color = theme.qcolor(theme.mode_swatch(self._color, light))
        tile = QRectF(4, 4, 30, 30)
        if self._selected:
            ring = theme.qcolor(theme.mode_swatch(self._color, light))
            p.setBrush(ring)
            p.drawRoundedRect(QRectF(1, 1, 36, 36), 11, 11)
            p.setBrush(theme.qcolor(theme.palette().surface))
            p.drawRoundedRect(QRectF(2.5, 2.5, 33, 33), 10, 10)
        p.setBrush(color)
        p.drawRoundedRect(tile, 8, 8)
        p.setFont(theme.qfont(13, theme.W_SEMIBOLD, mono=True))
        p.setPen(theme.qcolor(theme.mode_glyph_color(self._color)))
        p.drawText(tile, Qt.AlignmentFlag.AlignCenter, self._glyph)


class _IconRow(QWidget):
    changed = Signal(str)

    def __init__(self, selected: str, color_key: str, parent=None) -> None:
        super().__init__(parent)
        self._selected = selected
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._opts: list[_IconOption] = []
        glyphs = list(theme.MODE_GLYPHS)
        if selected not in glyphs:
            glyphs = [selected, *glyphs]
        for g in glyphs:
            o = _IconOption(g, color_key, self)
            o.set_selected(g == selected)
            o.picked.connect(self._on_pick)
            lay.addWidget(o)
            self._opts.append(o)

    def _on_pick(self, glyph: str) -> None:
        self._selected = glyph
        for o in self._opts:
            o.set_selected(o._glyph == glyph)  # noqa: SLF001
        self.changed.emit(glyph)

    def set_color(self, color_key: str) -> None:
        for o in self._opts:
            o.set_color(color_key)

    def value(self) -> str:
        return self._selected


# ===========================================================================
# Card de modo + card "novo"
# ===========================================================================

class _ModeCard(QWidget):
    clicked = Signal(str)
    toggled = Signal(str, bool)

    def __init__(self, mode: Mode, is_active: bool, parent=None) -> None:
        super().__init__(parent)
        self._mode = mode
        self._is_active = is_active
        self.setObjectName("ModeCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(110)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 13, 14, 13)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(kit.ModeIconTile(mode.color, mode.glyph, 28),
                      0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch(1)
        self._tg = kit.IOSToggle(mode.active, size="small")
        self._tg.toggled.connect(lambda v: self.toggled.emit(self._mode.id, v))
        top.addWidget(self._tg, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(top)

        pal = theme.palette()
        name = QLabel(mode.name)
        name.setFont(theme.qfont(14, theme.W_SEMIBOLD))
        name.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(name)
        desc = QLabel(mode.description)
        desc.setFont(theme.qfont(12))
        desc.setStyleSheet(f"color: {pal.text_secondary}; background: transparent;")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        lay.addStretch(1)
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        if self._is_active:
            border = theme.mode_swatch("green", not pal.is_dark)
        else:
            border = pal.border_subtle
        self.setStyleSheet(f"""
        QWidget#ModeCard {{
            background: {pal.surface};
            border: 1px solid {border};
            border-radius: {theme.RADIUS_CARD}px;
        }}
        QWidget#ModeCard:hover {{ border: 1px solid {pal.border_strong}; }}
        """)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton \
                and not self._tg.geometry().contains(e.pos()):
            self.clicked.emit(self._mode.id)


class _NewCard(QWidget):
    clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("NewCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(110)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl = QLabel("+  Novo modo")
        self._lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._lbl)
        self.apply_theme()

    def apply_theme(self) -> None:
        pal = theme.palette()
        self._lbl.setStyleSheet(
            f"color: {pal.text_secondary}; background: transparent;")
        self.setStyleSheet(f"""
        QWidget#NewCard {{
            background: transparent;
            border: 1px dashed {pal.border_strong};
            border-radius: {theme.RADIUS_CARD}px;
        }}
        QWidget#NewCard:hover {{ border: 1px dashed {pal.link}; }}
        """)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ===========================================================================
# Gerenciador (conteúdo da aba Modos)
# ===========================================================================

class ModesManager(QWidget):
    edit_requested = Signal(str)
    new_requested = Signal()
    changed = Signal()

    def __init__(self, store: ModeStore, active_id: str, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._active_id = active_id
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 18, 20, 20)
        self._lay.setSpacing(16)
        self._build()

    def set_active_id(self, mode_id: str) -> None:
        self._active_id = mode_id
        self.refresh()

    def _build(self) -> None:
        pal = theme.palette()
        head = QHBoxLayout()
        title = QLabel("Modos")
        title.setFont(theme.qfont(20, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        title.setStyleSheet(f"color: {pal.text_primary};")
        head.addWidget(title)
        head.addStretch(1)
        new_btn = kit.PrimaryButton("+ Novo modo")
        new_btn.clicked.connect(self.new_requested.emit)
        head.addWidget(new_btn)
        self._lay.addLayout(head)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)
        self._lay.addWidget(self._grid_host)
        self._lay.addStretch(1)
        self._populate()

    def _populate(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        modes = self._store.all()
        for i, m in enumerate(modes):
            card = _ModeCard(m, m.id == self._active_id)
            card.clicked.connect(self.edit_requested.emit)
            card.toggled.connect(self._on_toggle)
            self._grid.addWidget(card, i // 2, i % 2)
        nc = _NewCard()
        nc.clicked.connect(self.new_requested.emit)
        n = len(modes)
        self._grid.addWidget(nc, n // 2, n % 2)

    def _on_toggle(self, mode_id: str, active: bool) -> None:
        self._store.set_active(mode_id, active)
        self.changed.emit()

    def refresh(self) -> None:
        self._populate()


# ===========================================================================
# Editor de modo (diálogo)
# ===========================================================================

class ModeEditor(FramelessWindow):
    saved = Signal(str)        # id salvo
    deleted = Signal(str)

    def __init__(self, store: ModeStore, mode_id: str | None = None,
                 parent=None) -> None:
        super().__init__(width=600, dialog=True, parent=parent)
        self._store = store
        self._is_new = mode_id is None
        if self._is_new:
            self._mode = Mode(id="", name="", description="", color="purple",
                              glyph="★", prompt="", builtin=False)
        else:
            self._mode = replace(store.get(mode_id))  # cópia editável
        self._build()

    # --------------------------------------------------------------- build

    def _build(self) -> None:
        pal = theme.palette()
        bar = kit.WindowTitleBar(
            "Novo modo" if self._is_new else "Editar modo", show_minimize=False)
        bar.close_requested.connect(self.close)
        self.body.addWidget(bar)

        host = QWidget()
        self.body.addWidget(host, 1)
        c = QVBoxLayout(host)
        c.setContentsMargins(22, 8, 22, 16)
        c.setSpacing(16)

        # --- header (tile 44 + nome + meta + toggle grande) ---
        head = QHBoxLayout(); head.setSpacing(14)
        self._tile = kit.ModeIconTile(self._mode.color, self._mode.glyph, 44)
        head.addWidget(self._tile, 0, Qt.AlignmentFlag.AlignVCenter)
        head_col = QVBoxLayout(); head_col.setSpacing(3)
        self._head_name = QLabel(self._mode.name or "Novo modo")
        self._head_name.setFont(theme.qfont(17, theme.W_SEMIBOLD,
                                            tracking=theme.TRACK_TITLE))
        self._head_name.setStyleSheet(f"color: {pal.text_primary};")
        head_col.addWidget(self._head_name)
        meta = "ativo" if self._mode.active else "inativo"
        if not self._is_new:
            meta += f" · usado {self._mode.usage_count} vezes"
        self._head_meta = QLabel(meta)
        self._head_meta.setFont(theme.qfont(12))
        self._head_meta.setStyleSheet(f"color: {pal.text_secondary};")
        head_col.addWidget(self._head_meta)
        head.addLayout(head_col)
        head.addStretch(1)
        self._active_tg = kit.IOSToggle(self._mode.active, size="large")
        self._active_tg.toggled.connect(self._on_active)
        head.addWidget(self._active_tg, 0, Qt.AlignmentFlag.AlignVCenter)
        c.addLayout(head)

        # --- Nome ---
        c.addWidget(self._field_label("Nome"))
        self._name = kit.LineEdit(self._mode.name, "Nome do modo")
        self._name.textChanged.connect(self._on_name)
        c.addWidget(self._name)

        # --- Cor ---
        c.addWidget(self._field_label("Cor"))
        self._colors = _ColorRow(self._mode.color)
        self._colors.changed.connect(self._on_color)
        c.addWidget(self._colors)

        # --- Ícone ---
        c.addWidget(self._field_label("Ícone"))
        self._icons = _IconRow(self._mode.glyph, self._mode.color)
        self._icons.changed.connect(self._on_glyph)
        c.addWidget(self._icons)

        # --- Modelo ---
        c.addWidget(self._field_label("Modelo"))
        mcard = kit.GroupCard()
        self._model_row = kit.ValueRow("LLM", DEFAULT_LLM_LABEL)
        mcard.add_row(self._model_row)
        c.addWidget(mcard)

        # --- Instrução pro modelo ---
        instr_head = QHBoxLayout()
        instr_head.addWidget(self._field_label("Instrução pro modelo"))
        instr_head.addStretch(1)
        if self._mode.builtin:
            restore = kit.GhostButton("restaurar padrão", accent=True)
            restore.clicked.connect(self._restore_prompt)
            instr_head.addWidget(restore)
        c.addLayout(instr_head)
        self._prompt = kit.TextArea(
            self._mode.prompt,
            "Descreva como o modelo deve transformar o texto…")
        self._prompt.setFixedHeight(120)
        c.addWidget(self._prompt)

        # --- Atalho direto (DESABILITADO / em breve) ---
        c.addWidget(self._field_label("Atalho direto"))
        c.addWidget(self._shortcut_field())

        # --- Pré-visualização (estática) ---
        c.addWidget(self._field_label("Pré-visualização"))
        c.addWidget(self._preview())

        # --- footer (sticky) ---
        foot = QWidget()
        foot.setObjectName("EditorFooter")
        foot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        foot.setStyleSheet(
            f"QWidget#EditorFooter {{ background: {pal.window}; "
            f"border-top: 1px solid {pal.divider}; }}")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(22, 12, 22, 14)
        if not self._is_new and not self._mode.builtin:
            del_btn = kit.GhostButton("excluir modo")
            del_btn.clicked.connect(self._delete)
            fl.addWidget(del_btn)
        fl.addStretch(1)
        cancel = kit.SecondaryButton("Cancelar")
        cancel.clicked.connect(self.close)
        fl.addWidget(cancel)
        self._save_btn = kit.PrimaryButton("Salvar modo")
        self._save_btn.clicked.connect(self._save)
        fl.addWidget(self._save_btn)
        self.body.addWidget(foot)

        self._update_save_enabled()

    def retheme(self) -> None:
        """Reconstrói com o tema novo (rebuild garante re-tema completo do
        footer/preview que têm fundo cravado). Preserva as edições: nome/cor/
        glyph/active já vivem em _mode; o prompt só sincroniza no save."""
        self._mode.prompt = self._prompt.toPlainText()
        super().apply_theme()
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._build()

    # --------------------------------------------------------------- helpers

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(theme.qfont(11, theme.W_SEMIBOLD, tracking=theme.TRACK_LABEL))
        lbl.setStyleSheet(
            f"color: {theme.palette().text_tertiary}; text-transform: uppercase;")
        return lbl

    def _shortcut_field(self) -> QWidget:
        pal = theme.palette()
        w = QWidget()
        w.setObjectName("ShortcutField")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        w.setStyleSheet(f"""
        QWidget#ShortcutField {{
            background: transparent;
            border: 1px dashed {pal.border_strong};
            border-radius: {theme.RADIUS_INPUT}px;
        }}
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 11, 12, 11)
        lbl = QLabel("+ definir atalho")
        lbl.setFont(theme.qfont(13))
        lbl.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        badge = QLabel("em breve")
        badge.setFont(theme.qfont(10, theme.W_SEMIBOLD, mono=True))
        badge.setStyleSheet(
            f"color: {pal.text_tertiary}; background: {pal.inset}; "
            f"border-radius: 6px; padding: 3px 8px;")
        lay.addWidget(badge)
        w.setEnabled(False)
        return w

    def _preview(self) -> QWidget:
        pal = theme.palette()
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        before = self._preview_box(
            "Antes", "humm, então tipo, eu queria... eu queria revisar o "
            "contrato, sabe?", pal.inset, pal.text_secondary, pal.border_subtle)
        lay.addWidget(before, 1)

        arrow = QLabel("→")
        arrow.setFont(theme.qfont(16, theme.W_MEDIUM))
        arrow.setStyleSheet(f"color: {pal.text_tertiary};")
        lay.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)

        green = theme.mode_swatch("green", not pal.is_dark)
        after = self._preview_box(
            "Depois", "Eu queria revisar o contrato.",
            theme.rgba(green, 0.10), pal.text_primary,
            theme.rgba(green, 0.30))
        lay.addWidget(after, 1)
        return w

    def _preview_box(self, tag: str, text: str, bg: str, fg: str,
                     border: str) -> QWidget:
        box = QWidget()
        box.setObjectName("PreviewBox")
        box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        box.setStyleSheet(f"""
        QWidget#PreviewBox {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 10px;
        }}
        """)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(6)
        t = QLabel(tag.upper())
        t.setFont(theme.qfont(10, theme.W_SEMIBOLD, mono=True))
        t.setStyleSheet(
            f"color: {theme.palette().text_tertiary}; background: transparent;")
        lay.addWidget(t)
        body = QLabel(text)
        body.setFont(theme.qfont(12))
        body.setStyleSheet(f"color: {fg}; background: transparent;")
        body.setWordWrap(True)
        lay.addWidget(body)
        return box

    # --------------------------------------------------------------- signals

    def _on_name(self, text: str) -> None:
        self._mode.name = text
        self._head_name.setText(text or "Novo modo")
        self._update_save_enabled()

    def _on_color(self, key: str) -> None:
        self._mode.color = key
        self._tile.set_mode(key, self._mode.glyph)
        self._icons.set_color(key)

    def _on_glyph(self, glyph: str) -> None:
        self._mode.glyph = glyph
        self._tile.set_mode(self._mode.color, glyph)

    def _on_active(self, v: bool) -> None:
        self._mode.active = v
        meta = "ativo" if v else "inativo"
        if not self._is_new:
            meta += f" · usado {self._mode.usage_count} vezes"
        self._head_meta.setText(meta)

    def _restore_prompt(self) -> None:
        self._prompt.setPlainText(M.default_prompt(self._mode.id))

    def _update_save_enabled(self) -> None:
        self._save_btn.setEnabled(bool(self._mode.name.strip()))

    def _save(self) -> None:
        self._mode.prompt = self._prompt.toPlainText()
        if self._is_new:
            self._mode.id = self._store.new_id(self._mode.name)
            self._store.add(self._mode)
        else:
            self._store.update(self._mode)
        self.saved.emit(self._mode.id)
        self.close()

    def _delete(self) -> None:
        if self._store.delete(self._mode.id):
            self.deleted.emit(self._mode.id)
            self.close()
