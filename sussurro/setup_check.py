"""Detecção de hardware + pré-requisitos pro primeiro uso (tela 09).

Tudo REAL (sem placeholder): GPU via nvidia-smi, cache do Whisper via
huggingface_hub, Ollama via ping/list. Downloads rodam em QThread com progresso
real (Whisper monitorando o cache do HF; Qwen via stream do /api/pull).
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from sussurro.llm import ollama as ollama_client

# tamanho aproximado pra estimar o % do download do Whisper (GB)
_WHISPER_APPROX_GB = {
    "tiny": 0.075, "base": 0.145, "small": 0.5, "medium": 1.5,
    "large-v3": 3.1, "large-v3-turbo": 1.6,
}
_QWEN_MODEL = ollama_client.DEFAULT_MODEL


# --------------------------------------------------------------------------- GPU

def detect_gpu() -> tuple[str, int] | None:
    """(nome curto, VRAM GB) via nvidia-smi, ou None se não houver GPU NVIDIA."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=6,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    line = out.stdout.strip().splitlines()[0]
    try:
        name, mem = (x.strip() for x in line.split(","))
        gb = round(int(mem) / 1024)
    except (ValueError, IndexError):
        return None
    short = (name.replace("NVIDIA GeForce ", "")
                 .replace("NVIDIA ", "").strip())
    return short, gb


# ----------------------------------------------------------------------- Whisper

def whisper_repo(model_size: str) -> str:
    special = {
        "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    }
    return special.get(model_size, f"Systran/faster-whisper-{model_size}")


def whisper_cached(model_size: str) -> bool:
    """True se o modelo Whisper já está no cache do HuggingFace."""
    try:
        from huggingface_hub import try_to_load_from_cache
    except Exception:  # noqa: BLE001
        return False
    repo = whisper_repo(model_size)
    try:
        hit = try_to_load_from_cache(repo, "model.bin")
        return isinstance(hit, str) and Path(hit).exists()
    except Exception:  # noqa: BLE001
        return False


def _repo_cache_dir(repo: str) -> Path | None:
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
    except Exception:  # noqa: BLE001
        HF_HUB_CACHE = os.path.expanduser("~/.cache/huggingface/hub")
    folder = "models--" + repo.replace("/", "--")
    p = Path(HF_HUB_CACHE) / folder
    return p if p.exists() else None


def _dir_size_gb(path: Path) -> float:
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total / 1e9


class WhisperDownloadWorker(QThread):
    """Baixa o modelo Whisper, emitindo progresso real (GB baixados/total)."""

    progress = Signal(float, float, float)   # feito_gb, total_gb, velocidade_mbps
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, model_size: str) -> None:
        super().__init__()
        self._size = model_size
        self._cancelled = False

    def cancel(self) -> None:
        """Para de emitir e encerra a thread (o download HF daemon termina só)."""
        self._cancelled = True

    def run(self) -> None:
        repo = whisper_repo(self._size)
        total = _WHISPER_APPROX_GB.get(self._size, 3.0)
        err: list[Exception | None] = [None]
        done = threading.Event()

        def _dl() -> None:
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(repo)
            except Exception as e:  # noqa: BLE001
                err[0] = e
            finally:
                done.set()

        t = threading.Thread(target=_dl, daemon=True)
        t.start()

        last_gb, last_t = 0.0, time.monotonic()
        while not done.wait(0.5):
            if self._cancelled:
                return
            cache = _repo_cache_dir(repo)
            cur = _dir_size_gb(cache) if cache else 0.0
            now = time.monotonic()
            speed = max(0.0, (cur - last_gb) * 1000.0 / max(now - last_t, 1e-3))
            self.progress.emit(min(cur, total), total, speed)
            last_gb, last_t = cur, now

        if err[0] is not None:
            self.failed.emit(repr(err[0]))
            return
        self.progress.emit(total, total, 0.0)
        self.finished_ok.emit()


import shutil
import tempfile

# ------------------------------------------------------------------------ Espaço em Disco

def get_free_disk_space_gb(path: str | Path | None = None) -> float:
    """Retorna espaço livre em GB na unidade do sistema/usuário."""
    target = path or os.environ.get("SYSTEMDRIVE", "C:")
    try:
        usage = shutil.disk_usage(str(target))
        return usage.free / 1e9
    except OSError:
        return 0.0


# ------------------------------------------------------------------------ Ollama

OLLAMA_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
_OLLAMA_INSTALL_TIMEOUT_S = 180.0


def ollama_installed() -> bool:
    """Ollama no PATH ou rodando na API local."""
    if ollama_client.is_running():
        return True
    from shutil import which
    if which("ollama") is not None:
        return True
    # Caminho padrão do instalador no Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        standard_path = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
        if standard_path.exists():
            return True
    return False


def ollama_running() -> bool:
    return ollama_client.is_running()


def qwen_pulled() -> bool:
    models = ollama_client.list_models()
    return _QWEN_MODEL in models


class OllamaInstallWorker(QThread):
    """Baixa e executa o instalador oficial do Ollama em segundo plano."""

    progress = Signal(float, float, float)  # feito_mb, total_mb, velocidade_mbps
    status_changed = Signal(str)            # status textual da etapa
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import httpx

        # 1. Checagem de espaço em disco
        free_gb = get_free_disk_space_gb()
        if free_gb < 2.0:
            self.failed.emit(f"Espaço insuficiente em disco ({free_gb:.1f} GB livres; requer no mínimo 2.0 GB)")
            return

        self.status_changed.emit("Conectando aos servidores do Ollama…")
        installer_path = Path(tempfile.gettempdir()) / "SussurroOllamaSetup.exe"

        # 2. Download do OllamaSetup.exe
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0, verify=True) as client:
                with client.stream("GET", OLLAMA_INSTALLER_URL) as resp:
                    resp.raise_for_status()
                    total_bytes = int(resp.headers.get("content-length", 0))
                    total_mb = total_bytes / 1e6 if total_bytes else 70.0
                    downloaded_bytes = 0
                    t0 = time.monotonic()
                    last_emit_t = t0

                    with open(installer_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=65536):
                            if self._cancelled:
                                return
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            now = time.monotonic()
                            if now - last_emit_t >= 0.2:
                                speed_mbps = (downloaded_bytes / 1e6) / max(now - t0, 1e-3)
                                self.progress.emit(downloaded_bytes / 1e6, total_mb, speed_mbps)
                                self.status_changed.emit(f"Baixando Ollama ({downloaded_bytes / 1e6:.1f} / {total_mb:.1f} MB)…")
                                last_emit_t = now

            # Validação de integridade mínima (binário executável real > 10 MB)
            if not installer_path.exists() or installer_path.stat().st_size < 10 * 1024 * 1024:
                self.failed.emit("Arquivo de instalação baixado está corrompido ou incompleto.")
                try:
                    installer_path.unlink(missing_ok=True)
                except OSError:
                    pass
                return

            self.progress.emit(total_mb, total_mb, 0.0)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Falha no download do Ollama: {exc}")
            try:
                installer_path.unlink(missing_ok=True)
            except OSError:
                pass
            return

        if self._cancelled:
            try:
                installer_path.unlink(missing_ok=True)
            except OSError:
                pass
            return

        # 3. Execução do instalador
        self.status_changed.emit("Instalando Ollama silenciosamente…")
        try:
            proc = subprocess.Popen([str(installer_path), "/silent"])
            # Espera o instalador terminar (ou o serviço responder). O
            # ollama.exe aparece no disco antes de a instalação acabar, então
            # a existência do arquivo sozinha não conta como sucesso.
            t_start = time.monotonic()
            while time.monotonic() - t_start < _OLLAMA_INSTALL_TIMEOUT_S:
                if self._cancelled:
                    proc.kill()
                    return
                if ollama_running() or proc.poll() is not None:
                    break
                time.sleep(1.0)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Falha ao executar o instalador do Ollama: {exc}")
            return
        finally:
            # Limpeza do arquivo temporário de instalação
            try:
                installer_path.unlink(missing_ok=True)
            except OSError:
                pass

        # 4. Confirmação
        finished = proc.poll() == 0
        if ollama_running() or (finished and ollama_installed()):
            self.status_changed.emit("Ollama instalado com sucesso!")
            self.finished_ok.emit()
        else:
            self.failed.emit("A instalação do Ollama não terminou a tempo. "
                             "Tente de novo ou instale pelo site ollama.com.")


def pull_error_message(error: str) -> str:
    """Traduz erros do /api/pull do Ollama numa mensagem curta pro usuário."""
    low = error.lower()
    if any(k in low for k in ("dial tcp", "no such host", "connecterror",
                              "timeout", "network", "connection")):
        return "sem conexão com a internet ou com o Ollama"
    if "no space" in low or "disk" in low:
        return "espaço em disco insuficiente para o modelo"
    if "file does not exist" in low or "not found" in low:
        return "modelo não encontrado no catálogo do Ollama"
    return f"falha ao baixar o modelo: {error[:120]}"


class QwenPullWorker(QThread):
    """`ollama pull` com progresso real (stream NDJSON do /api/pull)."""

    progress = Signal(float, float)   # feito_gb, total_gb
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, model: str = _QWEN_MODEL) -> None:
        super().__init__()
        self._model = model
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import httpx
        success = False
        try:
            with httpx.stream(
                "POST", f"{ollama_client.OLLAMA_BASE}/api/pull",
                json={"name": self._model, "stream": True}, timeout=None,
            ) as resp:
                resp.raise_for_status()
                import json
                for line in resp.iter_lines():
                    if self._cancelled:
                        return
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except ValueError:
                        continue
                    if data.get("error"):
                        # ex.: sem internet, modelo inexistente, disco cheio
                        self.failed.emit(pull_error_message(str(data["error"])))
                        return
                    total = data.get("total")
                    completed = data.get("completed")
                    if total:
                        self.progress.emit(
                            (completed or 0) / 1e9, total / 1e9)
                    if data.get("status") == "success":
                        success = True
                        self.finished_ok.emit()
                        return
        except Exception as e:  # noqa: BLE001
            self.failed.emit(pull_error_message(repr(e)))
            return
        if not success:
            self.failed.emit("pull do Qwen terminou sem confirmação de sucesso")
