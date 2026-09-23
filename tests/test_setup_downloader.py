from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from sussurro.setup_check import (
    OllamaInstallWorker,
    get_free_disk_space_gb,
    ollama_installed,
    whisper_cached,
    whisper_repo,
)


def test_free_disk_space_detection() -> None:
    free_gb = get_free_disk_space_gb()
    assert isinstance(free_gb, float)
    assert free_gb >= 0.0


def test_whisper_repo_matches_faster_whisper_catalog() -> None:
    """O setup precisa checar/baixar o MESMO repo que o ASR vai carregar.

    Quando divergem, o primeiro uso baixa dois modelos (3 GB para 1,5 GB de
    pesos) e whisper_cached() nunca confere, repetindo o download.
    """
    from faster_whisper.utils import _MODELS

    assert _MODELS, "catálogo do faster-whisper vazio — API mudou?"
    for size, repo in _MODELS.items():
        assert whisper_repo(size) == repo, (
            f"{size}: setup baixaria {whisper_repo(size)!r}, "
            f"mas o ASR carrega {repo!r}"
        )


def test_whisper_repo_fallback_for_unknown_size() -> None:
    assert whisper_repo("tamanho-inventado") == (
        "Systran/faster-whisper-tamanho-inventado"
    )


def test_whisper_cached_handles_missing(monkeypatch) -> None:
    # Se huggingface_hub não achar cache
    assert whisper_cached("inexistente_12345") is False


def test_ollama_install_worker_disk_check(monkeypatch) -> None:
    _ = QCoreApplication.instance() or QCoreApplication([])

    # Simula disco com apenas 0.5 GB livres
    monkeypatch.setattr("sussurro.setup_check.get_free_disk_space_gb", lambda *_: 0.5)

    worker = OllamaInstallWorker()
    failed_messages: list[str] = []
    worker.failed.connect(failed_messages.append)

    worker.run()

    assert len(failed_messages) == 1
    assert "Espaço insuficiente" in failed_messages[0]


def test_ollama_installed_fallback(monkeypatch) -> None:
    monkeypatch.setattr("sussurro.llm.ollama.is_running", lambda: False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    # Sem Ollama instalado
    monkeypatch.setenv("LOCALAPPDATA", "C:\\TempInexistente")
    assert ollama_installed() is False
