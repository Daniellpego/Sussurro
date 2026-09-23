"""Transcritor de arquivos de áudio locais (reuniões, aulas, podcasts, mentorias).

Reutiliza o faster-whisper e o pós-processador do Sussurro com fallback de hardware
e suporte para salvar diretamente na pasta RAW/ do Segundo Cérebro.

Uso:
    python -m sussurro.transcribe_file caminho/do/audio.mp3
    python -m sussurro.transcribe_file audio.m4a --output e:/Dados/RAW/mentoria.txt
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel

from sussurro.asr.postprocess import postprocess
from sussurro.cuda_setup import setup_cuda_dll_path


def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def load_model(
    model_size: str = "large-v3-turbo",
    device: str = "cuda",
    compute_type: str = "int8_float16",
) -> tuple[WhisperModel, str]:
    """Carrega o faster-whisper tentando CUDA e caindo para CPU se necessário."""
    setup_cuda_dll_path()

    if device == "cuda":
        try:
            print(f"Carregando {model_size} na GPU (CUDA, compute={compute_type})...")
            model = WhisperModel(model_size, device="cuda", compute_type=compute_type)
            return model, "cuda"
        except Exception as exc:
            print(f"Aviso: falha ao inicializar CUDA ({exc}). Recorrendo à CPU...")

    print(f"Carregando {model_size} na CPU (compute=int8)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return model, "cpu"


def transcribe_file(
    audio_path: str | Path,
    output_path: str | Path | None = None,
    model_size: str = "large-v3-turbo",
    device: str = "cuda",
    compute_type: str = "int8_float16",
    language: str = "pt",
    apply_postprocess: bool = True,
) -> Path:
    audio = Path(audio_path).resolve()
    if not audio.exists() or not audio.is_file():
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio}")

    # Determina destino padrão se não for especificado
    if output_path is None:
        raw_dir = Path("E:/Dados/RAW")
        if raw_dir.exists() and raw_dir.is_dir():
            out_file = raw_dir / f"{audio.stem}.txt"
        else:
            out_file = audio.with_suffix(".txt")
    else:
        out_file = Path(output_path).resolve()

    start_time = time.perf_counter()
    model, used_device = load_model(model_size, device, compute_type)

    print(f"Transcrevendo '{audio.name}' com Whisper em {used_device}...")
    segments_iter, info = model.transcribe(
        str(audio),
        language=language if language != "auto" else None,
        beam_size=5,
    )

    segments_data: list[tuple[float, float, str]] = []
    full_paragraphs: list[str] = []

    for seg in segments_iter:
        text = seg.text.strip()
        if not text:
            continue
        if apply_postprocess:
            text = postprocess(text)
        segments_data.append((seg.start, seg.end, text))
        full_paragraphs.append(text)

    elapsed = time.perf_counter() - start_time
    duration_audio = info.duration or (segments_data[-1][1] if segments_data else 0.0)

    # Monta cabeçalho formatado para arquivo RAW
    header = [
        "---",
        "tipo: transcricao_audio",
        f"arquivo_origem: {audio.name}",
        f"data_transcricao: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"duracao_audio: {_format_time(duration_audio)} ({duration_audio:.1f}s)",
        f"tempo_processamento: {elapsed:.1f}s (dispositivo: {used_device})",
        f"modelo_whisper: {model_size}",
        "---",
        "",
        f"# Transcrição: {audio.stem}",
        "",
        "## ⏱️ Transcrição Detalhada por Minutagem",
        "",
    ]

    for start, end, text in segments_data:
        header.append(f"**[{_format_time(start)} - {_format_time(end)}]** {text}")

    header.extend([
        "",
        "## 📝 Texto Contínuo Consolidado",
        "",
        " ".join(full_paragraphs),
        "",
    ])

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(header), encoding="utf-8")

    print(f"Sucesso! Transcrição concluída em {elapsed:.1f}s (Áudio de {_format_time(duration_audio)}).")
    print(f"Arquivo salvo em: {out_file}")
    return out_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcreve arquivos de áudio locais com faster-whisper e pós-processamento do Sussurro."
    )
    parser.add_argument("audio_path", help="Caminho do arquivo de áudio (.mp3, .wav, .m4a, etc.)")
    parser.add_argument(
        "-o", "--output", help="Caminho do arquivo de saída .txt/.md (padrão: E:/Dados/RAW/<nome>.txt se existir)"
    )
    parser.add_argument(
        "-m", "--model", default="large-v3-turbo", help="Tamanho do modelo (padrão: large-v3-turbo)"
    )
    parser.add_argument(
        "-d", "--device", default="cuda", choices=["cuda", "cpu"], help="Dispositivo de execução"
    )
    parser.add_argument(
        "-c", "--compute-type", default="int8_float16", help="Precisão de cálculo (padrão: int8_float16)"
    )
    parser.add_argument("-l", "--language", default="pt", help="Idioma do áudio (padrão: pt)")
    parser.add_argument(
        "--raw", action="store_true", help="Desabilita o pós-processamento de pontuação em português"
    )

    args = parser.parse_args(argv)
    try:
        transcribe_file(
            audio_path=args.audio_path,
            output_path=args.output,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            apply_postprocess=not args.raw,
        )
        return 0
    except Exception as exc:
        print(f"Erro na transcrição: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
