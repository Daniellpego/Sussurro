"""Gera os sons de feedback em sussurro/assets/sounds.

Os arquivos são sintetizados aqui para não depender de áudio de terceiros.
Uso:
    python scripts/generate_sounds.py
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sussurro" / "assets" / "sounds"
RATE = 44_100
VOLUME = 0.22


def _tone(start_hz: float, end_hz: float, ms: float) -> np.ndarray:
    n = int(RATE * ms / 1000)
    freq = np.linspace(start_hz, end_hz, n)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    # ataque curto e decaimento suave, sem estalo nas pontas
    attack = np.minimum(1.0, np.arange(n) / (RATE * 0.005))
    decay = np.exp(-np.linspace(0, 5, n))
    return np.sin(phase) * attack * decay


def _silence(ms: float) -> np.ndarray:
    return np.zeros(int(RATE * ms / 1000))


def _write(name: str, samples: np.ndarray) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(samples * VOLUME, -1, 1)
    data = (pcm * 32767).astype("<i2").tobytes()
    path = OUT / f"{name}.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(data)
    return path


def main() -> None:
    # início da gravação: um toque curto subindo
    print(_write("start", _tone(660, 880, 90)))
    # ditado concluído: duas notas ascendentes
    print(_write("done", np.concatenate([
        _tone(880, 880, 70), _silence(15), _tone(1320, 1320, 110),
    ])))


if __name__ == "__main__":
    main()
