"""Localizacao das pastas de dados do Sussurro no Windows."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_dir() -> Path:
    """Raiz do pacote `sussurro/` — funciona em dev e no bundle PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "sussurro"
    return Path(__file__).resolve().parent.parent


def asset_path(*parts: str) -> Path:
    """Caminho de um asset empacotado (ex: asset_path('fonts', 'Inter.ttf'))."""
    return resource_dir() / "assets" / Path(*parts)


def app_data_dir() -> Path:
    """%APPDATA%\\Sussurro (cria se nao existir)."""
    base = os.environ.get("APPDATA")
    if base:
        root = Path(base) / "Sussurro"
    else:
        root = Path.home() / ".sussurro"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_text_atomic(path: Path, text: str) -> None:
    """Escreve via tmp + os.replace: um crash no meio nunca corrompe o arquivo."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def config_path() -> Path:
    return app_data_dir() / "config.toml"


def history_path() -> Path:
    return app_data_dir() / "history.json"


def log_path() -> Path:
    return app_data_dir() / "sussurro.log"


def latency_path() -> Path:
    return app_data_dir() / "latency.jsonl"
