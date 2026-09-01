"""Benchmark reproduzível do modelo de produção e resumo das métricas locais."""
from __future__ import annotations

import argparse
import json
import statistics
import time
import wave
from pathlib import Path

import numpy as np

MODEL = "large-v3-turbo"


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def summary(values: list[float]) -> dict[str, float]:
    return {
        "p50_ms": round(statistics.median(values), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
        "worst_ms": round(max(values), 3),
    }


def load_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        if wav.getframerate() != 16_000 or wav.getnchannels() != 1:
            raise ValueError("o áudio precisa ser WAV mono de 16 kHz")
        width = wav.getsampwidth()
        raw = wav.readframes(wav.getnframes())
    if width != 2:
        raise ValueError("o áudio precisa usar PCM de 16 bits")
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def run(audio: np.ndarray, device: str, iterations: int) -> dict[str, object]:
    from faster_whisper import WhisperModel

    compute = "int8_float16" if device == "cuda" else "int8"
    model = WhisperModel(MODEL, device=device, compute_type=compute)
    list(model.transcribe(np.zeros(16_000, dtype=np.float32), language="pt")[0])
    values: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        segments, _ = model.transcribe(audio, language="pt", vad_filter=True)
        list(segments)
        values.append((time.perf_counter() - started) * 1000)
    return {
        "model": MODEL,
        "device": device,
        "compute_type": compute,
        "iterations": iterations,
        "audio_seconds": round(audio.size / 16_000, 3),
        "stt": summary(values),
        "samples_ms": [round(value, 3) for value in values],
    }


def summarize_metrics(path: Path) -> dict[str, dict[str, float]]:
    stages: dict[str, list[float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("metadata", {}).get("model") != MODEL:
            continue
        for name, value in record.get("durations_ms", {}).items():
            stages.setdefault(name, []).append(float(value))
    return {name: summary(values) for name, values in sorted(stages.items())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument(
        "--metrics", type=Path,
        help="JSONL produzido pelo app para resumir o pipeline completo",
    )
    args = parser.parse_args()
    if args.iterations < 10:
        parser.error("use pelo menos 10 iterações")
    result = run(load_wav(args.audio), args.device, args.iterations)
    if args.metrics:
        result["pipeline"] = summarize_metrics(args.metrics)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
