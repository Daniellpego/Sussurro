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


def test_whisper_repo_resolution() -> None:
    assert whisper_repo("large-v3-turbo") == "deepdml/faster-whisper-large-v3-turbo-ct2"
    assert whisper_repo("small") == "Systran/faster-whisper-small"


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
