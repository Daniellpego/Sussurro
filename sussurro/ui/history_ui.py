"""Histórico (tela 04) — janela separada com busca, agrupamento por dia e copiar.

Dados reais do History store. Dark = linhas divididas; light = cards brancos.
Busca filtra em tempo real; clique copia (com toast "Copiado"); "limpar tudo"
pede confirmação; delete individual no hover. Estados vazios tratados.
"""
from __future__ import annotations

import time

import pyperclip
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from sussurro.llm import modes as M
from sussurro.storage.history import History
from sussurro.ui import components as kit
from sussurro.ui import icons, theme
from sussurro.ui.components.confirm import ConfirmDialog
from sussurro.ui.components.window_frame import FramelessWindow

_RENDER_CAP = 150


def _relative_label(ts: float) -> str:
    delta = max(0.0, time.time() - ts)
    if delta < 60:
        return "agora"
    if delta < 3600:
        return f"{int(delta // 60)}m"
    same_day = (time.strftime("%Y-%m-%d", time.localtime(ts))
                == time.strftime("%Y-%m-%d"))
    if same_day:
        return f"{int(delta // 3600)}h"
    return time.strftime("%H:%M", time.localtime(ts))


def _day_group(ts: float) -> str:
    d = time.strftime("%Y-%m-%d", time.localtime(ts))
    if d == time.strftime("%Y-%m-%d"):
        return "Hoje"
    if d == time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400)):
        return "Ontem"
    return time.strftime("%d/%m/%Y", time.localtime(ts))


def _chip_data(mode_id: str):
    """(nome, cor) do chip; modo deletado -> neutro (não quebra)."""
    light = not theme.is_dark()
    store = M.active()
    if store.exists(mode_id):
        m = store.get(mode_id)
        return m.name, theme.mode_swatch(m.color, light)
    return mode_id.capitalize(), theme.palette().text_secondary


class _Chip(QWidget):
    def __init__(self, name: str, color: str, parent=None) -> None:
        super().__init__(parent)
        self._name = name
        self._color = color
        self._font = theme.qfont(10.5, theme.W_SEMIBOLD)
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance(name) + 16, fm.height() + 6)

    def paintEvent(self, e: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(theme.rgba(self._color, 0.16)))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 7, 7)
        p.setFont(self._font)
        p.setPen(theme.qcolor(self._color))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._name)


class _HistItem(QWidget):
    copied = Signal(str)
    deleted = Signal(float)

    def __init__(self, entry, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setObjectName("HistItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        pal = theme.palette()
        light = not pal.is_dark

        if light:
            self.setStyleSheet(f"""
            QWidget#HistItem {{ background: {pal.surface};
                border: 1px solid {pal.border_subtle}; border-radius: 11px; }}
            QWidget#HistItem:hover {{ border: 1px solid {pal.border_strong}; }}
            """)
        else:
            self.setStyleSheet(f"""
            QWidget#HistItem {{ background: transparent;
                border-bottom: 1px solid {pal.divider}; }}
            QWidget#HistItem:hover {{ background: {theme.rgba(pal.text_primary, 0.03)}; }}
            """)

        lay = QVBoxLayout(self)
        if light:
            lay.setContentsMargins(14, 12, 14, 12)
        else:
            lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(7)

        top = QHBoxLayout(); top.setSpacing(8)
        name, color = _chip_data(entry.mode)
        top.addWidget(_Chip(name, color), 0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch(1)
        self._del = QLabel("×")
        self._del.setFont(theme.qfont(14))
        self._del.setStyleSheet(f"color: {pal.text_tertiary}; background: transparent;")
        self._del.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del.setVisible(False)
        self._del.mouseReleaseEvent = self._on_delete  # type: ignore[method-assign]
        top.addWidget(self._del, 0, Qt.AlignmentFlag.AlignVCenter)
        ts = QLabel(_relative_label(entry.timestamp))
        ts.setFont(theme.qfont(11, theme.W_MEDIUM, mono=True))
        ts.setStyleSheet(f"color: {pal.text_mono_dim}; background: transparent;")
        top.addWidget(ts, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(top)

        body = QLabel(entry.text.strip())
        body.setWordWrap(True)
        is_code = entry.mode == "code"
        if is_code:
            body.setFont(theme.qfont(12.5, theme.W_REGULAR, mono=True))
            body.setStyleSheet(
                f"color: {theme.code_text()}; background: transparent;")
        else:
            body.setFont(theme.qfont(13.5))
            body.setStyleSheet(f"color: {pal.text_body_card}; background: transparent;")
        # clamp ~2 linhas
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(body.font())
        body.setMaximumHeight(int(fm.lineSpacing() * 2.2))
        lay.addWidget(body)

    def enterEvent(self, e) -> None:  # noqa: N802
        self._del.setVisible(True)

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._del.setVisible(False)

    def _on_delete(self, e) -> None:
        self.deleted.emit(self._entry.timestamp)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            try:
                pyperclip.copy(self._entry.text)
            except Exception:  # noqa: BLE001
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(self._entry.text)
            self.copied.emit(self._entry.text)


class _SearchBox(QWidget):
    textChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        pal = theme.palette()
        self.setObjectName("SearchBox")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
        QWidget#SearchBox {{ background: {pal.surface};
            border: 1px solid {pal.border_subtle}; border-radius: 11px; }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(13, 9, 13, 9)
        lay.setSpacing(9)
        ico = QLabel()
        ico.setPixmap(icons.pixmap("search", color=pal.text_tertiary, size=15))
        lay.addWidget(ico, 0, Qt.AlignmentFlag.AlignVCenter)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("Buscar transcrições…")
        self._edit.setFont(theme.qfont(13.5))
        self._edit.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; "
            f"color: {pal.text_primary}; }}")
        self._edit.textChanged.connect(self.textChanged.emit)
        lay.addWidget(self._edit, 1)


class HistoryWindow(FramelessWindow):
    def __init__(self, history: History, parent=None) -> None:
        super().__init__(width=540, parent=parent)
        self._history = history
        self._filter = ""
        self._build()
        self.refresh()

    def _build(self) -> None:
        pal = theme.palette()
        bar = kit.WindowTitleBar("Histórico", show_minimize=False)
        bar.close_requested.connect(self.hide)
        self.body.addWidget(bar)

        self._search = _SearchBox()
        self._search.textChanged.connect(self._on_search)
        sw = QWidget(); sl = QVBoxLayout(sw)
        sl.setContentsMargins(18, 0, 18, 8); sl.addWidget(self._search)
        self.body.addWidget(sw)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
        QScrollArea {{ background: transparent; }}
        QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {theme.rgba(pal.text_primary, 0.16)};
            border-radius: 4px; min-height: 30px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
        """)
        self._list_host = QWidget()
        self._list_host.setObjectName("HistList")
        self._list_host.setStyleSheet(
            f"QWidget#HistList {{ background: {pal.window}; }}")
        self._scroll.viewport().setStyleSheet(f"background: {pal.window};")
        self._list = QVBoxLayout(self._list_host)
        self._list.setContentsMargins(0, 4, 0, 8)
        self._list.setSpacing(0)
        self._scroll.setWidget(self._list_host)
        self.body.addWidget(self._scroll, 1)
        self._root.setMinimumHeight(560)

        foot = QWidget()
        foot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        foot.setStyleSheet(
            f"background: transparent; border-top: 1px solid {pal.divider};")
        fl = QHBoxLayout(foot); fl.setContentsMargins(18, 12, 18, 12)
        self._count = QLabel("")
        self._count.setFont(theme.qfont(11, theme.W_MEDIUM, mono=True))
        self._count.setStyleSheet(f"color: {pal.text_mono_dim};")
        fl.addWidget(self._count)
        fl.addStretch(1)
        self._clear = kit.GhostButton("limpar tudo")
        self._clear.clicked.connect(self._confirm_clear)
        fl.addWidget(self._clear)
        self.body.addWidget(foot)

        # toast "Copiado"
        self._toast = QLabel("Copiado", self)
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setFont(theme.qfont(12, theme.W_SEMIBOLD))
        self._toast.setStyleSheet(
            f"background: {pal.text_primary}; color: {pal.window}; "
            f"border-radius: 9px; padding: 8px 16px;")
        self._toast.hide()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast.hide)

    # ------------------------------------------------------------------- API

    def refresh(self) -> None:
        # limpa (setParent(None) é síncrono: evita sobreposição com deleteLater)
        while self._list.count():
            it = self._list.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        entries = self._history.all()
        if self._filter:
            f = self._filter.lower()
            entries = [e for e in entries if f in e.text.lower()]

        total = self._history.count()
        self._count.setText(f"{total} transcriç{'ão' if total == 1 else 'ões'}")
        self._clear.setVisible(total > 0)

        if not entries:
            self._add_empty(
                "Nada encontrado." if self._filter
                else "Nenhuma transcrição ainda.")
            return

        shown = entries[:_RENDER_CAP]
        last_group = None
        for e in shown:
            g = _day_group(e.timestamp)
            if g != last_group:
                self._list.addWidget(self._group_header(g))
                last_group = g
            item = _HistItem(e)
            item.copied.connect(self._on_copied)
            item.deleted.connect(self._on_delete)
            if not theme.is_dark():
                wrap = QWidget(); wl = QVBoxLayout(wrap)
                wl.setContentsMargins(12, 0, 12, 8); wl.addWidget(item)
                self._list.addWidget(wrap)
            else:
                self._list.addWidget(item)

        if len(entries) > _RENDER_CAP:
            more = self._group_header(
                f"+ {len(entries) - _RENDER_CAP} mais — use a busca")
            self._list.addWidget(more)

        self._list.addStretch(1)  # fixa os itens no topo

    def _group_header(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setFont(theme.qfont(10.5, theme.W_SEMIBOLD, mono=True,
                                tracking=theme.TRACK_LABEL))
        lbl.setStyleSheet(
            f"color: {theme.palette().text_mono_dim}; "
            f"padding: 10px 18px 4px; background: transparent;")
        return lbl

    def _add_empty(self, message: str) -> None:
        pal = theme.palette()
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(0, 60, 0, 60)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(message)
        lbl.setFont(theme.qfont(13.5))
        lbl.setStyleSheet(f"color: {pal.text_tertiary};")
        bl.addWidget(lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        self._list.addWidget(box)

    # --------------------------------------------------------------- handlers

    def _on_search(self, text: str) -> None:
        self._filter = text.strip()
        self.refresh()

    def _on_copied(self, _text: str) -> None:
        self._show_toast()

    def _on_delete(self, ts: float) -> None:
        self._history.delete_at(ts)
        self.refresh()

    def _confirm_clear(self) -> None:
        dlg = ConfirmDialog(
            "Limpar histórico?",
            "Isso apaga todas as transcrições salvas. Não dá pra desfazer.",
            confirm_label="Limpar tudo", danger=True, parent=self)
        dlg.confirmed.connect(self._do_clear)
        dlg.show()
        dlg.raise_()
        wp = self.geometry()
        dlg.move(wp.x() + (wp.width() - dlg.width()) // 2,
                 wp.y() + (wp.height() - dlg.height()) // 2)

    def _do_clear(self) -> None:
        self._history.clear()
        self.refresh()

    def _show_toast(self) -> None:
        self._toast.adjustSize()
        self._toast.move((self.width() - self._toast.width()) // 2,
                         self.height() - self._toast.height() - 60)
        self._toast.show()
        self._toast.raise_()
        self._toast_timer.start(1100)

    def retheme(self) -> None:
        """Re-tematiza a janela inteira (rebuild garante re-tema completo)."""
        super().apply_theme()
        if hasattr(self, "_toast"):
            self._toast.deleteLater()
        while self.body.count():
            item = self.body.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                _clear_layout(item.layout())
        self._build()
        self.refresh()


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            _clear_layout(item.layout())
