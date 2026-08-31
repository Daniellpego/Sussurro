"""Importa TODOS os modulos do sussurro pra validar sintaxe + bindings.

Varre o pacote com pkgutil em vez de listar imports na mao — assim o script
nao quebra quando um simbolo e renomeado/removido numa refatoracao.
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sussurro.cuda_setup import setup_cuda_dll_path

setup_cuda_dll_path()

import sussurro

mods = sorted(m.name for m in pkgutil.walk_packages(sussurro.__path__,
                                                    "sussurro."))
fails: list[tuple[str, str]] = []
for name in mods:
    try:
        importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        fails.append((name, repr(exc)))

print(f"[{'ok' if not fails else 'FALHA'}] {len(mods)} modulos varridos")
for name, err in fails:
    print(f"     {name}: {err}")

from sussurro.llm import ollama as ollama_client

print(f"     Ollama rodando = {ollama_client.is_running()}")
sys.exit(1 if fails else 0)
