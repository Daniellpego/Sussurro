"""Orquestrador: cola hotkey + recorder + ASR worker + overlay + paste
+ janela principal + tray.

Roda como app Qt persistente:
- Tray icon sempre visivel
- Janela principal aparece no primeiro boot, depois fica fechada-em-tray
- Push-to-talk continua funcionando com a janela escondida
- Transcricoes vao pro historico (persistido em %APPDATA%)
"""
from __future__ import annotations

import logging
import signal
import sys
import time

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from sussurro.asr.whisper import (
    TranscriptionJob,
    TranscriptionResult,
    WhisperWorker,
)
from sussurro.audio.capture import Recorder
from sussurro.hotkey.listener import PushToTalkListener
from sussurro.hotkey.mouse_listener import MouseButtonListener
from sussurro.inject.paste import PasteResult, paste_text
from sussurro.llm import modes as modes_mod
from sussurro.llm.modes import ModeStore
from sussurro.llm.worker import LLMJob, LLMResult, LLMWorker
from sussurro.storage.config import Config
from sussurro.storage.dictionary import Dictionary
from sussurro.storage.history import History, HistoryEntry
from sussurro.storage.paths import log_path
from sussurro.ui.onboarding import OnboardingWizard
from sussurro.ui.overlay import Overlay
from sussurro.ui.tray import Tray
from sussurro.ui.window import MainWindow

log = logging.getLogger("sussurro")


class App(QObject):
    # colagem roda em thread de fundo; sinal traz PasteResult pra UI
    _pasted = Signal(object, bool, str, object)  # asr, used_llm, reason, PasteResult

    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self._qt = qt_app
        self._cfg = Config.load()
        # efeito vidro (acrílico Win11) — definido antes de criar qualquer janela
        from sussurro.ui.components.window_frame import set_glass
        set_glass(self._cfg.glass)
        self._history = History()
        self._dictionary = Dictionary()  # vocabulário + seed + sugestões
        self._mode = self._cfg.default_mode
        self._request_seq = 0
        # Em espera = não gasta VRAM; Ativo = pode ditar (carrega sob demanda)
        self._paused = not self._cfg.start_armed
        self._hotkeys_started = False
        self._asr_note = ""  # aviso de fallback CPU etc.

        # backend
        self._recorder = Recorder(device=self._cfg.mic_device or None)
        self._overlay = Overlay(level_source=lambda: self._recorder.level)
        self._hotkey = PushToTalkListener()
        self._mouse_hotkey = MouseButtonListener(self._cfg.mouse_button)
        self._worker = WhisperWorker(
            model_size=self._cfg.model_size,
            device="cuda",
            compute_type=self._cfg.compute_type,
            language=self._cfg.language,
            quality_preset=self._cfg.quality_preset,
        )
        self._modes = ModeStore.load()
        modes_mod.set_active(self._modes)  # singleton p/ componentes resolverem
        # modo ativo precisa ser valido (pode ter sido deletado/desativado)
        self._mode = self._modes.fallback_id(self._cfg.default_mode)
        if self._mode != self._cfg.default_mode:
            self._cfg.default_mode = self._mode
            self._cfg.save()
        self._active_mode = self._mode  # modo efetivo da gravacao atual
        self._llm_worker = LLMWorker(
            store=self._modes,
            keep_alive=self._cfg.ollama_keep_alive,
            allow_autostart=True,  # sob demanda no 1º modo com IA
        )
        # estado de transcricoes pendentes (raw enquanto LLM processa)
        self._pending_raw: dict[int, TranscriptionResult] = {}

        # timer de ociosidade -> libera Whisper da VRAM (opt-in unload_idle)
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(10 * 60 * 1000)  # 10 min
        self._idle_timer.timeout.connect(self._on_idle)
        # Qwen solto mais cedo (2 min) — qualidade do texto idêntica no próximo
        # Clean; só paga reload. Não mexe no large-v3.
        self._llm_idle_timer = QTimer(self)
        self._llm_idle_timer.setSingleShot(True)
        self._llm_idle_timer.setInterval(2 * 60 * 1000)  # 2 min
        self._llm_idle_timer.timeout.connect(self._on_llm_idle)

        # UI (compartilha o ModeStore com o LLM worker)
        self._window = MainWindow(self._cfg, self._history,
                                   mode_store=self._modes)
        self._tray = Tray(self._modes, lambda: self._mode)
        self._settings = None  # janela de Ajustes (lazy)
        if self._paused:
            self._set_status("paused", "em espera · ative na bandeja")
        elif self._cfg.preload_asr:
            self._set_status("loading", "carregando modelo...")
        else:
            self._set_status("ready", f"ativo · {self._cfg.trigger_label}")

        self._wire_signals()

    # --- wiring ---

    def _wire_signals(self) -> None:
        # hotkey -> app
        self._hotkey.pressed.connect(
            self._on_pressed, Qt.ConnectionType.QueuedConnection
        )
        self._hotkey.released.connect(
            self._on_released, Qt.ConnectionType.QueuedConnection
        )
        self._hotkey.cancelled.connect(
            self._on_cancelled, Qt.ConnectionType.QueuedConnection
        )

        # mouse hotkey -> mesmos handlers (os guards de estado em
        # _on_pressed/_on_released evitam disparo duplo)
        self._mouse_hotkey.pressed.connect(
            self._on_pressed, Qt.ConnectionType.QueuedConnection
        )
        self._mouse_hotkey.released.connect(
            self._on_released, Qt.ConnectionType.QueuedConnection
        )

        # worker -> app
        self._worker.ready.connect(self._on_worker_ready)
        self._worker.started_transcription.connect(self._on_started_inf)
        self._worker.done.connect(self._on_asr_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.reloading.connect(self._on_reloading)
        self._worker.recovered.connect(self._on_worker_recovered)
        self._worker.device_ready.connect(self._on_device_ready)
        self._pasted.connect(self._on_pasted)

        # LLM worker -> app
        self._llm_worker.started_processing.connect(self._on_llm_started)
        self._llm_worker.done.connect(self._on_llm_done)
        self._llm_worker.failed.connect(self._on_llm_failed)

        # tray
        self._tray.show_window_requested.connect(self._show_window)
        self._tray.history_requested.connect(self._show_history)
        self._tray.settings_requested.connect(self._show_settings)
        self._tray.mode_selected.connect(self._on_tray_mode)
        self._tray.pause_toggled.connect(self._on_pause_toggled)
        self._tray.quit_requested.connect(self._quit)

        # window
        self._window.close_to_tray.connect(self._on_close_to_tray)
        self._window.config_changed.connect(self._on_config_changed)
        self._window.settings_requested.connect(self._show_settings)

        # tema do sistema mudou (so reaplica se a preferencia for "system")
        hints = self._qt.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._on_system_scheme)

    # --- lifecycle ---

    def start(self) -> None:
        log.info(
            "startup (armed=%s ollama_boot=%s preload=%s keep_alive=%s)",
            not self._paused, self._cfg.ollama_autostart,
            self._cfg.preload_asr, self._cfg.ollama_keep_alive,
        )
        # Ollama no boot: SÓ se armado E o usuário pediu autostart.
        if (not self._paused) and self._cfg.ollama_autostart:
            self._ensure_ollama()
        self._llm_worker.start()  # thread vazia — não carrega Qwen sozinha
        self._tray.show()
        self._tray.set_paused(self._paused)

        if not self._cfg.first_run_done:
            # primeiro uso: onboarding; depois arma e carrega
            self._paused = False
            self._tray.set_paused(False)
            self._window.show()
            self._window.raise_()
            self._show_onboarding()
        else:
            if self._paused:
                # ESPERA: bandeja leve, zero Whisper/Qwen na VRAM
                self._set_status(
                    "paused", "em espera · ative na bandeja pra falar")
                self._tray.notify(
                    "Sussurro em espera",
                    "Quase não usa memória. Clique no ícone → Ativar Sussurro.",
                )
            else:
                self._arm_engine(notify=False)
            if not self._cfg.start_minimized:
                self._window.show()
                self._window.raise_()

    def _ensure_ollama(self) -> None:
        """Sobe o Ollama em background (opt-in via ollama_autostart)."""
        import threading

        def _run() -> None:
            from sussurro.llm import ollama as oc
            if oc.is_running():
                return
            if oc.try_start():
                log.info("ollama iniciado automaticamente (autostart ligado)")
            else:
                log.warning("ollama indisponível — modos com IA colarão raw")

        threading.Thread(target=_run, daemon=True,
                         name="ollama-autostart").start()

    def _ensure_asr_started(self) -> None:
        """Garante que o WhisperWorker está rodando (lazy se preload_asr=False)."""
        if not self._worker.isRunning():
            log.info("ASR lazy-start (primeiro uso)")
            self._set_status("loading", "carregando modelo...")
            if self._cfg.show_overlay:
                self._overlay.show_loading_model()
            self._worker.start()

    def _center_over_main(self, win, w: int, h: int) -> None:
        wp = self._window.geometry()
        win.move(wp.x() + (wp.width() - w) // 2, wp.y() + (wp.height() - h) // 2)

    def _show_onboarding(self) -> None:
        self._onboarding = OnboardingWizard(self._window)
        self._onboarding.finished_setup.connect(self._on_onboarding_done)
        self._onboarding.show()
        self._onboarding.raise_()
        self._center_over_main(self._onboarding, 372, 466)

    @Slot(dict)
    def _on_onboarding_done(self, choices: dict) -> None:
        mic = choices.get("mic_device")
        if mic:
            self._cfg.mic_device = mic
            self._cfg.save()
            self._recorder = Recorder(device=mic)
        log.info("onboarding concluido — mic=%s", mic or "default")
        self._show_setup()

    def _show_setup(self) -> None:
        from sussurro.ui.setup_ui import SetupWindow
        self._setup = SetupWindow(self._cfg, parent=self._window)
        self._setup.done.connect(self._on_setup_done)
        self._setup.show()
        self._setup.raise_()
        self._center_over_main(self._setup, 440, 440)

    @Slot()
    def _on_setup_done(self) -> None:
        self._cfg.first_run_done = True
        self._cfg.save()
        log.info("primeiro uso concluido — armando motor")
        self._paused = False
        self._tray.set_paused(False)
        self._arm_engine(notify=True)

    def shutdown(self) -> None:
        if getattr(self, "_shutdown_done", False):
            return
        self._shutdown_done = True
        log.info("shutdown")
        # cancela downloads do setup se estiverem rodando
        setup = getattr(self, "_setup", None)
        if setup is not None:
            try:
                setup.stop_workers()
            except Exception:  # noqa: BLE001
                pass
        try:
            self._hotkey.stop()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._mouse_hotkey.stop()
        except Exception:  # noqa: BLE001
            pass
        if self._worker.isRunning():
            self._worker.shutdown()
            self._worker.wait(3000)
        self._llm_worker.shutdown()
        self._llm_worker.wait(2000)
        if self._recorder.is_recording:
            self._recorder.stop()
        # solta Qwen da VRAM ao sair (não mata ollama.exe — só descarrega pesos)
        if self._cfg.ollama_unload_on_quit:
            import threading
            threading.Thread(target=self._unload_owned_llm_models, daemon=True,
                             name="ollama-quit-unload").start()
        self._tray.hide()

    # --- callbacks ---

    def _restart_idle(self) -> None:
        """(Re)arma timers de ociosidade (Whisper longo + Qwen curto)."""
        if self._paused or self._recorder.is_recording:
            self._idle_timer.stop()
            self._llm_idle_timer.stop()
            return
        if self._cfg.unload_idle:
            self._idle_timer.start()
        else:
            self._idle_timer.stop()
        # Qwen: solta cedo se smart_economy (não afeta qualidade do ASR)
        if self._cfg.smart_economy:
            self._llm_idle_timer.start()
        else:
            self._llm_idle_timer.stop()

    def _free_llm_vram(self, reason: str = "") -> None:
        """Descarrega só o Qwen/Ollama — zero impacto na qualidade do Whisper."""
        if not self._cfg.smart_economy and not self._cfg.ollama_unload_on_quit:
            return
        import threading

        from sussurro.llm import ollama as oc

        def _run() -> None:
            try:
                owned = self._owned_llm_models()
                loaded = set(oc.loaded_models())
                targets = sorted(owned & loaded)
                if not targets:
                    return
                log.info("soltando LLM do Sussurro da VRAM (%s): %s",
                         reason or "—", targets)
                oc.unload_models(targets)
            except Exception:  # noqa: BLE001
                log.debug("unload LLM falhou", exc_info=True)

        threading.Thread(target=_run, daemon=True, name="ollama-free").start()

    def _owned_llm_models(self) -> set[str]:
        """Tags de Ollama que o Sussurro pode ter carregado."""
        from sussurro.llm import ollama as oc
        from sussurro.llm.modes import DEFAULT_LLM_MODEL

        models = {oc.DEFAULT_MODEL}
        for mode in self._modes.all():
            if mode.model and mode.model != DEFAULT_LLM_MODEL:
                models.add(mode.model)
        return models

    def _unload_owned_llm_models(self) -> None:
        from sussurro.llm import ollama as oc
        oc.unload_models(self._owned_llm_models())

    @Slot()
    def _on_llm_idle(self) -> None:
        """2 min sem ditar → solta Qwen. Whisper fica (se preload/unload_idle)."""
        if self._paused or self._recorder.is_recording:
            return
        if self._cfg.smart_economy:
            self._free_llm_vram("idle-2min")

    @Slot()
    def _on_idle(self) -> None:
        if self._cfg.unload_idle and not self._recorder.is_recording and not self._paused:
            log.info("ocioso 10min -> liberando Whisper (+ LLM) da VRAM")
            if self._worker.isRunning():
                self._worker.request_unload()
            self._free_llm_vram("idle-10min")

    @Slot()
    def _on_reloading(self) -> None:
        log.info("recarregando modelo (aquecendo a GPU)")
        if self._cfg.show_overlay:
            self._overlay.show_loading_model()
        self._set_status("loading", "aquecendo a GPU...")

    def _start_hotkeys(self) -> None:
        if self._hotkeys_started:
            return
        self._hotkeys_started = True
        self._hotkey.start()
        self._mouse_hotkey.start()

    @Slot(str, str)
    def _on_device_ready(self, device: str, note: str) -> None:
        self._asr_note = note or ""
        if note:
            log.warning("ASR device=%s (%s)", device, note)
        else:
            log.info("ASR device=%s", device)

    @Slot()
    def _on_worker_ready(self) -> None:
        log.info("modelo carregado, ativando hotkey")
        self._start_hotkeys()
        self._restart_idle()
        if self._asr_note:
            status = f"pronto · {self._asr_note}"
            self._set_status("ready", status)
            self._tray.notify(
                "Sussurro pronto (modo limitado)",
                self._asr_note + f" · {self._cfg.trigger_label}",
            )
        else:
            self._set_status("ready", f"pronto · {self._cfg.trigger_label}")
            self._tray.notify(
                "Sussurro está pronto",
                f"Segure {self._cfg.trigger_label} pra falar.",
            )

    @Slot()
    def _on_worker_recovered(self) -> None:
        log.info("modelo recarregado com sucesso (recuperado)")

    def _resolve_mode(self) -> str:
        """Modo efetivo desta gravação: app-aware (se ligado) ou o default."""
        if self._cfg.auto_mode:
            from sussurro.foreground import foreground_app, mode_for_app
            m = mode_for_app(foreground_app())
            if m and self._modes.exists(m) and self._modes.get(m).active:
                return m
        return self._mode

    @Slot()
    def _on_pressed(self) -> None:
        if self._paused:
            return
        if self._recorder.is_recording:
            return
        # ASR lazy: se preload_asr=False, sobe o Whisper no 1º PTT
        self._ensure_asr_started()
        # modo automatico por app em foco (consciencia de contexto)
        self._active_mode = self._resolve_mode()
        log.info("PTT pressed: gravando (modo=%s)", self._active_mode)
        try:
            self._recorder.start()
        except Exception:  # noqa: BLE001 - mic indisponivel/removido/ocupado
            log.exception("falha ao abrir o microfone")
            if self._cfg.show_overlay:
                self._overlay.show_error("microfone indisponível")
            self._set_status("error", "microfone indisponível")
            return
        if self._cfg.show_overlay:
            self._overlay.show_recording(self._active_mode)
        from sussurro import sound
        sound.play("start", self._cfg.play_sound)
        self._set_status("recording", "ouvindo...")

    @Slot()
    def _on_released(self) -> None:
        if not self._recorder.is_recording:
            return
        log.info("PTT released: transcrevendo")
        audio = self._recorder.stop()
        if self._cfg.show_overlay:
            self._overlay.show_transcribing(self._active_mode)
        self._request_seq += 1
        self._worker.submit(TranscriptionJob(
            audio=audio,
            mode=self._active_mode,
            request_id=self._request_seq,
            # estilo PT-BR + termos; hotwords = bias nativo do CTranslate2
            initial_prompt=self._dictionary.to_prompt(),
            hotwords=self._dictionary.to_hotwords(),
        ))
        self._restart_idle()  # rearma o timer de ociosidade

    @Slot()
    def _on_cancelled(self) -> None:
        # Tecla extra apertada durante Ctrl+Win -> e atalho do sistema,
        # cancela a gravacao sem transcrever.
        if not self._recorder.is_recording:
            return
        log.info("PTT cancelled: terceira tecla detectada (system shortcut)")
        self._recorder.stop()  # descarta o buffer
        if self._cfg.show_overlay:
            self._overlay.show_cancelled()
        self._set_status("ready", f"pronto · {self._cfg.trigger_label}")

    @Slot(int)
    def _on_started_inf(self, request_id: int) -> None:
        log.debug("inferencia iniciada (req %d)", request_id)

    @Slot(object)
    def _on_asr_done(self, result: TranscriptionResult) -> None:
        text = result.text.strip()
        log.info("asr done: %.2fs audio -> %.2fs infer | %r",
                 result.duration_audio, result.duration_infer, text[:80])

        # 1) limpeza leve + grafia canônica do dicionário + macros PT-BR (sem LLM)
        from sussurro.asr.postprocess import postprocess
        text = postprocess(
            text,
            terms=self._dictionary.all(),
            macros=self._dictionary.all_macros(),
            capitalize=self._cfg.auto_capitalization,
        )

        # 2) comandos de voz ("nova linha", pontuação por extenso) — antes do
        # LLM pra modos com IA preservarem a estrutura
        from sussurro.commands import apply_commands
        text = apply_commands(text, self._cfg.voice_commands)

        # 3) aprende sugestões de vocabulário (não adiciona sozinho)
        try:
            self._dictionary.observe_text(text)
        except Exception:  # noqa: BLE001
            log.debug("observe_text falhou", exc_info=True)

        if not text:
            if self._cfg.show_overlay:
                self._overlay.show_done(ok=False)  # pílula âmbar "Não captei nada"
            self._set_status("ready",
                                     f"silêncio · {self._cfg.trigger_label}")
            return

        # Modo raw: cola direto. Modos com LLM: worker depois.
        if result.mode == "raw":
            self._finalize(result, text, used_llm=False)
            return

        # Modo LLM: empilha pro worker
        # Guarda a versão já pós-processada para o fallback de qualquer erro
        # inesperado do worker não voltar ao texto cru anterior.
        result.text = text
        self._pending_raw[result.request_id] = result
        self._llm_worker.submit(LLMJob(
            request_id=result.request_id,
            mode=result.mode,
            raw_text=text,
        ))

    @Slot(int, str)
    def _on_failed(self, request_id: int, error: str) -> None:
        log.error("transcricao falhou (req %d): %s", request_id, error)
        if request_id == -1:
            # falha total de load (nem CPU). Worker segue vivo pra re-tentar.
            self._start_hotkeys()
            msg = "sem GPU e CPU falhou"
            low = error.lower()
            if "cuda" in low or "cudnn" in low:
                msg = "CUDA/GPU indisponível"
            elif "memory" in low or "vram" in low:
                msg = "sem memória pra o modelo"
            if self._cfg.show_overlay:
                self._overlay.show_error(msg)
            self._set_status(
                "error",
                f"{msg} · fale de novo pra tentar ({self._cfg.trigger_label})")
            return
        if self._cfg.show_overlay:
            self._overlay.show_error("erro na transcrição")
        self._set_status("error", "erro de transcrição")

    @Slot(int)
    def _on_llm_started(self, request_id: int) -> None:
        pending = self._pending_raw.get(request_id)
        mode_id = pending.mode if pending else self._active_mode
        if self._cfg.show_overlay:
            self._overlay.show_processing(mode_id)  # spinner + chip do modo
        name = self._modes.get(mode_id).name
        self._set_status("loading", f"refinando · {name}...")

    @Slot(object)
    def _on_llm_done(self, result: LLMResult) -> None:
        log.info("llm done (req %d, mode=%s, used_llm=%s, reason=%s, %.0fms): %r",
                 result.request_id, result.mode, result.used_llm,
                 result.reason, result.duration_ms, result.processed_text[:80])
        asr_result = self._pending_raw.pop(result.request_id, None)
        if asr_result is None:
            log.warning("llm done sem asr correspondente, ignorando")
            return
        text = result.processed_text or result.raw_text
        self._finalize(asr_result, text,
                       used_llm=result.used_llm, reason=result.reason)

    @Slot(int, str)
    def _on_llm_failed(self, request_id: int, error: str) -> None:
        log.error("llm falhou (req %d): %s — usando raw", request_id, error)
        asr_result = self._pending_raw.pop(request_id, None)
        if asr_result is None:
            return
        # fallback: cola o texto raw
        self._finalize(asr_result, asr_result.text.strip(),
                       used_llm=False, reason="error")

    def _finalize(self,
                  asr_result: TranscriptionResult,
                  text: str,
                  used_llm: bool,
                  reason: str = "") -> None:
        """Salva no historico + cola no app + atualiza overlay/status."""
        self._modes.increment_usage(asr_result.mode)
        self._history.append(HistoryEntry(
            timestamp=time.time(),
            mode=asr_result.mode,
            text=text,
            duration_audio=asr_result.duration_audio,
            duration_infer=asr_result.duration_infer,
            language=asr_result.language,
        ))
        self._window.refresh_history()
        self._restart_idle()

        # Economia SEM perder qualidade do large-v3:
        # - Raw: Qwen não serve de nada → solta se ficou de um Clean anterior
        # - LLM com keep_alive=0: o próprio generate já soltou; reforço se residual
        if self._cfg.smart_economy:
            if asr_result.mode == "raw" or not used_llm:
                self._free_llm_vram("pos-raw")
            elif str(self._cfg.ollama_keep_alive) in ("0", "0m", "0s"):
                self._free_llm_vram("pos-llm-keep0")

        if self._cfg.paste_after_transcribe:
            # colar fora da thread da UI: paste_text tem sleeps (~0.3s no modo
            # clipboard) e keyboard.write lento em textos longos no modo "type"
            import threading
            threading.Thread(
                target=self._paste_bg,
                args=(asr_result, text, used_llm, reason),
                daemon=True, name="paste").start()
            return

        self._finish_ui(asr_result, used_llm, reason)

    def _paste_bg(self, asr_result: TranscriptionResult, text: str,
                  used_llm: bool, reason: str) -> None:
        """Roda em thread de fundo; resultado volta pra UI via sinal."""
        try:
            result = paste_text(
                text,
                method=self._cfg.paste_method,
                auto_fallback=self._cfg.paste_auto_fallback,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("falha ao colar texto")
            result = PasteResult(ok=False, message=f"erro ao colar: {exc!r}")
        self._pasted.emit(asr_result, used_llm, reason, result)

    @Slot(object, bool, str, object)
    def _on_pasted(self, asr_result: TranscriptionResult,
                   used_llm: bool, reason: str,
                   paste: object) -> None:
        pr = paste if isinstance(paste, PasteResult) else PasteResult(
            ok=bool(paste), message="" if paste else "falha ao colar")
        if not pr.ok:
            msg = pr.message or "falha ao colar"
            if self._cfg.show_overlay:
                # mensagem curta pro HUD (cabe na pílula)
                short = msg if len(msg) <= 48 else msg[:45] + "…"
                self._overlay.show_error(short)
            self._set_status("error", msg)
            # texto já está no histórico — usuário pode copiar de lá
            self._tray.notify("Não consegui colar", msg)
            return
        self._finish_ui(asr_result, used_llm, reason)

    def _finish_ui(self, asr_result: TranscriptionResult,
                   used_llm: bool, reason: str) -> None:
        ai_skipped = asr_result.mode != "raw" and not used_llm
        if self._cfg.show_overlay:
            if ai_skipped:
                # a IA do modo NAO rodou — avisa em vez de fingir sucesso
                why = {"offline": "Ollama offline",
                       "error": "erro na IA"}.get(reason, "IA indisponível")
                self._overlay.show_pasted_no_ai(why)
            else:
                # confirmacao (chip assina qual modo processou; raw fica limpo)
                self._overlay.show_done(
                    ok=True, mode=asr_result.mode if used_llm else None)
        from sussurro import sound
        sound.play("done", self._cfg.play_sound)
        status_msg = f"pronto · {self._cfg.trigger_label}"
        if ai_skipped:
            status_msg = f"colado sem IA · {self._cfg.trigger_label}"
        self._set_status("ready", status_msg)

    @Slot()
    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    @Slot()
    def _show_settings(self) -> None:
        from sussurro.ui.settings_ui import SettingsWindow
        if self._settings is None:
            self._settings = SettingsWindow(
                self._cfg, self._modes,
                active_mode_getter=lambda: self._mode,
                dictionary=self._dictionary)
            self._settings.config_changed.connect(self._on_settings_changed)
            self._settings.theme_changed.connect(self._set_theme_pref)
            self._settings.modes_changed.connect(self._on_modes_changed)
        self._settings.show()
        self._settings.raise_()
        self._settings.activateWindow()

    @Slot()
    def _on_settings_changed(self) -> None:
        # aplica efeitos colaterais + propaga a config pra janela principal
        from sussurro.storage import autostart
        autostart.set_enabled(self._cfg.autostart)
        self._window.sync_from_config()
        self._on_config_changed()

    def _set_status(self, kind: str, msg: str) -> None:
        """Atualiza o status na janela e na bandeja juntos."""
        self._window.set_status(kind, msg)
        self._tray.set_status(kind)

    @Slot()
    def _show_history(self) -> None:
        self._window.show()
        self._window._open_history()  # noqa: SLF001

    @Slot(str)
    def _on_tray_mode(self, mode_id: str) -> None:
        self._cfg.default_mode = mode_id
        self._cfg.save()
        self._mode = mode_id
        self._window.refresh_modes()
        self._overlay.set_mode(mode_id)

    @Slot()
    def _on_modes_changed(self) -> None:
        # modo pode ter sido desativado/deletado/renomeado -> revalida e propaga
        self._window.refresh_modes()
        self._mode = self._cfg.default_mode
        self._overlay.set_mode(self._mode)

    @Slot(str)
    def _set_theme_pref(self, pref: str) -> None:
        self._cfg.theme = pref
        self._cfg.save()
        QTimer.singleShot(0, self._reapply_theme)

    @Slot()
    def _on_system_scheme(self) -> None:
        if self._cfg.theme == "system":
            QTimer.singleShot(0, self._reapply_theme)

    def _reapply_theme(self) -> None:
        from sussurro.ui import theme
        from sussurro.ui.components import apply_theme_recursive
        theme.apply_preference(self._cfg.theme)
        self._qt.setStyleSheet(theme.app_base_qss())
        # re-tematiza TODAS as janelas abertas (principal, Ajustes, Histórico,
        # editor de modos, onboarding, setup, confirm...)
        for w in self._qt.topLevelWidgets():
            try:
                fn = getattr(w, "retheme", None)
                if callable(fn):
                    fn()
                else:
                    apply_fn = getattr(w, "apply_theme", None)
                    if callable(apply_fn):
                        apply_fn()
                    apply_theme_recursive(w)
                w.update()  # força o repaint na tela (não só no buffer)
            except Exception:  # noqa: BLE001
                log.exception("retheme falhou em %s", type(w).__name__)

    @Slot()
    def _on_close_to_tray(self) -> None:
        log.info("janela fechada -> tray")

    @Slot(bool)
    def _on_pause_toggled(self, paused: bool) -> None:
        """Interruptor Ativar / Desativar (economizar memória).

        Desativar = solta Whisper + Qwen da VRAM e ignora hotkey.
        Ativar = volta a ouvir; modelo carrega sob demanda (ou no preload).
        """
        if paused:
            self._disarm_engine(notify=True)
        else:
            self._arm_engine(notify=True)

    def _disarm_engine(self, notify: bool = True) -> None:
        """Modo espera: solta GPU e para de ouvir o atalho."""
        self._paused = True
        self._tray.set_paused(True)
        log.info("standby — liberando VRAM (Whisper + Ollama)")
        if self._recorder.is_recording:
            try:
                self._recorder.stop()
            except Exception:  # noqa: BLE001
                pass
        self._idle_timer.stop()
        self._llm_idle_timer.stop()
        # Whisper: pede unload se a thread existe
        if self._worker.isRunning():
            self._worker.request_unload()
        self._free_llm_vram("standby")
        self._set_status("paused", "em espera · memória liberada")
        if notify:
            self._tray.notify(
                "Sussurro em espera",
                "Modelos fora da VRAM. Ative de novo quando for ditar.",
            )

    def _arm_engine(self, notify: bool = True) -> None:
        """Modo ativo: hotkeys ligados; modelo sob demanda ou preload."""
        # SEMPRE limpa o flag — senão o hotkey ignora o PTT mesmo "armado"
        self._paused = False
        self._tray.set_paused(False)
        log.info("armed — pronto pra ditar (preload=%s)", self._cfg.preload_asr)
        self._start_hotkeys()
        if self._cfg.preload_asr:
            self._ensure_asr_started()
            self._set_status("loading", "carregando modelo...")
        else:
            # sem preload: zero VRAM até a 1ª fala
            self._set_status("ready", f"ativo · {self._cfg.trigger_label}")
        self._restart_idle()
        if notify:
            if self._cfg.preload_asr:
                self._tray.notify(
                    "Sussurro ativo",
                    "Carregando o modelo… depois é só segurar o atalho.",
                )
            else:
                self._tray.notify(
                    "Sussurro ativo",
                    f"Segure {self._cfg.trigger_label} pra falar "
                    "(1ª vez carrega o modelo).",
                )

    @Slot()
    def _on_config_changed(self) -> None:
        # algumas configs aplicam imediatamente, outras precisam restart
        self._mode = self._cfg.default_mode
        # idioma + preset de qualidade em runtime
        self._worker.set_language(self._cfg.language)
        try:
            self._worker.set_quality_preset(self._cfg.quality_preset)
        except Exception:  # noqa: BLE001
            pass
        # LLM: keep_alive e permissão de autostart sob demanda
        self._llm_worker.set_keep_alive(self._cfg.ollama_keep_alive)
        self._llm_worker.set_allow_autostart(True)
        # so reinstancia o Recorder se o mic realmente mudou (evita custo
        # a cada toggle de checkbox que nao tem nada a ver com audio)
        new_mic = self._cfg.mic_device or None
        if new_mic != getattr(self._recorder, "_device", None):
            self._recorder = Recorder(device=new_mic)
        # aplica troca do botao do mouse em runtime (sem restart)
        self._mouse_hotkey.set_button(self._cfg.mouse_button)
        self._overlay.set_mode(self._mode)
        self._restart_idle()  # liga/desliga o timer de VRAM conforme a config
        # mantem a janela de Ajustes em sincronia (mesma fonte de verdade)
        if self._settings is not None and self._settings.isVisible():
            self._settings.sync_from_config()
        log.info(
            "config: mode=%s mic=%s mouse=%s lang=%s ollama_boot=%s "
            "preload=%s keep_alive=%s unload_idle=%s",
            self._mode, self._cfg.mic_device or "default",
            self._cfg.mouse_button, self._cfg.language,
            self._cfg.ollama_autostart, self._cfg.preload_asr,
            self._cfg.ollama_keep_alive, self._cfg.unload_idle,
        )

    def _quit(self) -> None:
        self.shutdown()
        self._qt.quit()


def run() -> int:
    # logging pra arquivo + console
    handlers = [logging.StreamHandler(sys.stderr)]
    try:
        handlers.append(logging.FileHandler(log_path(), encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    qt = QApplication(sys.argv)
    qt.setApplicationName("Sussurro")
    qt.setOrganizationName("Sussurro")
    qt.setQuitOnLastWindowClosed(False)
    from sussurro.ui.components import brand_icon
    qt.setWindowIcon(brand_icon())
    # Fusion respeita 100% do QSS (estilo nativo do Windows pinta gradients
    # por cima da regra de background, "comendo" o efeito do Primary button).
    qt.setStyle("Fusion")

    # fontes Geist + Geist Mono (empacotadas) como padrao de todo o app
    from PySide6.QtGui import QFont

    from sussurro.ui import theme
    from sussurro.ui.fonts import load_fonts
    family = load_fonts()
    app_font = QFont(family)
    app_font.setPixelSize(13)
    app_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    qt.setFont(app_font)

    # tema ativo (system/dark/light) a partir da config, + QSS base global
    cfg = Config.load()
    theme.apply_preference(cfg.theme)
    qt.setStyleSheet(theme.app_base_qss())

    # se tray nao tiver disponivel, segue mesmo assim mas avisa
    if not QSystemTrayIcon.isSystemTrayAvailable():
        log.warning("system tray indisponivel — app vai rodar so com janela")

    app = App(qt)
    app.start()

    # Ctrl+C no console -> shutdown gracioso
    signal.signal(signal.SIGINT, lambda *_: qt.quit())
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(1000)  # so pra liberar o SIGINT sob o event loop Qt

    try:
        return qt.exec()
    finally:
        app.shutdown()


if __name__ == "__main__":
    sys.exit(run())
