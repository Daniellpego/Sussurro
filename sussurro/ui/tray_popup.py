"""Popup rico da bandeja (tela 08) — frameless, fecha no clique-fora (Qt.Popup).

Custom (não QMenu nativo) pra bater 100% com o mock: header com brand mini +
dot de status, linha "Modo" destacada com dot da cor + submenu inline, e "Sair"
vermelho. Segue o tema (dark/light).
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from sussurro.llm.modes import ModeStore
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components import nav_icons
from sussurro.ui.components.chevron import Chevron

_M = 22         # margem pra sombra
_W = 256        # largura do card


def _popup_colors():
    """(bg, border, divider, hover) específicos do popup, por tema."""
    return theme.popup_colors()


class _Dot(QWidget):
    def __init__(self, color: str, d: int = 6, parent=None) -> None:
        super().__init__(parent)
        self._c = color
        self._d = d
        self.setFixedSize(d, d)

    def paintEvent(self, e: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._c))
        p.drawEllipse(self.rect())


class _Icon(QWidget):
    """Ícone de linha 16px à esquerda de cada item do menu."""

    def __init__(self, key: str, color: str, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self._color = color
        self.setFixedSize(16, 16)

    def paintEvent(self, e: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        nav_icons.paint(p, self._key, QRectF(0, 0, 16, 16),
                        theme.qcolor(self._color), 1.5)


class _Row(QWidget):
    clicked = Signal()

    def __init__(self, label: str, color: str, *, right: QWidget | None = None,
                 highlight: bool = False, icon: str | None = None,
                 icon_color: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PopRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _bg, _b, _dv, hover = _popup_colors()
        base = hover if highlight else "transparent"
        self.setStyleSheet(
            f"QWidget#PopRow {{ background: {base}; border-radius: 8px; }}"
            f"QWidget#PopRow:hover {{ background: {hover}; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 11, 8)
        lay.setSpacing(10)
        if icon is not None:
            lay.addWidget(_Icon(icon, icon_color or color), 0,
                          Qt.AlignmentFlag.AlignVCenter)
        lbl = QLabel(label)
        lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {color}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        if right is not None:
            lay.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class TrayPopup(QWidget):
    open_window = Signal()
    open_history = Signal()
    open_settings = Signal()
    toggle_pause = Signal()
    quit_app = Signal()
    pick_mode = Signal(str)

    def __init__(self, store: ModeStore, active_mode: str,
                 status: tuple[str, str], paused: bool, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._active = active_mode
        self._status = status        # (cor, texto)
        self._paused = paused
        self._view = "main"
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        bg, border, divider, hover = _popup_colors()
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(_M, _M, _M, _M)
        self._card = QWidget(self)
        self._card.setObjectName("PopCard")
        self._card.setFixedWidth(_W)
        self._card.setStyleSheet(
            f"QWidget#PopCard {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: 13px; }}")
        self._outer.addWidget(self._card)

        from PySide6.QtWidgets import QStackedWidget
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(6, 6, 6, 6)
        card_lay.setSpacing(0)
        self._stack = QStackedWidget()
        page_main = QWidget()
        self._build_main(QVBoxLayout(page_main), divider)
        page_modes = QWidget()
        self._build_modes(QVBoxLayout(page_modes), divider)
        self._stack.addWidget(page_main)
        self._stack.addWidget(page_modes)
        card_lay.addWidget(self._stack)
        self.adjustSize()

    def _page_layout(self, lay: QVBoxLayout) -> QVBoxLayout:
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        return lay

    def _divider(self, color: str) -> QWidget:
        d = QWidget()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background: {color};")
        wrap = QWidget()
        wl = QHBoxLayout(wrap)
        wl.setContentsMargins(8, 5, 8, 5)
        wl.addWidget(d)
        return wrap

    def _build_main(self, lay: QVBoxLayout, divider: str) -> None:
        self._page_layout(lay)
        pal = theme.palette()
        # header
        head = QWidget()
        hl = QHBoxLayout(head)
        hl.setContentsMargins(11, 9, 11, 9)
        hl.setSpacing(10)
        hl.addWidget(kit.BrandMark(28), 0, Qt.AlignmentFlag.AlignVCenter)
        col = QVBoxLayout(); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(3)
        name = QLabel("Sussurro")
        name.setFont(theme.qfont(13, theme.W_SEMIBOLD))
        name.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        col.addWidget(name)
        st = QHBoxLayout(); st.setContentsMargins(0, 0, 0, 0); st.setSpacing(5)
        st.addWidget(_Dot(self._status[0], 5), 0, Qt.AlignmentFlag.AlignVCenter)
        stl = QLabel(self._status[1])
        stl.setFont(theme.qfont(11, theme.W_MEDIUM))
        stl.setStyleSheet(f"color: {self._status[0]}; background: transparent;")
        st.addWidget(stl); st.addStretch(1)
        sw = QWidget(); sw.setLayout(st)
        col.addWidget(sw)
        hl.addLayout(col); hl.addStretch(1)
        lay.addWidget(head)
        lay.addWidget(self._divider(divider))

        # Modo (destacada) + dot da cor + chevron
        m = self._store.get(self._active)
        right = QWidget()
        rl = QHBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(5)
        rl.addWidget(_Dot(theme.mode_swatch(m.color, not pal.is_dark), 6),
                     0, Qt.AlignmentFlag.AlignVCenter)
        mv = QLabel(m.name)
        mv.setFont(theme.qfont(12.5, theme.W_MEDIUM))
        mv.setStyleSheet(f"color: {pal.text_secondary}; background: transparent;")
        rl.addWidget(mv)
        rl.addWidget(Chevron(arm=5), 0, Qt.AlignmentFlag.AlignVCenter)
        row_mode = _Row("Modo", pal.text_primary, right=right, highlight=True,
                        icon="modos", icon_color=pal.text_secondary)
        row_mode.clicked.connect(self._show_modes)
        lay.addWidget(row_mode)
        lay.addWidget(self._divider(divider))

        text_color = pal.text_primary if pal.is_dark else theme.POPUP_TEXT_LIGHT
        for label, icon, sig in (("Abrir janela", "janela", self.open_window),
                                 ("Histórico", "historico", self.open_history),
                                 ("Ajustes", "ajustes", self.open_settings)):
            r = _Row(label, text_color, icon=icon, icon_color=pal.text_secondary)
            r.clicked.connect(lambda s=sig: (s.emit(), self.close()))
            lay.addWidget(r)
        lay.addWidget(self._divider(divider))

        # Interruptor de memória: Ativar = pode ditar (e gastar VRAM).
        # Desativar = solta Whisper/Qwen da GPU e fica leve na bandeja.
        if self._paused:
            rp = _Row("Retomar ditado", pal.state(theme.READY),
                      icon="retomar")
        else:
            rp = _Row("Pausar e liberar memória", text_color,
                      icon="pausar", icon_color=pal.text_secondary)
        rp.clicked.connect(lambda: (self.toggle_pause.emit(), self.close()))
        lay.addWidget(rp)

        rq = _Row("Sair", pal.state_text(theme.ERROR), icon="sair")
        rq.clicked.connect(lambda: (self.quit_app.emit(), self.close()))
        lay.addWidget(rq)

    def _build_modes(self, lay: QVBoxLayout, divider: str) -> None:
        self._page_layout(lay)
        pal = theme.palette()
        back = _Row("‹  Modo", pal.text_secondary)
        back.clicked.connect(self._show_main)
        lay.addWidget(back)
        lay.addWidget(self._divider(divider))
        for m in self._store.active_modes():
            right = None
            if m.id == self._active:
                chk = QLabel("✓")
                chk.setFont(theme.qfont(13, theme.W_SEMIBOLD))
                chk.setStyleSheet(
                    f"color: {pal.state(theme.READY)}; background: transparent;")
                right = chk
            dot = _Dot(theme.mode_swatch(m.color, not pal.is_dark), 6)
            r = _ModeRow(m.name, dot, right, pal)
            r.clicked.connect(lambda mid=m.id: (self.pick_mode.emit(mid), self.close()))
            lay.addWidget(r)

    def _show_modes(self) -> None:
        self._stack.setCurrentIndex(1)
        self.adjustSize()

    def _show_main(self) -> None:
        self._stack.setCurrentIndex(0)
        self.adjustSize()

    # --------------------------------------------------------------- posição

    def popup_at(self, anchor_global) -> None:
        """Mostra o popup com o canto inferior-direito perto do ponto âncora
        (tipicamente o cursor sobre o ícone da bandeja)."""
        from PySide6.QtGui import QGuiApplication
        self.adjustSize()
        w, h = self.width(), self.height()
        x = anchor_global.x() - w + _M
        y = anchor_global.y() - h + _M
        screen = QGuiApplication.screenAt(anchor_global) or QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            x = max(geo.x() - _M, min(x, geo.right() - w + _M))
            y = max(geo.y() - _M, min(y, geo.bottom() - h + _M))
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------ paint

    def paintEvent(self, e: QPaintEvent) -> None:  # noqa: N802
        # sombra suave atrás do card (QSS não tem box-shadow)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(self._card.geometry())
        dark = theme.is_dark()
        base = QColor(0, 0, 0) if dark else QColor(20, 22, 40)
        per = (0.7 if dark else 0.28) / _M
        for i in range(_M, 0, -1):
            c = QColor(base); c.setAlphaF(per)
            p.setBrush(c)
            g = float(i)
            p.drawRoundedRect(rect.adjusted(-g, -g + 5, g, g + 8), 13 + g, 13 + g)


class _ModeRow(QWidget):
    clicked = Signal()

    def __init__(self, name: str, dot: QWidget, right: QWidget | None, pal,
                 parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PopRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _bg, _b, _dv, hover = _popup_colors()
        self.setStyleSheet(
            f"QWidget#PopRow {{ background: transparent; border-radius: 8px; }}"
            f"QWidget#PopRow:hover {{ background: {hover}; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(11, 8, 11, 8)
        lay.setSpacing(8)
        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        lbl = QLabel(name)
        lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch(1)
        if right is not None:
            lay.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
