"""Primeiro uso (tela 09) — checklist de pré-requisitos.

Reframe (decisão de escopo #3): estados mistos em vez de duas barras iguais.
GPU (detecção) · Whisper (download) · Ollama (instalação) ·
Qwen (pull opcional). "Continuar" libera assim que o Whisper terminar — o LLM
é opcional.
"""
from __future__ import annotations

import threading
import webbrowser

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from sussurro import setup_check
from sussurro.storage.config import Config
from sussurro.ui import components as kit
from sussurro.ui import theme
from sussurro.ui.components.window_frame import FramelessWindow


class _Check(QWidget):
    """Badge 18px: check verde, ou spinner/cinza conforme estado."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self._state = "wait"   # wait | ok | warn

    def set_state(self, s: str) -> None:
        self._state = s
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        pal = theme.palette()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = QRectF(0, 0, 18, 18)
        if self._state == "ok":
            p.setBrush(theme.qcolor(pal.state(theme.READY)))
            p.drawEllipse(r)
            from PySide6.QtCore import QPointF
            pen = QPen(theme.qcolor("#0E0F12" if pal.is_dark else "#FFFFFF"))
            pen.setWidthF(2); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawPolyline([QPointF(5, 9), QPointF(8, 12), QPointF(13, 6)])
        elif self._state == "warn":
            p.setBrush(theme.qcolor(theme.rgba(pal.state(theme.WARNING), 0.18)))
            p.drawEllipse(r)
            p.setFont(theme.qfont(12, theme.W_SEMIBOLD))
            p.setPen(theme.qcolor(pal.state(theme.WARNING)))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "!")
        else:
            p.setBrush(theme.qcolor(pal.inset))
            p.drawEllipse(r)


class SetupWindow(FramelessWindow):
    done = Signal()
    _ollama_start_finished = Signal(bool)  # resultado de try_start (thread)

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(width=440, parent=parent)
        self._cfg = config
        self._whisper_ready = False
        self._ollama_start_finished.connect(self._on_ollama_start_finished)
        self._dl_worker = None
        self._pull_worker = None
        self._build()
        QTimer.singleShot(60, self._detect)

    # ----------------------------------------------------------------- build

    def _build(self) -> None:
        pal = theme.palette()
        wrap = QVBoxLayout()
        wrap.setContentsMargins(26, 26, 26, 22)
        wrap.setSpacing(0)
        self.body.addLayout(wrap, 1)

        head = QHBoxLayout(); head.setSpacing(13)
        head.addWidget(kit.BrandMark(46), 0, Qt.AlignmentFlag.AlignVCenter)
        hc = QVBoxLayout(); hc.setSpacing(2)
        t = QLabel("Preparando o Sussurro")
        t.setFont(theme.qfont(18, theme.W_SEMIBOLD, tracking=theme.TRACK_TITLE))
        t.setStyleSheet(f"color: {pal.text_primary};")
        hc.addWidget(t)
        s = QLabel("Configurando o que roda local. Só desta vez.")
        s.setFont(theme.qfont(13))
        s.setStyleSheet(f"color: {pal.text_secondary};")
        hc.addWidget(s)
        head.addLayout(hc); head.addStretch(1)
        wrap.addLayout(head)
        wrap.addSpacing(18)

        # GPU
        self._gpu_box, self._gpu_check, self._gpu_val = self._gpu_row()
        wrap.addWidget(self._gpu_box)
        wrap.addSpacing(14)

        # Whisper
        (self._wh_card, self._wh_status, self._wh_bar, self._wh_btn) = self._dl_card(
            f"Whisper {self._cfg.model_size}", with_button=True)
        self._wh_btn.setText("Tentar de novo")
        self._wh_btn.clicked.connect(self._start_whisper_download)
        wrap.addWidget(self._wh_card)
        wrap.addSpacing(10)

        # Ollama
        self._ol_card = self._ollama_row()
        wrap.addWidget(self._ol_card)
        wrap.addSpacing(10)

        # Qwen
        (self._qw_card, self._qw_status, self._qw_bar, self._qw_btn) = \
            self._dl_card("Qwen 2.5 · 7B", with_button=True)
        # conectado uma vez só: _setup_qwen roda a cada atualização do Ollama
        self._qw_btn.clicked.connect(self._pull_qwen)
        wrap.addWidget(self._qw_card)
        wrap.addSpacing(20)

        foot = QHBoxLayout()
        later = kit.GhostButton("instalar IA depois")
        later.clicked.connect(self._continue)
        foot.addWidget(later)
        foot.addStretch(1)
        self._continue_btn = kit.PrimaryButton("Continuar")
        self._continue_btn.setEnabled(False)
        self._continue_btn.clicked.connect(self._continue)
        foot.addWidget(self._continue_btn)
        wrap.addLayout(foot)

    def _gpu_row(self):
        pal = theme.palette()
        box = QWidget()
        box.setObjectName("GpuBox")
        box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        green = pal.state(theme.READY)
        box.setStyleSheet(
            f"QWidget#GpuBox {{ background: {theme.rgba(green, 0.07)}; "
            f"border: 1px solid {theme.rgba(green, 0.20)}; border-radius: 11px; }}")
        lay = QHBoxLayout(box); lay.setContentsMargins(14, 12, 14, 12); lay.setSpacing(10)
        chk = _Check(); chk.set_state("wait")
        lay.addWidget(chk, 0, Qt.AlignmentFlag.AlignVCenter)
        lbl = QLabel("Detectando GPU…")
        lbl.setFont(theme.qfont(13, theme.W_MEDIUM))
        lbl.setStyleSheet(f"color: {pal.text_body_card}; background: transparent;")
        lay.addWidget(lbl); lay.addStretch(1)
        val = QLabel("")
        val.setFont(theme.qfont(12, theme.W_MEDIUM, mono=True))
        val.setStyleSheet(f"color: {green}; background: transparent;")
        lay.addWidget(val)
        box._label = lbl  # type: ignore[attr-defined]
        return box, chk, val

    def _dl_card(self, name: str, with_button: bool = False):
        pal = theme.palette()
        card = QWidget()
        card.setObjectName("DlCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(
            f"QWidget#DlCard {{ background: {pal.surface}; "
            f"border: 1px solid {pal.border_subtle}; border-radius: 11px; }}")
        lay = QVBoxLayout(card); lay.setContentsMargins(14, 13, 14, 13); lay.setSpacing(9)
        top = QHBoxLayout()
        nm = QLabel(name)
        nm.setFont(theme.qfont(13, theme.W_MEDIUM))
        nm.setStyleSheet(f"color: {pal.text_primary}; background: transparent;")
        top.addWidget(nm); top.addStretch(1)
        status = QLabel("")
        status.setFont(theme.qfont(11.5, theme.W_MEDIUM, mono=True))
        status.setStyleSheet(f"color: {pal.text_secondary}; background: transparent;")
        top.addWidget(status)
        btn = None
        if with_button:
            btn = kit.SecondaryButton("Baixar")
            btn.setVisible(False)
            top.addWidget(btn)
        lay.addLayout(top)
        bar = kit.ProgressBar(0.0)
        lay.addWidget(bar)
        return card, status, bar, btn

    def _ollama_row(self):
        pal = theme.palette()
        card = QWidget()
        card.setObjectName("OlCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(
            f"QWidget#OlCard {{ background: {pal.surface}; "
            f"border: 1px solid {pal.border_subtle}; border-radius: 11px; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(10)
        self._ol_check = _Check()
        self._ol_check.set_state("wait")
        top.addWidget(self._ol_check, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ol_label = QLabel("Verificando Ollama…")
        self._ol_label.setFont(theme.qfont(13, theme.W_MEDIUM))
        self._ol_label.setStyleSheet(
            f"color: {pal.text_primary}; background: transparent;")
        top.addWidget(self._ol_label)
        top.addStretch(1)
        self._ol_note = QLabel("")
        self._ol_note.setFont(theme.qfont(11.5))
        self._ol_note.setStyleSheet(
            f"color: {pal.text_tertiary}; background: transparent;")
        top.addWidget(self._ol_note)

        self._ol_btn = kit.SecondaryButton("Instalar Automaticamente")
        self._ol_btn.setVisible(False)
        # a ação do botão muda com o estado (instalar, iniciar, abrir o site)
        self._ol_action = self._install_ollama
        self._ol_btn.clicked.connect(lambda: self._ol_action())
        top.addWidget(self._ol_btn)

        lay.addLayout(top)
        self._ol_bar = kit.ProgressBar(0.0)
        self._ol_bar.setVisible(False)
        lay.addWidget(self._ol_bar)
        return card

    # --------------------------------------------------------------- detecção

    def _detect(self) -> None:
        gpu = setup_check.detect_gpu()
        if gpu is not None:
            name, gb = gpu
            self._gpu_check.set_state("ok")
            self._gpu_box._label.setText("GPU detectada")  # type: ignore[attr-defined]
            self._gpu_val.setText(f"{name} · {gb} GB (Aceleração CUDA)")
        else:
            self._gpu_check.set_state("ok")
            self._gpu_box._label.setText("Modo CPU")  # type: ignore[attr-defined]
            self._gpu_val.setText("Whisper Turbo INT8 (Execução local)")

        # Whisper
        if setup_check.whisper_cached(self._cfg.model_size):
            self._whisper_done()
        else:
            self._start_whisper_download()

        self._refresh_ollama()

    def _start_whisper_download(self) -> None:
        self._wh_btn.setVisible(False)
        self._wh_bar.set_value(0.0)
        self._wh_status.setText("baixando…")
        self._dl_worker = setup_check.WhisperDownloadWorker(self._cfg.model_size)
        self._dl_worker.progress.connect(self._on_wh_progress)
        self._dl_worker.finished_ok.connect(self._whisper_done)
        self._dl_worker.failed.connect(self._on_wh_failed)
        self._dl_worker.start()

    def _on_wh_progress(self, done_gb: float, total_gb: float, mbps: float) -> None:
        self._wh_bar.set_value(done_gb / total_gb if total_gb else 0)
        self._wh_status.setText(f"{done_gb:.1f} / {total_gb:.1f} GB · {mbps:.0f} MB/s")

    def _whisper_done(self) -> None:
        self._whisper_ready = True
        self._wh_bar.set_value(1.0)
        self._wh_status.setText("pronto")
        self._continue_btn.setEnabled(True)

    def _on_wh_failed(self, err: str) -> None:
        self._wh_status.setText("falhou · confira a internet")
        self._wh_btn.setVisible(True)

    def _refresh_ollama(self) -> None:
        running = setup_check.ollama_running()
        installed = running or setup_check.ollama_installed()
        if running:
            self._ol_check.set_state("ok")
            self._ol_label.setText("Ollama rodando")
            self._ol_note.setText("")
            self._ol_btn.setVisible(False)
            self._ol_bar.setVisible(False)
            self._setup_qwen(enabled=True)
        elif installed:
            self._ol_check.set_state("warn")
            self._ol_label.setText("Ollama instalado")
            self._ol_note.setText("não está em execução")
            self._ol_action = self._start_ollama
            self._ol_btn.setText("Iniciar Ollama")
            self._ol_btn.setEnabled(True)
            self._ol_btn.setVisible(True)
            self._ol_bar.setVisible(False)
            self._setup_qwen(enabled=False)
        else:
            self._ol_check.set_state("wait")
            self._ol_label.setText("Ollama")
            self._ol_note.setText("opcional para IA")
            self._ol_action = self._install_ollama
            self._ol_btn.setText("Instalar Automaticamente")
            self._ol_btn.setEnabled(True)
            self._ol_btn.setVisible(True)
            self._ol_bar.setVisible(False)
            self._setup_qwen(enabled=False)

    def _start_ollama(self) -> None:
        self._ol_btn.setEnabled(False)
        self._ol_note.setText("iniciando…")

        def _run() -> None:
            try:
                ok = setup_check.ollama_client.try_start()
            except Exception:  # noqa: BLE001
                ok = False
            self._ollama_start_finished.emit(ok)

        threading.Thread(target=_run, daemon=True, name="ollama-start").start()

    def _on_ollama_start_finished(self, ok: bool) -> None:
        self._refresh_ollama()
        if not ok:
            self._ol_note.setText("não iniciou · abra o Ollama pelo menu Iniciar")

    def _install_ollama(self) -> None:
        self._ol_btn.setVisible(False)
        self._ol_bar.setVisible(True)
        self._ol_bar.set_value(0.0)
        self._ol_worker = setup_check.OllamaInstallWorker()
        self._ol_worker.progress.connect(
            lambda done, total, speed: (
                self._ol_bar.set_value(done / total if total else 0.0),
                self._ol_note.setText(f"{done:.1f}/{total:.1f} MB ({speed:.1f} MB/s)"),
            )
        )
        self._ol_worker.status_changed.connect(
            lambda msg: self._ol_label.setText(msg)
        )
        self._ol_worker.finished_ok.connect(self._refresh_ollama)
        self._ol_worker.failed.connect(self._on_ol_failed)
        self._ol_worker.start()

    def _on_ol_failed(self, error: str) -> None:
        self._ol_check.set_state("warn")
        self._ol_label.setText("Falha no setup do Ollama")
        self._ol_note.setText(error[:60])
        self._ol_bar.setVisible(False)
        self._ol_action = lambda: webbrowser.open("https://ollama.com/download")
        self._ol_btn.setText("Baixar Manualmente")
        self._ol_btn.setEnabled(True)
        self._ol_btn.setVisible(True)

    def _setup_qwen(self, enabled: bool) -> None:
        if enabled and setup_check.qwen_pulled():
            self._qw_status.setText("pronto")
            self._qw_bar.set_value(1.0)
            self._qw_btn.setVisible(False)
        elif enabled:
            self._qw_status.setText("~4.7 GB")
            self._qw_bar.set_value(0.0)
            self._qw_btn.setText("Baixar")
            self._qw_btn.setVisible(True)
        else:
            self._qw_status.setText("aguardando Ollama")
            self._qw_bar.set_value(0.0)
            self._qw_btn.setVisible(False)

    def _pull_qwen(self) -> None:
        self._qw_btn.setVisible(False)
        self._qw_status.setText("baixando…")
        self._pull_worker = setup_check.QwenPullWorker()
        self._pull_worker.progress.connect(
            lambda d, t: (self._qw_bar.set_value(d / t if t else 0),
                          self._qw_status.setText(f"{d:.1f} / {t:.1f} GB")))
        self._pull_worker.finished_ok.connect(
            lambda: (self._qw_bar.set_value(1.0), self._qw_status.setText("pronto")))
        self._pull_worker.failed.connect(self._on_qwen_failed)
        self._pull_worker.start()

    def _on_qwen_failed(self, message: str) -> None:
        self._qw_status.setText(f"falhou · {message}"[:60])
        self._qw_btn.setText("Tentar de novo")
        self._qw_btn.setVisible(True)

    def _continue(self) -> None:
        self.done.emit()
        self.hide()

    def stop_workers(self) -> None:
        """Cancela e encerra os workers de download (close + shutdown)."""
        workers = [
            getattr(self, "_dl_worker", None),
            getattr(self, "_pull_worker", None),
            getattr(self, "_ol_worker", None),
        ]
        for w in workers:
            if w is not None and w.isRunning():
                w.cancel()
                w.quit()
                w.wait(2000)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_workers()
        super().closeEvent(event)
