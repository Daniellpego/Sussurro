"""Captura de audio via sounddevice.

Push-to-talk: `start()` abre a stream, `stop()` retorna o buffer
acumulado como np.float32 mono em 16 kHz (formato esperado pelo Whisper).

Em paralelo, calcula nivel RMS por chunk pra alimentar o waveform da UI.
"""
from __future__ import annotations

import threading
from collections import deque

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 1024  # ~64 ms a 16 kHz


class Recorder:
    """Recorder de push-to-talk com nivel RMS instantaneo."""

    def __init__(self,
                 sample_rate: int = SAMPLE_RATE,
                 device: int | str | None = None) -> None:
        self._sr = sample_rate
        self._device = device
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._level = 0.0
        self._level_history: deque[float] = deque(maxlen=32)

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            # underflow nao e fatal, so loga
            pass
        chunk = indata.copy()
        with self._lock:
            self._chunks.append(chunk)
        # RMS normalizado (0..1, ajustado pra fala humana)
        rms = float(np.sqrt(np.mean(chunk * chunk)))
        # mapeamento percepcual: -40 dB ate 0 dB -> 0..1
        db = 20 * np.log10(max(rms, 1e-6))
        norm = max(0.0, min(1.0, (db + 40.0) / 40.0))
        self._level = norm
        self._level_history.append(norm)

    def start(self) -> None:
        if self._stream is not None:
            return
        with self._lock:
            self._chunks.clear()
            self._level = 0.0
            self._level_history.clear()
        stream = sd.InputStream(
            samplerate=self._sr,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            device=self._device,
            callback=self._callback,
        )
        try:
            stream.start()
        except Exception:
            try:
                stream.close()
            finally:
                self._stream = None
            raise
        self._stream = stream

    def stop(self) -> np.ndarray:
        if self._stream is None:
            return np.zeros(0, dtype=np.float32)
        stream = self._stream
        self._stream = None
        try:
            stream.stop()
        finally:
            stream.close()
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0).flatten()
            self._chunks.clear()
        return audio.astype(np.float32, copy=False)

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    @property
    def level(self) -> float:
        """Nivel RMS instantaneo, 0..1."""
        return self._level

    def recent_levels(self, n: int) -> list[float]:
        """Ultimos n niveis RMS (mais antigo -> mais recente)."""
        with self._lock:
            data = list(self._level_history)
        if len(data) >= n:
            return data[-n:]
        return [0.0] * (n - len(data)) + data
