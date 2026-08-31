"""Valida que faster-whisper carrega na GPU sem precisar de microfone.

Loadingo apenas: carrega `large-v3` em int8_float16, transcreve um buffer
sintético curto (silencio + ruido), reporta tempos e VRAM. Se isso roda,
o stack CUDA+cuDNN+CTranslate2 esta saudavel.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np


def _load_cuda_dlls() -> None:
    import importlib.util

    for pkg in ("nvidia.cublas", "nvidia.cudnn"):
        spec = importlib.util.find_spec(pkg)
        if spec is None or spec.submodule_search_locations is None:
            continue
        for loc in spec.submodule_search_locations:
            bin_dir = Path(loc) / "bin"
            if bin_dir.is_dir():
                os.add_dll_directory(str(bin_dir))


_load_cuda_dlls()

from faster_whisper import WhisperModel  # noqa: E402


def main() -> int:
    print(f"[init] python {sys.version.split()[0]}")
    print("[init] device=cuda | model=large-v3 | compute_type=int8_float16")
    print("[init] (primeira execucao baixa o modelo, ~3 GB)")

    t0 = time.perf_counter()
    model = WhisperModel(
        "large-v3",
        device="cuda",
        compute_type="int8_float16",
    )
    t_load = time.perf_counter() - t0
    print(f"[load] modelo carregado em {t_load:.2f}s")

    rng = np.random.default_rng(42)
    audio = rng.standard_normal(16_000 * 3).astype(np.float32) * 0.001
    audio[:16_000] = 0.0

    t0 = time.perf_counter()
    segments, info = model.transcribe(
        audio,
        language="pt",
        beam_size=5,
        vad_filter=True,
    )
    list(segments)
    t_infer = time.perf_counter() - t0

    print(f"[asr ] inferencia em buffer sintetico de 3s: {t_infer:.2f}s")
    print(f"[asr ] idioma forcado=pt | duracao detectada={info.duration:.2f}s")
    print("[ok  ] stack CUDA+cuDNN+CTranslate2 funcionando.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
