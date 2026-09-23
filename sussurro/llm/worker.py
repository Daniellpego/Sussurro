"""QThread worker que aplica um modo (system prompt) a um texto via Ollama."""
from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from sussurro.llm import ollama as ollama_client
from sussurro.llm.modes import DEFAULT_LLM_MODEL, ModeStore

log = logging.getLogger("sussurro")


@dataclass
class LLMJob:
    request_id: int
    mode: str
    raw_text: str


@dataclass
class LLMResult:
    request_id: int
    mode: str
    raw_text: str
    processed_text: str
    duration_ms: float
    used_llm: bool   # False se modo == raw ou Ollama indisponivel
    # por que used_llm=False: "raw" | "offline" | "no_model" | "error"
    reason: str = ""


class LLMWorker(QThread):
    started_processing = Signal(int)
    done = Signal(object)            # LLMResult
    failed = Signal(int, str)

    def __init__(self, store: ModeStore, model: str | None = None,
                 keep_alive: str = "0",
                 allow_autostart: bool = True) -> None:
        super().__init__()
        self._store = store
        self._model = model or ollama_client.DEFAULT_MODEL
        self._keep_alive = keep_alive
        self._allow_autostart = allow_autostart
        self._queue: queue.Queue[LLMJob | None] = queue.Queue()
        self._stop = False
        self._autostart_tried = False

    def set_keep_alive(self, value: str) -> None:
        # "0" é válido (descarrega na hora)
        self._keep_alive = "0" if value is None or value == "" else value

    def set_allow_autostart(self, value: bool) -> None:
        self._allow_autostart = value

    def _resolve_model(self, mode_id: str) -> str:
        """Modelo do modo, se customizado; senão o default global (tag real)."""
        m = self._store.get(mode_id)
        if m.model and m.model != DEFAULT_LLM_MODEL:
            return m.model
        return self._model

    def _try_autostart(self) -> None:
        """Sobe o Ollama só sob demanda (1ª vez que um modo com IA precisar)."""
        if not self._allow_autostart or self._autostart_tried:
            return
        self._autostart_tried = True
        threading.Thread(target=ollama_client.try_start,
                         daemon=True, name="ollama-autostart").start()

    def submit(self, job: LLMJob) -> None:
        self._queue.put(job)

    def shutdown(self) -> None:
        self._stop = True
        self._queue.put(None)

    def run(self) -> None:  # noqa: D401
        while not self._stop:
            job = self._queue.get()
            if job is None:
                break
            try:
                self._handle(job)
            except Exception as exc:  # noqa: BLE001
                self.failed.emit(job.request_id, repr(exc))

    def _degrade(self, job: LLMJob, reason: str) -> None:
        """Cola o texto cru — mas SEMPRE dizendo por quê (nunca silencioso)."""
        self.done.emit(LLMResult(
            request_id=job.request_id,
            mode=job.mode,
            raw_text=job.raw_text,
            processed_text=job.raw_text,
            duration_ms=0.0,
            used_llm=False,
            reason=reason,
        ))

    def _handle(self, job: LLMJob) -> None:
        # Raw mode -> bypass
        if job.mode == "raw":
            self._degrade(job, "raw")
            return

        # Ollama parado: tenta subir sob demanda (se permitido) e re-checa.
        # Se ainda offline -> cola raw com reason="offline" (HUD honesto).
        if not ollama_client.is_running():
            if self._allow_autostart and not self._autostart_tried:
                self._try_autostart()
                # espera curta o serve subir (sem travar minutos)
                deadline = time.monotonic() + 8.0
                while time.monotonic() < deadline:
                    if ollama_client.is_running(timeout=0.4):
                        break
                    time.sleep(0.35)
            if not ollama_client.is_running():
                self._degrade(job, "offline")
                return

        self.started_processing.emit(job.request_id)

        system_prompt = self._store.get_prompt(job.mode)
        user_prompt = (
            f"Texto transcrito da fala:\n"
            f"\"\"\"\n{job.raw_text}\n\"\"\""
        )

        t0 = time.perf_counter()
        try:
            result = ollama_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                model=self._resolve_model(job.mode),
                temperature=0.25,
                keep_alive=self._keep_alive,
            )
        except ollama_client.OllamaModelMissing as exc:
            log.error("llm sem modelo (modo=%s): %s — colando raw", job.mode, exc)
            self._degrade(job, "no_model")
            return
        except ollama_client.OllamaError as exc:
            log.error("llm erro (modo=%s): %s — colando raw", job.mode, exc)
            self._degrade(job, "error")
            return
        dt_ms = (time.perf_counter() - t0) * 1000.0

        processed = result.text.strip()
        # remove aspas circundantes se LLM teimar
        if processed.startswith('"') and processed.endswith('"'):
            processed = processed[1:-1].strip()

        self.done.emit(LLMResult(
            request_id=job.request_id,
            mode=job.mode,
            raw_text=job.raw_text,
            processed_text=processed or job.raw_text,
            duration_ms=dt_ms,
            used_llm=True,
        ))
