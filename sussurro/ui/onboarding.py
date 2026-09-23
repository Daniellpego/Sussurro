"""Onboarding (tela 03) — wizard de 3 passos. Card centralizado ~372px.

1. Welcome (brand 70 + tagline + Começar + pular)
2. Teste de microfone — medidor de nível AO VIVO (lê o mic de verdade) + seletor
3. Atalho (keycaps Ctrl+Win + aviso âmbar)
"""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sussurro.audio.capture import Recorder, list_input_devices
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components.window_frame import FramelessWindow


class _ProgressDots(QWidget):
    def __init__(self, total: int = 3, parent=None) -> None:
        super().__init__(parent)
        self._total = total
        self._current = 0
        self.setFixedHeight(6)
        self.setMinimumWidth(total * 12)

    def set_current(self, idx: int) -> None:
        self._current = idx
        self.update()

    def sizeHint(self):  # noqa: N802
        from PySide6.QtCore import QSize
        w = (self._total - 1) * 6 + 18 + (self._total - 1) * 6
        return QSize(w, 6)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        inactive = theme.qcolor(theme.onb_dot_off())
        # calcula largura total e centraliza
        widths = [18 if i == self._current else 6 for i in range(self._total)]
        total_w = sum(widths) + 6 * (self._total - 1)
        x = (self.width() - total_w) / 2
        for i in range(self._total):
            w = widths[i]
            if i == self._current:
                g = QLinearGradient(x, 0, x + w, 6)
                g.setColorAt(0, theme.qcolor(theme.GRAD_A))
                g.setColorAt(1, theme.qcolor(theme.GRAD_B))
                p.setBrush(g)
            else:
                p.setBrush(inactive)
            p.drawRoundedRect(QRectF(x, 0, w, 6), 3, 3)
            x += w + 6


class _LevelMeter(QWidget):
    """11 barras com nível AO VIVO do microfone (VU scrolling)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._n = 11
        self._bw = 3.0
        self._gap = 3.0
        self.setFixedSize(int(self._n * self._bw + (self._n - 1) * self._gap), 64)
        self._recorder: Recorder | None = None
        self._device = None
        self._t0 = time.monotonic()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)

    def start(self, device=None) -> None:
        self._device = device
        self._stop_recorder()
        try:
            self._recorder = Recorder(device=device)
            self._recorder.start()
        except Exception:  # noqa: BLE001
            self._recorder = None
        self._t0 = time.monotonic()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._stop_recorder()

    def _stop_recorder(self) -> None:
        if self._recorder is not None:
            try:
                self._recorder.stop()
            except Exception:  # noqa: BLE001
                pass
            self._recorder = None

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        h = self.height()
        cy = h / 2

        if self._recorder is not None:
            levels = self._recorder.recent_levels(self._n)
        else:
            t = time.monotonic() - self._t0
            levels = [0.25 + 0.2 * (0.5 - 0.5 * math.cos(
                2 * math.pi * ((t - i * 0.08) % 1.0))) for i in range(self._n)]

        x = 0.0
        for lvl in levels:
            bar_h = 6 + max(0.0, min(1.0, lvl)) * (h - 10)
            g = QLinearGradient(0, cy - bar_h / 2, 0, cy + bar_h / 2)
            g.setColorAt(0, theme.qcolor(theme.GRAD_A))
            g.setColorAt(1, theme.qcolor(theme.GRAD_B))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x, cy - bar_h / 2, self._bw, bar_h), 1.5, 1.5)
            x += self._bw + self._gap


class OnboardingWizard(FramelessWindow):
    finished_setup = Signal(dict)   # {mic_device: str|None, skipped: bool}

    def __init__(self, parent=None) -> None:
        super().__init__(width=372, dialog=True, parent=parent)
        self._index = 0
        self._mic_device = None
        self._build()

    def _build(self) -> None:
        wrap = QVBoxLayout()
        wrap.setContentsMargins(28, 26, 28, 24)
        wrap.setSpacing(0)
        self.body.addLayout(wrap, 1)

        self._dots = _ProgressDots(3)
        wrap.addWidget(self._dots)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._step_welcome())
        self._stack.addWidget(self._step_mic())
        self._stack.addWidget(self._step_shortcut())
        self._stack.setMinimumHeight(360)
        wrap.addWidget(self._stack, 1)

        self._root.setMinimumHeight(466)
        self._stack.currentChanged.connect(self._on_step)

    # --- steps ---

    def _step_welcome(self) -> QWidget:
        pal = theme.palette()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)
        lay.addStretch(1)
        lay.addWidget(kit.BrandMark(70), 0, Qt.AlignmentFlag.AlignHCenter)
        title = QLabel("Sussurro")
        title.setFont(theme.qfont(25, theme.W_SEMIBOLD, tracking=theme.TRACK_DISPLAY))
        title.setStyleSheet(f"color: {pal.text_primary};")
        lay.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        sub = QLabel("Fale e cole em qualquer app.\n100% local, no seu computador.")
        sub.setFont(theme.qfont(14))
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub.setStyleSheet(f"color: {pal.text_secondary};")
        lay.addWidget(sub, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        btn = self._primary("Começar")
        btn.clicked.connect(self._next)
        lay.addWidget(btn)
        skip = kit.GhostButton("pular configuração")
        skip.clicked.connect(self._skip)
        lay.addWidget(skip, 0, Qt.AlignmentFlag.AlignHCenter)
        return w

    def _step_mic(self) -> QWidget:
        pal = theme.palette()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addSpacing(30)
        title = QLabel("Teste seu microfone")
        title.setFont(theme.qfont(19, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        title.setStyleSheet(f"color: {pal.text_primary};")
        lay.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(7)
        sub = QLabel("Fale algo e veja se as barras se mexem.")
        sub.setFont(theme.qfont(13.5))
        sub.setStyleSheet(f"color: {pal.text_secondary};")
        lay.addWidget(sub, 0, Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(26)
        self._meter = _LevelMeter()
        lay.addWidget(self._meter, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(26)

        card = kit.GroupCard()
        self._mic_row = kit.ValueRow("Microfone", self._mic_label())
        self._mic_row.clicked.connect(self._pick_mic)
        card.add_row(self._mic_row)
        lay.addWidget(card)
        lay.addStretch(1)

        btn = self._primary("Continuar")
        btn.clicked.connect(self._next)
        lay.addWidget(btn)
        return w

    def _step_shortcut(self) -> QWidget:
        pal = theme.palette()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addSpacing(30)
        title = QLabel("Seu atalho")
        title.setFont(theme.qfont(19, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        title.setStyleSheet(f"color: {pal.text_primary};")
        lay.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(7)
        sub = QLabel("Segure para falar e solte para colar.")
        sub.setFont(theme.qfont(13.5))
        sub.setStyleSheet(f"color: {pal.text_secondary};")
        lay.addWidget(sub, 0, Qt.AlignmentFlag.AlignHCenter)

        lay.addStretch(1)
        keys = QHBoxLayout()
        keys.setSpacing(12)
        keys.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        keys.addWidget(kit.Keycap("Ctrl", large=True))
        plus = QLabel("+")
        plus.setFont(theme.qfont(18))
        plus.setStyleSheet(f"color: {pal.text_tertiary};")
        keys.addWidget(plus)
        keys.addWidget(kit.Keycap("Win", large=True))
        kw = QWidget(); kw.setLayout(keys)
        lay.addWidget(kw, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)

        tip = QLabel("Para cancelar, aperte qualquer outra tecla enquanto segura.")
        tip.setFont(theme.qfont(12.5))
        tip.setStyleSheet(f"color: {pal.text_tertiary};")
        tip.setWordWrap(True)
        tip.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(tip)

        lay.addSpacing(20)
        btn = self._primary("Concluir")
        btn.clicked.connect(self._finish)
        lay.addWidget(btn)
        return w

    # --- helpers ---

    def _primary(self, text: str) -> kit.PrimaryButton:
        from PySide6.QtWidgets import QSizePolicy
        btn = kit.PrimaryButton(text)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return btn

    def _mic_label(self) -> str:
        return self._mic_device or "Padrão do sistema"

    def _pick_mic(self) -> None:
        pal = theme.palette()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
        QMenu {{ background: {pal.surface}; border: 1px solid {pal.border_strong};
            border-radius: 10px; padding: 6px; color: {pal.text_primary}; font-size: 13px; }}
        QMenu::item {{ padding: 7px 26px 7px 12px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {pal.hover}; }}
        """)
        opts = [(None, "Padrão do sistema")]
        opts.extend((name, name) for name in list_input_devices())
        for val, label in opts:
            act = menu.addAction(label); act.setData(val)
        chosen = menu.exec(self._mic_row.mapToGlobal(QPoint(0, self._mic_row.height())))
        if chosen is not None:
            self._mic_device = chosen.data()
            self._mic_row.set_value(self._mic_label())
            self._meter.start(self._mic_device)  # reinicia com o novo mic

    def _on_step(self, idx: int) -> None:
        self._index = idx
        self._dots.set_current(idx)
        # liga/desliga o medidor de nível conforme entra/sai do passo do mic
        if idx == 1:
            self._meter.start(self._mic_device)
        else:
            if hasattr(self, "_meter"):
                self._meter.stop()

    def _next(self) -> None:
        if self._index < 2:
            self._stack.setCurrentIndex(self._index + 1)

    def _skip(self) -> None:
        self._meter_stop()
        self.finished_setup.emit({"mic_device": self._mic_device, "skipped": True})
        self.hide()

    def _finish(self) -> None:
        self._meter_stop()
        self.finished_setup.emit({"mic_device": self._mic_device, "skipped": False})
        self.hide()

    def _meter_stop(self) -> None:
        if hasattr(self, "_meter"):
            self._meter.stop()

    def hideEvent(self, event) -> None:  # noqa: N802
        self._meter_stop()
        super().hideEvent(event)
