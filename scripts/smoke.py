"""Smoke test da Phase 0.

Carrega o `faster-whisper large-v3` em int8_float16 na GPU, grava ~6 s do
microfone default, transcreve e imprime tempos. Objetivo: provar que a
stack (CUDA + cuDNN + CTranslate2 + sounddevice) está viva antes de
construir qualquer coisa em cima.

Uso:
    python scripts/smoke.py             # grava do mic
    python scripts/smoke.py audio.wav   # transcreve arquivo existente
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

# Com stdout redirecionado (CI, runtime) o Windows cai pra cp1252, que não
# cobre a seta "→" dos timestamps e derruba o print no fim da transcrição.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# Usa o loader de DLLs CUDA da própria lib em vez de uma cópia local: ele
# cobre add_dll_directory *e* PATH (necessário pro LoadLibraryW legacy),
# inclui cuda_nvrtc e funciona em bundle PyInstaller. Sem isso o CTranslate2
# não acha cublas64_12.dll no Windows.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sussurro.cuda_setup  # noqa: E402  (precisa de ROOT no sys.path)

sussurro.cuda_setup.setup_cuda_dll_path()

from faster_whisper import WhisperModel  # noqa: E402  (after DLL setup)

SAMPLE_RATE = 16_000
RECORD_SECONDS = 6
MODEL_SIZE = "large-v3"
COMPUTE_TYPE = "int8_float16"
DEVICE = "cuda"


def record_from_mic(seconds: int = RECORD_SECONDS) -> np.ndarray:
    print(f"[mic ] gravando {seconds}s — fale algo "
          "(misture PT-BR + termos em inglês pra testar code-switching)...")
    audio = sd.rec(int(seconds * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE,
                   channels=1,
                   dtype="float32")
    sd.wait()
    print("[mic ] gravação concluída.")
    return audio.flatten()


def load_audio_file(path: Path) -> np.ndarray:
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != SAMPLE_RATE:
        raise SystemExit(
            f"audio precisa estar em {SAMPLE_RATE} Hz, recebido {sr} Hz"
        )
    return data


def main() -> int:
    print(f"[init] python {sys.version.split()[0]} | cwd={os.getcwd()}")
    print(f"[init] device={DEVICE} | model={MODEL_SIZE} | "
          f"compute_type={COMPUTE_TYPE}")

    t0 = time.perf_counter()
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    t_load = time.perf_counter() - t0
    print(f"[load] modelo carregado em {t_load:.2f}s")

    if len(sys.argv) > 1:
        audio = load_audio_file(Path(sys.argv[1]))
        source = sys.argv[1]
    else:
        audio = record_from_mic()
        source = f"mic ({RECORD_SECONDS}s)"

    audio_seconds = len(audio) / SAMPLE_RATE
    print(f"[asr ] transcrevendo {source} ({audio_seconds:.2f}s de áudio)...")

    t0 = time.perf_counter()
    segments, info = model.transcribe(
        audio,
        language=None,            # autodetect; deve cair em "pt"
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=False,
    )
    segments = list(segments)     # força geração (é generator preguiçoso)
    t_infer = time.perf_counter() - t0

    print(f"[asr ] idioma detectado: {info.language} "
          f"(prob={info.language_probability:.2f})")
    print(f"[asr ] inferência: {t_infer:.2f}s "
          f"({audio_seconds/t_infer:.2f}× tempo real)")
    print("-" * 60)
    for seg in segments:
        print(f"  [{seg.start:5.2f}s → {seg.end:5.2f}s] {seg.text.strip()}")
    print("-" * 60)
    print("[done] smoke test ok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
