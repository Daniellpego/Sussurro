"""Captura de áudio com stream pré-aberto e pré-buffer."""
from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

import numpy as np

try:
    import sounddevice as sd
except OSError:
    class _UnavailableSoundDevice:
        def InputStream(self, **_kwargs):
            raise OSError("PortAudio não está disponível")

    sd = _UnavailableSoundDevice()

SAMPLE_RATE = 16_000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 320  # 20 ms a 16 kHz
PREBUFFER_MS = 300


def _input_devices() -> list[tuple[int, dict]]:
    try:
        devices = list(sd.query_devices())
    except Exception:  # noqa: BLE001
        return []
    return [(i, d) for i, d in enumerate(devices)
            if d.get("max_input_channels", 0) > 0]


def _default_input_hostapi() -> int | None:
    try:
        return int(sd.query_devices(kind="input")["hostapi"])
    except Exception:  # noqa: BLE001
        return None


def list_input_devices() -> list[str]:
    """Nomes dos microfones, um por aparelho.

    O Windows expõe o mesmo microfone em várias APIs (MME, DirectSound,
    WASAPI...). A lista usa só a API do microfone padrão, e cai para todas
    as APIs, sem nomes repetidos, se a padrão não for conhecida.
    """
    devices = _input_devices()
    hostapi = _default_input_hostapi()
    if hostapi is not None and any(d.get("hostapi") == hostapi for _, d in devices):
        devices = [(i, d) for i, d in devices if d.get("hostapi") == hostapi]
    names: list[str] = []
    for _, d in devices:
        name = d.get("name", "")
        if name and name not in names:
            names.append(name)
    return names


def resolve_input_device(device: int | str | None) -> int | None:
    """Converte o nome salvo na config no índice do dispositivo.

    Passar só o nome ao sounddevice falha com "Multiple input devices found"
    quando o nome aparece em mais de uma API. None usa o microfone padrão.
    """
    if device is None or isinstance(device, int):
        return device
    wanted = device.strip()
    if not wanted:
        return None
    devices = _input_devices()
    hostapi = _default_input_hostapi()
    preferred = [(i, d) for i, d in devices if d.get("hostapi") == hostapi]
    for pool in (preferred, devices):
        for i, d in pool:
            if d.get("name") == wanted:
                return i
    # o MME corta nomes em 31 caracteres; aceita o nome cortado de um lado
    # ou de outro quando ele identifica um único aparelho
    lowered = wanted.lower()
    prefixed = {d.get("name") for _, d in devices
                if len(d.get("name", "")) >= 20
                and (lowered.startswith(d["name"].lower())
                     or d["name"].lower().startswith(lowered))}
    if len(prefixed) == 1:
        name = prefixed.pop()
        for pool in (preferred, devices):
            for i, d in pool:
                if d.get("name") == name:
                    return i
    raise ValueError(f"microfone não encontrado: {wanted}")


class Recorder:
    """Recorder de push-to-talk que mantém o dispositivo pronto."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        device: int | str | None = None,
        on_first_frame: Callable[[float], None] | None = None,
    ) -> None:
        self._sr = sample_rate
        self._device = device
        self._chunks: list[np.ndarray] = []
        self._prebuffer: deque[np.ndarray] = deque(
            maxlen=max(1, round(PREBUFFER_MS * sample_rate / 1000 / BLOCK_SIZE))
        )
        self._lock = threading.Lock()
        self._stream: object | None = None
        self._active = False
        self._stream_ready = threading.Event()
        self._stream_ready_at: float | None = None
        self._first_frame_at: float | None = None
        self._on_first_frame = on_first_frame
        self._level = 0.0
        self._level_history: deque[float] = deque(maxlen=32)

    def _callback(self, indata, frames, time_info, status) -> None:
        del frames, time_info, status
        now = time.perf_counter()
        chunk = indata.copy()
        first_frame_callback = None
        with self._lock:
            if not self._stream_ready.is_set():
                self._stream_ready_at = now
                self._stream_ready.set()
            self._prebuffer.append(chunk)
            if self._active:
                self._chunks.append(chunk)
                if self._first_frame_at is None:
                    self._first_frame_at = now
                    first_frame_callback = self._on_first_frame
        if first_frame_callback is not None:
            first_frame_callback(now)

        rms = float(np.sqrt(np.mean(chunk * chunk)))
        db = 20 * np.log10(max(rms, 1e-6))
        norm = max(0.0, min(1.0, (db + 40.0) / 40.0))
        self._level = norm
        self._level_history.append(norm)

    def prepare(self, timeout: float = 2.0) -> float:
        """Abre o stream uma vez e espera o primeiro callback do dispositivo."""
        if self._stream is not None:
            if not self._stream_ready.wait(timeout):
                raise TimeoutError("microfone aberto, mas sem frames")
            return self._stream_ready_at or time.perf_counter()

        self._stream_ready.clear()
        stream = sd.InputStream(
            samplerate=self._sr,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            device=resolve_input_device(self._device),
            callback=self._callback,
        )
        try:
            stream.start()
            self._stream = stream
            if not self._stream_ready.wait(timeout):
                raise TimeoutError("microfone não entregou o primeiro frame")
        except Exception:
            try:
                stream.close()
            finally:
                self._stream = None
                self._stream_ready.clear()
            raise
        return self._stream_ready_at or time.perf_counter()

    def start(self) -> float:
        """Começa uma gravação sem reabrir o dispositivo."""
        self.prepare()
        ready_at = time.perf_counter()
        with self._lock:
            if self._active:
                return ready_at
            self._chunks = [chunk.copy() for chunk in self._prebuffer]
            self._first_frame_at = None
            self._active = True
            self._level_history.clear()
        return ready_at

    def snapshot(self) -> np.ndarray:
        """Cópia do áudio acumulado, sem interromper a captura."""
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            chunks = [chunk.copy() for chunk in self._chunks]
        return np.concatenate(chunks, axis=0).flatten().astype(np.float32, copy=False)

    def stop(self) -> np.ndarray:
        """Finaliza a gravação, mas mantém o stream preparado."""
        with self._lock:
            if not self._active:
                return np.zeros(0, dtype=np.float32)
            self._active = False
            chunks = self._chunks
            self._chunks = []
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks, axis=0).flatten().astype(np.float32, copy=False)

    def close(self) -> None:
        """Fecha o dispositivo no standby, troca de microfone ou shutdown."""
        stream = self._stream
        self._stream = None
        with self._lock:
            self._active = False
            self._chunks.clear()
            self._prebuffer.clear()
        self._stream_ready.clear()
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()

    @property
    def is_recording(self) -> bool:
        return self._active

    @property
    def is_ready(self) -> bool:
        return self._stream is not None and self._stream_ready.is_set()

    @property
    def stream_ready_at(self) -> float | None:
        return self._stream_ready_at

    @property
    def first_frame_at(self) -> float | None:
        return self._first_frame_at

    @property
    def level(self) -> float:
        return self._level

    def recent_levels(self, n: int) -> list[float]:
        with self._lock:
            data = list(self._level_history)
        if len(data) >= n:
            return data[-n:]
        return [0.0] * (n - len(data)) + data
