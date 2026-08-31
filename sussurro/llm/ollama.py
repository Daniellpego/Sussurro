"""Cliente HTTP minimal pro Ollama (localhost:11434).

API usada: POST /api/generate com `stream=false` (sincrono).
Documentacao: https://github.com/ollama/ollama/blob/main/docs/api.md
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

OLLAMA_BASE = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b-instruct-q5_K_M"
GENERATE_TIMEOUT = 90.0
PING_TIMEOUT = 1.5


@dataclass
class OllamaResult:
    text: str
    model: str
    eval_count: int = 0
    total_duration_ms: float = 0.0


class OllamaError(Exception):
    pass


def is_running(timeout: float = PING_TIMEOUT) -> bool:
    """Quick TCP check no porto 11434."""
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=timeout):
            return True
    except (TimeoutError, OSError):
        return False


def try_start(wait_s: float = 10.0) -> bool:
    """Tenta subir o Ollama sozinho (Windows: 'ollama app.exe' na bandeja;
    fallback: 'ollama serve' via PATH). Retorna True se a API respondeu.

    Não levanta janela nem rouba foco (DETACHED + CREATE_NO_WINDOW)."""
    if is_running():
        return True

    candidates: list[list[str]] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        app = Path(local) / "Programs" / "Ollama" / "ollama app.exe"
        if app.exists():
            candidates.append([str(app)])
    exe = shutil.which("ollama")
    if exe:
        candidates.append([exe, "serve"])

    for cmd in candidates:
        try:
            flags = 0
            if sys.platform == "win32":
                # DETACHED_PROCESS | CREATE_NO_WINDOW
                flags = 0x00000008 | 0x08000000
            subprocess.Popen(
                cmd,
                creationflags=flags,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            continue
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            if is_running(timeout=0.5):
                return True
            time.sleep(0.4)
    return False


def loaded_models() -> list[str]:
    """Modelos carregados AGORA na VRAM (`ollama ps`)."""
    try:
        resp = httpx.get(f"{OLLAMA_BASE}/api/ps", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return []
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def unload_model(model: str) -> bool:
    """Descarrega um modelo específico da VRAM (keep_alive=0)."""
    if not model:
        return False
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": model, "keep_alive": 0},
            timeout=10.0,
        )
        return resp.status_code < 400
    except httpx.HTTPError:
        return False


def unload_models(models: list[str] | set[str] | tuple[str, ...]) -> list[str]:
    """Descarrega somente modelos explicitamente informados e atualmente ativos."""
    loaded = set(loaded_models())
    unloaded: list[str] = []
    for model in dict.fromkeys(models):
        if model in loaded and unload_model(model):
            unloaded.append(model)
    return unloaded


def unload_all() -> None:
    """Descarrega da VRAM todo modelo carregado (keep_alive=0).

    Só descarrega o que está carregado — mandar keep_alive=0 pra um modelo
    frio faria o Ollama CARREGAR gigas pra descarregar em seguida."""
    unload_models(loaded_models())


def list_models() -> list[str]:
    """Lista modelos puxados localmente (`ollama list`)."""
    try:
        resp = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return []
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def generate(prompt: str,
             system: str | None = None,
             model: str = DEFAULT_MODEL,
             temperature: float = 0.3,
             stop: list[str] | None = None,
             keep_alive: str | int = 0) -> OllamaResult:
    """Chama /api/generate sincrono.

    keep_alive: quanto o modelo fica na VRAM depois.
    Default 0 = descarrega na hora (economia; qualidade do texto idêntica).
    Use "5m"/"30m" se for fazer vários Clean seguidos.
    """
    # Normaliza "0"/"0m" -> 0 (API do Ollama aceita int ou duração string)
    ka: str | int = keep_alive
    if ka in (0, "0", "0m", "0s", "0h"):
        ka = 0
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": ka,
        "options": {
            "temperature": temperature,
        },
    }
    if system:
        payload["system"] = system
    if stop:
        payload["options"]["stop"] = stop

    try:
        resp = httpx.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=GENERATE_TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise OllamaError(f"falha de rede ao chamar Ollama: {exc}") from exc

    if resp.status_code == 404:
        raise OllamaError(
            f"modelo '{model}' nao encontrado no Ollama. "
            f"Rode: ollama pull {model}"
        )
    if resp.status_code >= 400:
        raise OllamaError(
            f"Ollama retornou {resp.status_code}: {resp.text[:200]}"
        )

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise OllamaError(f"resposta invalida do Ollama: {exc}") from exc

    text = (data.get("response") or "").strip()
    return OllamaResult(
        text=text,
        model=model,
        eval_count=int(data.get("eval_count", 0)),
        total_duration_ms=float(data.get("total_duration", 0)) / 1e6,
    )
