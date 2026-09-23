"""Worker do faster-whisper rodando em QThread.

Mantem o modelo residente (VRAM ou RAM) e processa jobs de uma queue.

Fallback de dispositivo:
  1. device/compute preferidos (em geral CUDA)
  2. CUDA + int8 (VRAM apertada)
  3. CPU + int8 (sem GPU / driver quebrado) — mais lento, mas vivo

Presets de qualidade (beam_size / modelo) via quality_preset.
"""
from __future__ import annotations

import gc
import logging
import queue
import threading
import time
from dataclasses import dataclass, field

import numpy as np
from PySide6.QtCore import QThread, Signal

log = logging.getLogger("sussurro.asr")


@dataclass
class TranscriptionJob:
    audio: np.ndarray
    mode: str = "raw"
    initial_prompt: str | None = None
    hotwords: str | None = None
    request_id: int = 0


@dataclass
class PartialTranscriptionJob:
    audio: np.ndarray
    request_id: int
    initial_prompt: str | None = None


@dataclass
class TranscriptionResult:
    request_id: int
    text: str
    language: str
    duration_audio: float
    duration_infer: float
    mode: str
    segments: list = field(default_factory=list)
    device: str = "cuda"  # onde rodou de fato


# quality | balanced | light
_PRESETS: dict[str, dict] = {
    "quality":  {"beam_size": 5, "best_of": 5, "model_size": "large-v3-turbo",
                 "compute_type": "int8_float16"},
    "balanced": {"beam_size": 3, "best_of": 3, "model_size": "large-v3-turbo",
                 "compute_type": "int8_float16"},
    "light":    {"beam_size": 1, "best_of": 1, "model_size": "large-v3-turbo",
                 "compute_type": "int8"},
}


def resolve_preset(preset: str) -> dict:
    return dict(_PRESETS.get(preset, _PRESETS["quality"]))


_UNLOAD = object()
_WARMUP = object()


def _resolve_language(lang: str | None) -> str | None:
    if not lang or lang == "auto":
        return None
    return lang


class WhisperWorker(QThread):
    ready = Signal()
    started_transcription = Signal(int)
    done = Signal(object)
    partial = Signal(int, str)
    failed = Signal(int, str)
    reloading = Signal()
    recovered = Signal()
    # device real após load (cuda/cpu) + mensagem humana opcional
    device_ready = Signal(str, str)  # device, note

    def __init__(self,
                 model_size: str = "large-v3-turbo",
                 device: str = "cuda",
                 compute_type: str = "int8_float16",
                 language: str | None = "pt",
                 quality_preset: str = "quality") -> None:
        super().__init__()
        preset = resolve_preset(quality_preset)
        self._model_size = model_size or preset["model_size"]
        self._device = device
        self._compute_type = compute_type or preset["compute_type"]
        self._beam_size = int(preset["beam_size"])
        self._best_of = int(preset["best_of"])
        self._language = _resolve_language(language)
        self._quality_preset = quality_preset
        # o que a config pediu; _model_size/_device/_compute_type podem mudar
        # depois de um fallback, mas só um pedido diferente força reload
        self._requested = (self._model_size, device, self._compute_type)
        self._queue: queue.Queue = queue.Queue()
        self._model = None
        self._stop = False
        self._active_device = device
        self._active_compute = compute_type
        self._partial_lock = threading.Lock()
        self._partial_pending = False

    def set_language(self, language: str | None) -> None:
        self._language = _resolve_language(language)

    def set_quality_preset(self, preset: str) -> None:
        """Atualiza beam/best_of do preset. Não troca modelo nem compute."""
        p = resolve_preset(preset)
        self._quality_preset = preset
        self._beam_size = int(p["beam_size"])
        self._best_of = int(p["best_of"])

    def configure(self, *, model_size: str | None, compute_type: str | None,
                  quality_preset: str) -> bool:
        """Aplica modelo, compute e preset vindos da config.

        Segue a mesma regra do construtor: modelo e compute da config valem, e o
        preset só preenche o que estiver vazio. O modelo só é descarregado
        quando o pedido muda; um fallback anterior (CUDA int8, CPU) não conta
        como mudança. Retorna True quando um reload foi agendado.
        """
        self.set_quality_preset(quality_preset)
        p = resolve_preset(quality_preset)
        model = model_size or p["model_size"]
        compute = compute_type or p["compute_type"]
        requested_device = self._requested[1]
        if (model, requested_device, compute) == self._requested:
            return False
        self._requested = (model, requested_device, compute)
        self._model_size = model
        self._device = requested_device  # volta a tentar o dispositivo pedido
        self._compute_type = compute
        self.request_unload()  # recarrega na próxima job
        return True

    def submit(self, job: TranscriptionJob) -> None:
        self._queue.put(job)

    def submit_partial(self, job: PartialTranscriptionJob) -> bool:
        """Enfileira no máximo uma hipótese parcial por vez."""
        with self._partial_lock:
            if self._partial_pending:
                return False
            self._partial_pending = True
        self._queue.put(job)
        return True

    def shutdown(self) -> None:
        self._stop = True
        self._queue.put(None)

    def request_unload(self) -> None:
        self._queue.put(_UNLOAD)

    def request_warmup(self) -> None:
        """Carrega e aquece o modelo quando a thread já existe."""
        self._queue.put(_WARMUP)

    @property
    def active_device(self) -> str:
        return self._active_device

    def run(self) -> None:  # noqa: D401
        from sussurro.cuda_setup import setup_cuda_dll_path
        setup_cuda_dll_path()
        if self._load_model():
            self.ready.emit()

        while not self._stop:
            job = self._queue.get()
            if job is None:
                break
            if job is _UNLOAD:
                self._unload()
                continue
            if job is _WARMUP:
                if self._model is None and self._load_model():
                    self.ready.emit()
                elif self._model is not None:
                    self.ready.emit()
                continue
            try:
                if isinstance(job, PartialTranscriptionJob):
                    self._handle_partial(job)
                else:
                    self._handle(job)
            except Exception as exc:  # noqa: BLE001
                if isinstance(job, PartialTranscriptionJob):
                    # prévia ao vivo é descartável: o texto final ainda vem
                    log.warning("transcrição parcial falhou: %r", exc)
                else:
                    self.failed.emit(job.request_id, repr(exc))
            finally:
                if isinstance(job, PartialTranscriptionJob):
                    with self._partial_lock:
                        self._partial_pending = False

    def _load_attempts(self) -> list[tuple[str, str, str]]:
        """(device, compute_type, note) em ordem de preferência."""
        pref_dev = self._device or "cuda"
        pref_ct = self._compute_type or "int8_float16"
        attempts: list[tuple[str, str, str]] = [
            (pref_dev, pref_ct, ""),
        ]
        if pref_dev == "cuda":
            if pref_ct != "int8":
                attempts.append(("cuda", "int8", "VRAM limitada · int8"))
            attempts.append(("cpu", "int8", "sem GPU · CPU (mais lento)"))
        elif pref_dev != "cpu":
            attempts.append(("cpu", "int8", "fallback CPU"))
        # dedupe
        seen: set[tuple[str, str]] = set()
        out: list[tuple[str, str, str]] = []
        for a in attempts:
            key = (a[0], a[1])
            if key in seen:
                continue
            seen.add(key)
            out.append(a)
        return out

    def _load_model(self) -> bool:
        from faster_whisper import WhisperModel

        last_err: Exception | None = None
        for device, compute, note in self._load_attempts():
            try:
                log.info("carregando modelo %s device=%s compute=%s",
                         self._model_size, device, compute)
                try:
                    self._model = WhisperModel(
                        self._model_size, device=device,
                        compute_type=compute, local_files_only=True)
                except Exception:  # noqa: BLE001
                    self._model = WhisperModel(
                        self._model_size, device=device,
                        compute_type=compute)
                warm_lang = self._language or "pt"
                warmup = np.zeros(16_000, dtype=np.float32)
                list(self._model.transcribe(warmup, language=warm_lang)[0])
                self._active_device = device
                self._active_compute = compute
                self._device = device  # próximas loads preferem o que funcionou
                self._compute_type = compute
                if note:
                    log.warning("ASR em modo degradado: %s", note)
                self.device_ready.emit(device, note)
                return True
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                log.warning("load falhou (%s/%s): %s", device, compute, exc)
                self._model = None
                continue

        self.failed.emit(
            -1,
            f"falha ao carregar modelo: {last_err!r}",
        )
        return False

    def _unload(self) -> None:
        if self._model is not None:
            self._model = None
            gc.collect()

    def _handle(self, job: TranscriptionJob) -> None:
        if self._model is None:
            self.reloading.emit()
            if not self._load_model():
                return
            self.recovered.emit()
        self.started_transcription.emit(job.request_id)

        if job.audio.size < 16_000 // 4:
            self.done.emit(TranscriptionResult(
                request_id=job.request_id,
                text="",
                language=self._language or "pt",
                duration_audio=job.audio.size / 16_000,
                duration_infer=0.0,
                mode=job.mode,
                device=self._active_device,
            ))
            return

        t0 = time.perf_counter()
        kwargs: dict = dict(
            language=self._language,
            task="transcribe",
            beam_size=self._beam_size,
            best_of=self._best_of,
            patience=1.0,
            without_timestamps=True,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 350,
                "speech_pad_ms": 200,
            },
            condition_on_previous_text=False,
            temperature=[0.0, 0.2, 0.4],
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            hallucination_silence_threshold=0.4,
        )
        if job.initial_prompt:
            kwargs["initial_prompt"] = job.initial_prompt
        if job.hotwords:
            kwargs["hotwords"] = job.hotwords

        try:
            segments, info = self._model.transcribe(job.audio, **kwargs)
            segs = list(segments)
        except Exception as exc:  # noqa: BLE001
            # Degradação graciosa: se falhou no CUDA (ex: OOM), tenta CPU int8 sem perder o áudio
            if self._active_device == "cuda":
                log.warning("Falha durante inferência CUDA (%s). Executando fallback para CPU int8...", exc)
                self._unload()
                self._device = "cpu"
                self._compute_type = "int8"
                if self._load_model():
                    self.device_ready.emit("cpu", "fallback CPU após falha CUDA")
                    segments, info = self._model.transcribe(job.audio, **kwargs)
                    segs = list(segments)
                else:
                    raise
            else:
                raise

        text = "".join(s.text for s in segs).strip()
        if not text and segs:
            text = " ".join(s.text.strip() for s in segs).strip()
        t_infer = time.perf_counter() - t0

        self.done.emit(TranscriptionResult(
            request_id=job.request_id,
            text=text,
            language=getattr(info, "language", None) or self._language or "pt",
            duration_audio=job.audio.size / 16_000,
            duration_infer=t_infer,
            mode=job.mode,
            segments=[(s.start, s.end, s.text.strip()) for s in segs],
            device=self._active_device,
        ))

    def _handle_partial(self, job: PartialTranscriptionJob) -> None:
        """Gera uma hipótese barata para o HUD, sem tocar no campo ativo."""
        if self._model is None or job.audio.size < 16_000:
            return
        audio = job.audio[-16_000 * 12:]
        kwargs: dict = {
            "language": self._language,
            "task": "transcribe",
            "beam_size": 1,
            "best_of": 1,
            "without_timestamps": True,
            "vad_filter": True,
            "condition_on_previous_text": False,
            "temperature": 0.0,
        }
        if job.initial_prompt:
            kwargs["initial_prompt"] = job.initial_prompt
        segments, _ = self._model.transcribe(audio, **kwargs)
        text = "".join(segment.text for segment in segments).strip()
        if text:
            self.partial.emit(job.request_id, text)
