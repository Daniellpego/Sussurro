"""Configura caminho de busca de DLLs CUDA antes de importar ctranslate2.

No Windows precisamos de DOIS mecanismos pra cobrir todos os casos:
1. `os.add_dll_directory(...)` - cobre LoadLibraryExW com flag de search dirs
2. Modificar `os.environ["PATH"]` - cobre LoadLibraryW legacy

Funciona em dois modos:
- Venv: localiza pacotes nvidia-*-cu12 via importlib.find_spec
- PyInstaller bundle: olha em `sys._MEIPASS/nvidia/*/bin`

Sem isso o ctranslate2 nao encontra cublas64_12.dll / cudnn_*.dll.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_done = False
_PACKAGES = ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_nvrtc")
_BUNDLE_SUBPATHS = ("nvidia/cublas/bin", "nvidia/cudnn/bin", "nvidia/cuda_nvrtc/bin")


def _bundle_root() -> Path | None:
    """Raiz dos arquivos quando rodando como PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        # PyInstaller one-folder: _MEIPASS == diretorio root
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return None


def _find_bin_dirs() -> list[str]:
    dirs: list[str] = []

    # 1) Procura via importlib (venv mode)
    for pkg in _PACKAGES:
        try:
            spec = importlib.util.find_spec(pkg)
        except (ImportError, ValueError):
            spec = None
        if spec is None or spec.submodule_search_locations is None:
            continue
        for loc in spec.submodule_search_locations:
            bin_dir = Path(loc) / "bin"
            if bin_dir.is_dir():
                dirs.append(str(bin_dir))

    # 2) Procura no bundle PyInstaller
    bundle = _bundle_root()
    if bundle is not None:
        for sub in _BUNDLE_SUBPATHS:
            bin_dir = bundle / sub
            if bin_dir.is_dir():
                dirs.append(str(bin_dir))

    # dedup mantendo ordem
    seen: set[str] = set()
    unique: list[str] = []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique


def setup_cuda_dll_path() -> None:
    global _done
    if _done:
        return

    bin_dirs = _find_bin_dirs()

    # 1) PATH env var (cobre LoadLibraryW legacy + DLLs transitivas)
    if bin_dirs:
        existing = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(bin_dirs + [existing])

    # 2) add_dll_directory (Python 3.8+ DLL search path)
    for d in bin_dirs:
        try:
            os.add_dll_directory(d)
        except (OSError, FileNotFoundError):
            pass

    _done = True
