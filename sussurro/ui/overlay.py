"""HUD flutuante — pílula premium na base da tela durante o ditado.

Princípios (críticos):
- NÃO rouba foco: Qt.Tool + WindowDoesNotAcceptFocus + WA_ShowWithoutActivating
  + StaysOnTop + translúcido. Se ativar, o Ctrl+V cola no lugar errado.
- O paste é disparado pelo app.py assim que o texto fica pronto; o HUD é só
  feedback visual em paralelo.
- Animações param quando o HUD some (não queima GPU à toa).
- Posição: base da tela da janela em foco (multi-monitor).

Gravando é só a onda numa pílula escura compacta, sem texto, ponto de
gravação nem cronômetro (estilo Wispr Flow).

Estados: gravando · transcrevendo · refinando (LLM) · colado · colado sem IA
· cancelado · nenhuma fala · falha · carregando modelo.
"""
from __future__ import annotations

import math
import time
from collections.abc import Callable

from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from sussurro.ui import theme
from sussurro.ui.components.mode_chip import ModeChip

_FRAME_MS = 33  # ~30fps
_M = theme.HUD_SHADOW_MARGIN
_MAX_TEXT_W = 360


# ===========================================================================
# Sub-widgets animados
# ===========================================================================

class _Anim(QWidget):
    """Base: timer de animação + relógio monotônico; para quando escondido."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._t0 = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(_FRAME_MS)
        self._timer.timeout.connect(self.update)

    def start(self) -> None:
        self._t0 = time.monotonic()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _elapsed(self) -> float:
        return time.monotonic() - self._t0


class _HudWaveform(_Anim):
    """Onda de voz ao vivo no estilo da marca: poucas barras-cápsula simétricas.

    Cada barra fica no lugar e sobe e desce com o volume do microfone, com um
    ritmo próprio (nada rola para o lado). A central é a mais alta, como no
    logo. Em silêncio, as barras viram pontos que "respiram" devagar.
    """

    _PROFILE = (0.42, 0.62, 0.8, 0.94, 1.0, 0.94, 0.8, 0.62, 0.42)

    def __init__(self, level_source: Callable[[], float] | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._level = level_source
        self._n = len(self._PROFILE)
        self._bw = 3.5
        self._gap = 3.5
        # ritmos diferentes por barra para o movimento parecer orgânico
        self._speed = [5.1, 6.3, 4.4, 7.2, 5.6, 6.8, 4.9, 6.0, 5.4]
        self._phase = [i * 1.13 for i in range(self._n)]
        self._heights = [0.0] * self._n
        self._voice = 0.0
        w = self._n * self._bw + (self._n - 1) * self._gap
        self.setFixedSize(math.ceil(w), 20)
        self._timer.setInterval(16)  # 60 fps só enquanto grava
        self._timer.timeout.disconnect()
        self._timer.timeout.connect(self._frame)

    def start(self) -> None:
        self._heights = [0.0] * self._n
        self._voice = 0.0
        super().start()

    def _read_level(self) -> float:
        if self._level is None:
            return 0.0
        try:
            return max(0.0, min(1.0, float(self._level())))
        except Exception:  # noqa: BLE001
            return 0.0

    def _frame(self) -> None:
        # realce perceptual e suavização: sobe rápido, desce devagar
        target = self._read_level() ** 0.6
        k = 0.45 if target > self._voice else 0.12
        self._voice += (target - self._voice) * k

        t = self._elapsed()
        for i in range(self._n):
            wobble = 0.7 + 0.3 * math.sin(t * self._speed[i] + self._phase[i])
            goal = min(1.0, self._voice * 1.3 * self._PROFILE[i] * wobble)
            cur = self._heights[i]
            self._heights[i] = cur + (goal - cur) * (0.5 if goal > cur else 0.2)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        # um único gradiente da marca atravessando a onda inteira
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, theme.qcolor(theme.BRAND_SWEEP[0]))
        grad.setColorAt(0.5, theme.qcolor(theme.BRAND_SWEEP[2]))
        grad.setColorAt(1.0, theme.qcolor(theme.BRAND_SWEEP[4]))
        p.setBrush(grad)

        h = self.height()
        cy = h / 2
        t = self._elapsed()
        radius = self._bw / 2
        x = 0.0
        for i, amp in enumerate(self._heights):
            # respiração discreta em silêncio: pontos que crescem em onda
            breath = 0.5 + 0.5 * math.sin(t * 2.6 - i * 0.55)
            idle = self._bw + 1.6 * breath * (1.0 - min(1.0, self._voice * 4))
            bar_h = max(idle, self._bw + amp * (h - self._bw))
            p.drawRoundedRect(QRectF(x, cy - bar_h / 2, self._bw, bar_h),
                              radius, radius)
            x += self._bw + self._gap


class _BouncingDots(_Anim):
    """3 pontos lavanda — loading de transcrição."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._d = 5.0
        self._gap = 4.5
        self.setFixedSize(int(3 * self._d + 2 * self._gap), 18)

    def _color(self) -> str:
        return theme.LAVENDER if theme.is_dark() else theme.INDIGO

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        elapsed = self._elapsed()
        cy = self.height() / 2
        for i, delay in enumerate((0.0, 0.18, 0.36)):
            phase = ((elapsed - delay) % 1.1) / 1.1
            if phase < 0.35:
                k = phase / 0.35
            elif phase < 0.7:
                k = 1.0 - (phase - 0.35) / 0.35
            else:
                k = 0.0
            ty = -3.5 * k
            col = theme.qcolor(self._color())
            col.setAlphaF(0.28 + 0.72 * k)
            p.setBrush(col)
            x = i * (self._d + self._gap)
            p.drawEllipse(QRectF(x, cy - self._d / 2 + ty, self._d, self._d))


class _Spinner(_Anim):
    """Anel girando com trilha suave."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(16, 16)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1.5, 1.5, 13, 13)
        track = theme.qcolor(theme.LAVENDER)
        track.setAlphaF(0.22)
        pen = QPen(track)
        pen.setWidthF(2.2)
        p.setPen(pen)
        p.drawEllipse(rect)
        ang = (self._elapsed() % 0.75) / 0.75 * 360.0
        # arco com gradiente visual (dois tons)
        pen2 = QPen(theme.qcolor(theme.INDIGO))
        pen2.setWidthF(2.2)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        p.drawArc(rect, int((90 - ang) * 16), -100 * 16)


class _Badge(QWidget):
    """Badge estático 18px (check / cross / erro)."""

    def __init__(self, kind: str, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._kind = kind
        self.setFixedSize(18, 18)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = QRectF(0, 0, 18, 18)
        if self._kind == "check":
            p.setBrush(theme.qcolor(pal.state(theme.READY)))
            p.drawEllipse(r)
            mark = theme.qcolor("#0E0F12" if pal.is_dark else "#FFFFFF")
            pen = QPen(mark)
            pen.setWidthF(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawPolyline([QPointF(5, 9), QPointF(8, 12), QPointF(13, 6)])
        elif self._kind == "cross":
            p.setBrush(theme.qcolor("#3A3D44" if pal.is_dark else "#C9CCD3"))
            p.drawEllipse(r)
            p.setFont(theme.qfont(12, theme.W_REGULAR))
            p.setPen(theme.qcolor(pal.text_secondary))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "×")
        elif self._kind == "error":
            bg = theme.qcolor(pal.state(theme.ERROR))
            bg.setAlphaF(0.18)
            p.setBrush(bg)
            p.drawEllipse(r)
            p.setFont(theme.qfont(12, theme.W_SEMIBOLD))
            p.setPen(theme.qcolor("#FF8A80" if pal.is_dark else "#D9342B"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "!")


class _Dot7(QWidget):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._color = color
        self.setFixedSize(7, 7)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.qcolor(self._color))
        p.drawEllipse(self.rect())


# ===========================================================================
# Overlay principal
# ===========================================================================

class Overlay(QWidget):
    def __init__(self, level_source: Callable[[], float]) -> None:
        super().__init__()
        self._level_source = level_source
        self._mode = "raw"
        self._tint = "neutral"     # neutral | amber | red | record
        self._pill_h = theme.HUD_HEIGHT
        self._pill_r = theme.HUD_RADIUS

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("OverlayRoot")

        self._content = QWidget(self)
        self._content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._row = QHBoxLayout(self._content)
        self._row.setContentsMargins(16, 0, 16, 0)
        self._row.setSpacing(11)

        self._chip = ModeChip("raw", self._content)
        self._wave = _HudWaveform(self._level_source, parent=self._content)
        self._dots = _BouncingDots(self._content)
        self._spin = _Spinner(self._content)
        self._check = _Badge("check", self._content)
        self._cross = _Badge("cross", self._content)
        self._errb = _Badge("error", self._content)
        self._warn = _Dot7(theme.palette().state(theme.WARNING), self._content)
        self._msg = QLabel(self._content)
        for w in (self._chip, self._wave, self._dots, self._spin,
                  self._check, self._cross, self._errb, self._warn, self._msg):
            w.hide()

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(180)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._swap = QPropertyAnimation(self, b"windowOpacity")
        self._swap.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._swap.finished.connect(self._on_swap_finished)
        self._pending_swap = None

        self._state = ""
        self._slow = QTimer(self)
        self._slow.setSingleShot(True)
        self._slow.setInterval(5000)
        self._slow.timeout.connect(self._on_processing_slow)

        self._auto_hide = QTimer(self)
        self._auto_hide.setSingleShot(True)
        self._auto_hide.timeout.connect(self._fade_out)
        # hide agendado pelo fade-out; timer próprio pra poder ser cancelado
        # quando um novo estado chega no meio do sumiço
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self._anchor_cx: int | None = None
        self._anchor_bottom = 0
        self._minimal = False  # legado: gravação agora usa pílula cheia

    # ------------------------------------------------------------------ infra

    def _all_anims(self) -> tuple:
        return (self._wave, self._dots, self._spin)

    def _stop_anims(self) -> None:
        for a in self._all_anims():
            a.stop()
        self._slow.stop()

    def _clear_row(self) -> None:
        while self._row.count():
            item = self._row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()

    def _apply(self, items, **kw) -> None:
        """Troca de estado com crossfade curto (evita pulo seco de tamanho)."""
        if self.isVisible() and self.windowOpacity() > 0.5:
            self._pending_swap = lambda: self._apply_now(items, **kw)
            running_out = (
                self._swap.state() == QPropertyAnimation.State.Running
                and self._swap.endValue() == 0.0
            )
            if not running_out:
                self._swap.stop()
                self._swap.setDuration(70)
                self._swap.setStartValue(self.windowOpacity())
                self._swap.setEndValue(0.0)
                self._swap.start()
        else:
            self._apply_now(items, **kw)

    def _on_swap_finished(self) -> None:
        if self._swap.endValue() != 0.0:
            return
        fn, self._pending_swap = self._pending_swap, None
        if fn is not None:
            fn()
        self._swap.setDuration(100)
        self._swap.setStartValue(0.0)
        self._swap.setEndValue(1.0)
        self._swap.start()

    def _apply_now(self, items, *, pad_h: int, gap: int,
                   tint: str = "neutral", height: int = theme.HUD_HEIGHT,
                   radius: int = theme.HUD_RADIUS,
                   pad_l: int | None = None, pad_r: int | None = None,
                   minimal: bool = False) -> None:
        self._clear_row()
        self._minimal = minimal
        self._tint = tint
        self._pill_h = height
        self._pill_r = radius
        pl = pad_l if pad_l is not None else pad_h
        pr = pad_r if pad_r is not None else pad_h
        self._row.setContentsMargins(pl, 0, pr, 0)
        self._row.setSpacing(gap)
        for w in items:
            self._row.addWidget(w, 0, Qt.AlignmentFlag.AlignVCenter)
            w.show()

        self._content.adjustSize()
        cw = min(self._content.sizeHint().width(), _MAX_TEXT_W + 2 * pad_h + 48)
        self.setFixedSize(cw + 2 * _M, height + 2 * _M)
        self._content.setGeometry(_M, _M, cw, height)
        self._reposition()
        self.update()

    def _target_screen(self):
        """Tela da janela EM FOCO — multi-monitor. Fallback: cursor → primária."""
        from PySide6.QtCore import QPoint
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                rect = wintypes.RECT()
                if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    s = QGuiApplication.screenAt(QPoint(cx, cy))
                    if s is not None:
                        return s
        except Exception:  # noqa: BLE001
            pass
        return (QGuiApplication.screenAt(QCursor.pos())
                or QGuiApplication.primaryScreen())

    def _reposition(self) -> None:
        if not self.isVisible() or self._anchor_cx is None:
            screen = self._target_screen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            self._anchor_cx = geo.center().x()
            self._anchor_bottom = geo.bottom() - theme.HUD_BOTTOM_MARGIN
        x = self._anchor_cx - self.width() // 2
        y = self._anchor_bottom - self.height()
        self.move(x, y)

    def _show_pill(self) -> None:
        # novo ciclo: solta âncora pra recentrar na tela em foco
        self._anchor_cx = None
        # não para o _auto_hide: show_done/show_error já o agendaram antes de
        # chegar aqui (quem cancela sumiços pendentes é _keep_visible)
        self._swap.stop()
        self._pending_swap = None
        self.setWindowOpacity(0.0)
        self.show()
        self._reposition()
        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def _txt(self, label: QLabel, text: str, color: str,
             weight: int = theme.W_MEDIUM, size: int = 13,
             mono: bool = False) -> None:
        label.setText(text)
        label.setFont(theme.qfont(size, weight, mono=mono))
        label.setStyleSheet(f"color: {color}; background: transparent;")
        label.adjustSize()

    # --------------------------------------------------------------- estados

    def show_recording(self, mode: str) -> None:
        """Só a onda; o chip aparece quando o modo não é o padrão."""
        self._keep_visible()
        self._mode = mode
        self._state = "recording"
        self._stop_anims()
        items: list = []
        if mode and mode != "raw":
            self._chip.set_mode(mode)
            items.append(self._chip)
        items.append(self._wave)
        self._apply(items, pad_h=18, gap=10, pad_l=14 if items[0] is self._chip else 18)
        self._wave.start()
        if not self.isVisible():
            self._show_pill()

    def show_transcribing(self, mode: str | None = None) -> None:
        self._keep_visible()
        self._state = "transcribing"
        self._stop_anims()
        items: list = []
        if mode and mode != "raw":
            self._chip.set_mode(mode)
            items.append(self._chip)
        items.append(self._dots)
        self._apply(items, pad_h=18, gap=10, pad_l=14 if items[0] is self._chip else 18)
        self._dots.start()
        if not self.isVisible():
            self._show_pill()

    def show_processing(self, mode: str) -> None:
        self._keep_visible()
        self._state = "processing"
        self._stop_anims()
        self._chip.set_mode(mode)
        self._txt(self._msg, "Refinando…", theme.palette().text_secondary)
        self._apply([self._spin, self._chip, self._msg], pad_h=16, gap=10)
        self._spin.start()
        self._slow.start()
        if not self.isVisible():
            self._show_pill()

    def _on_processing_slow(self) -> None:
        if self._state != "processing":
            return
        self._txt(self._msg, "Carregando a IA…",
                  theme.palette().text_secondary)
        self._apply_now([self._spin, self._chip, self._msg], pad_h=16, gap=10)

    def show_pasted(self, text: str) -> None:
        self.show_done(ok=True)

    def show_done(self, ok: bool = True, message: str | None = None,
                  mode: str | None = None) -> None:
        self._keep_visible()
        self._state = "done"
        self._stop_anims()
        if ok:
            self._txt(self._msg, message or "Colado",
                      theme.palette().text_primary, weight=theme.W_SEMIBOLD)
            items: list = [self._check, self._msg]
            if mode and mode != "raw":
                self._chip.set_mode(mode)
                items.append(self._chip)
            self._apply(items, pad_h=18, gap=10, pad_l=14, pad_r=18)
            self._auto_hide.start(1100 if mode and mode != "raw" else 900)
        else:
            color = "#F4D58A" if theme.is_dark() else "#8A6D1A"
            self._txt(self._msg, message or "Não captei nada", color)
            self._apply([self._warn, self._msg], pad_h=16, gap=10, tint="amber")
            self._auto_hide.start(1400)
        if not self.isVisible():
            self._show_pill()

    def show_pasted_no_ai(self, why: str = "Ollama offline") -> None:
        self._keep_visible()
        self._state = "no_ai"
        self._stop_anims()
        color = "#F4D58A" if theme.is_dark() else "#8A6D1A"
        self._txt(self._msg, f"Colado sem IA · {why}", color)
        self._apply([self._warn, self._msg], pad_h=16, gap=10, tint="amber")
        if not self.isVisible():
            self._show_pill()
        self._auto_hide.start(2600)

    def show_cancelled(self) -> None:
        self._keep_visible()
        self._state = "cancelled"
        self._stop_anims()
        self._txt(self._msg, "Cancelado", theme.palette().text_secondary)
        self._apply([self._cross, self._msg], pad_h=18, gap=10, pad_l=14, pad_r=18)
        if not self.isVisible():
            self._show_pill()
        self._auto_hide.start(800)

    def show_error(self, message: str) -> None:
        self._keep_visible()
        self._state = "error"
        self._stop_anims()
        color = theme.palette().state_text(theme.ERROR)
        text = message or "Erro · tente de novo"
        text = text[:1].upper() + text[1:]  # mensagens do app vêm em minúsculas
        self._txt(self._msg, text, color)
        self._apply([self._errb, self._msg], pad_h=16, gap=10, tint="red")
        if not self.isVisible():
            self._show_pill()
        self._auto_hide.start(1900)

    def show_loading_model(self) -> None:
        self._keep_visible()
        self._state = "loading"
        self._stop_anims()
        self._txt(self._msg, "Carregando o modelo…", theme.palette().text_secondary)
        self._apply([self._spin, self._msg], pad_h=16, gap=11)
        self._spin.start()
        if not self.isVisible():
            self._show_pill()

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._chip.set_mode(mode)

    # ------------------------------------------------------------------- fade

    def _fade_out(self) -> None:
        self._stop_anims()
        self._swap.stop()
        self._pending_swap = None
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()
        self._hide_timer.start(self._fade.duration() + 20)

    def _keep_visible(self) -> None:
        """Cancela um sumiço pendente antes de mostrar um novo estado.

        Sem isso, gravar logo depois de "Colado" deixava o auto-hide (ou o
        fade-out já em andamento) esconder a pílula no meio da gravação.
        """
        self._auto_hide.stop()
        if self._hide_timer.isActive():
            self._hide_timer.stop()
            self._fade.stop()
            self.setWindowOpacity(1.0)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._stop_anims()
        self._anchor_cx = None  # próximo ciclo recentra
        super().hideEvent(event)

    # ------------------------------------------------------------------ paint

    def _pill_fill_border(self) -> tuple[QColor, QColor]:
        pal = theme.palette()
        dark = pal.is_dark
        if self._tint == "amber":
            if dark:
                return QColor(40, 33, 18, 230), QColor(251, 191, 36, 90)
            return QColor(250, 243, 224, 245), QColor(245, 166, 35, 120)
        if self._tint == "red":
            if dark:
                return QColor(42, 20, 20, 230), QColor(255, 69, 58, 95)
            return QColor(251, 228, 226, 245), QColor(255, 59, 48, 120)
        # neutro
        if dark:
            return QColor(14, 14, 18, 246), theme.qcolor("rgba(255,255,255,0.09)")
        return QColor(255, 255, 255, 248), theme.qcolor("rgba(0,0,0,0.07)")

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        if self._minimal:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(self._pill_r)
        pill = QRectF(_M, _M, self.width() - 2 * _M, self.height() - 2 * _M)

        dark = theme.is_dark()

        # ---- sombra suave ----
        # camadas finas com queda quadrática: somadas viram um desfoque sem
        # borda visível. Cabe inteira na margem, então nada é cortado.
        spread = _M - 3
        total = 0.34 if dark else 0.13
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(spread, 0, -1):
            outer = 1.0 - (i - 1) / spread
            inner = 1.0 - i / spread
            c = QColor(0, 0, 0)
            c.setAlphaF(total * (outer * outer - inner * inner))
            p.setBrush(c)
            grow = float(i)
            p.drawRoundedRect(pill.adjusted(-grow, -grow + 2, grow, grow + 2),
                              r + grow, r + grow)

        # ---- corpo da pílula ----
        fill, border = self._pill_fill_border()
        p.setBrush(fill)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(pill, r, r)

        pen = QPen(border)
        pen.setWidthF(1.0)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(pill.adjusted(0.5, 0.5, -0.5, -0.5), r, r)
