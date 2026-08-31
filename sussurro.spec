# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Sussurro.

One-folder build em `dist/Sussurro/`:
- entry point: sussurro/__main__.py -> Sussurro.exe
- inclui DLLs CUDA do nvidia-cublas-cu12 e nvidia-cudnn-cu12
- inclui binarios do ctranslate2, onnxruntime, av
- exclui o modelo Whisper (~3 GB) — baixado na primeira execucao

Build:
    .\.venv\Scripts\pyinstaller.exe --noconfirm sussurro.spec
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)


block_cipher = None


def _find_nvidia_bin_dirs() -> list[tuple[str, str]]:
    """Retorna [(src_dir, dest_dir_in_bundle), ...] das DLLs CUDA."""
    pairs: list[tuple[str, str]] = []
    for pkg, dest in (
        ("nvidia.cublas",       "nvidia/cublas/bin"),
        ("nvidia.cudnn",        "nvidia/cudnn/bin"),
        ("nvidia.cuda_nvrtc",   "nvidia/cuda_nvrtc/bin"),
    ):
        spec = importlib.util.find_spec(pkg)
        if spec is None or spec.submodule_search_locations is None:
            continue
        for loc in spec.submodule_search_locations:
            bin_dir = Path(loc) / "bin"
            if bin_dir.is_dir():
                pairs.append((str(bin_dir), dest))
    return pairs


# binarios extras: CUDA + ctranslate2 + onnxruntime + av
binaries: list[tuple[str, str]] = []
binaries += collect_dynamic_libs("ctranslate2")
binaries += collect_dynamic_libs("onnxruntime")
binaries += collect_dynamic_libs("av")

# datas: tokenizers + faster_whisper assets
datas: list[tuple[str, str]] = []
datas += collect_data_files("faster_whisper")
datas += collect_data_files("tokenizers")
datas += collect_data_files("av")


def _optional_data(path: str, dest: str) -> list[tuple[str, str]]:
    """Inclui um asset se existir; ausência de asset cosmético não quebra build."""
    return [(path, dest)] if Path(path).is_file() else []


# Assets essenciais + cosméticos opcionais. Fontes têm fallback de sistema e
# sons são opt-in, então o repositório pode ser distribuído sem binários extras.
for path, dest in (
    ("sussurro/assets/sussurro.ico", "sussurro/assets"),
    ("sussurro/assets/sussurro.png", "sussurro/assets"),
    ("sussurro/assets/chevron_down.png", "sussurro/assets"),
    ("sussurro/assets/fonts/Geist.ttf", "sussurro/assets/fonts"),
    ("sussurro/assets/fonts/GeistMono.ttf", "sussurro/assets/fonts"),
    ("sussurro/assets/sounds/start.wav", "sussurro/assets/sounds"),
    ("sussurro/assets/sounds/done.wav", "sussurro/assets/sounds"),
):
    datas += _optional_data(path, dest)

# CUDA bin dirs como datas (mantendo estrutura de pastas)
for src_dir, dest_dir in _find_nvidia_bin_dirs():
    for dll in Path(src_dir).glob("*.dll"):
        datas.append((str(dll), dest_dir))

# hidden imports do PySide6 e nvidia
hiddenimports: list[str] = []
hiddenimports += collect_submodules("sussurro")
hiddenimports += [
    "ctranslate2",
    "faster_whisper",
    "tokenizers",
    "onnxruntime",
    "huggingface_hub",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
]


a = Analysis(
    ["sussurro/__main__.py"],
    pathex=[str(Path.cwd())],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "pandas",
        "scipy",
        "IPython",
        "notebook",
        "jupyter",
        "PIL.ImageQt",
        "PyQt5",
        "PyQt6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Sussurro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="sussurro/assets/sussurro.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Sussurro",
)
