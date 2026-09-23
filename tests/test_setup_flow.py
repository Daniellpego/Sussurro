"""Tela de configuração inicial: sem becos sem saída quando algo falha."""
from __future__ import annotations

import contextlib
import json

import pytest

from sussurro import setup_check


class _FakeWorker:
    instances: list[_FakeWorker] = []

    def __init__(self, *args, **kwargs) -> None:
        from PySide6.QtCore import QObject, Signal

        class _Signals(QObject):
            progress = Signal(float, float, float)
            finished_ok = Signal()
            failed = Signal(str)

        self._signals = _Signals()
        self.progress = self._signals.progress
        self.finished_ok = self._signals.finished_ok
        self.failed = self._signals.failed
        self.started = False
        type(self).instances.append(self)

    def start(self) -> None:
        self.started = True

    def isRunning(self) -> bool:  # noqa: N802
        return False


@pytest.fixture
def window(qt_app, monkeypatch, tmp_path):
    from sussurro.storage import paths
    monkeypatch.setattr(paths, "app_data_dir", lambda: tmp_path)
    from sussurro.storage.config import Config
    from sussurro.ui.setup_ui import SetupWindow

    _FakeWorker.instances = []
    monkeypatch.setattr(setup_check, "WhisperDownloadWorker", _FakeWorker)
    monkeypatch.setattr(setup_check, "QwenPullWorker", _FakeWorker)
    win = SetupWindow(Config())
    yield win
    win.close()


def test_whisper_failure_offers_retry(window) -> None:
    window._start_whisper_download()
    first = _FakeWorker.instances[-1]
    first.failed.emit("ConnectError")
    assert not window._wh_btn.isHidden()
    assert "falhou" in window._wh_status.text()

    window._wh_btn.click()
    assert _FakeWorker.instances[-1] is not first
    assert _FakeWorker.instances[-1].started
    assert window._wh_btn.isHidden()


def test_qwen_button_starts_a_single_download(window, monkeypatch) -> None:
    monkeypatch.setattr(setup_check, "qwen_pulled", lambda: False)
    for _ in range(3):  # o estado do Ollama é atualizado várias vezes
        window._setup_qwen(enabled=True)
    window._qw_btn.click()
    assert len(_FakeWorker.instances) == 1


def test_qwen_failure_shows_reason_and_retry(window, monkeypatch) -> None:
    monkeypatch.setattr(setup_check, "qwen_pulled", lambda: False)
    window._setup_qwen(enabled=True)
    window._qw_btn.click()
    _FakeWorker.instances[-1].failed.emit("sem conexão com a internet ou com o Ollama")
    assert "sem conexão" in window._qw_status.text()
    assert window._qw_btn.text() == "Tentar de novo"
    assert not window._qw_btn.isHidden()


def test_installed_but_stopped_ollama_can_be_started(window, monkeypatch) -> None:
    monkeypatch.setattr(setup_check, "ollama_running", lambda: False)
    monkeypatch.setattr(setup_check, "ollama_installed", lambda: True)
    window._refresh_ollama()
    assert window._ol_btn.text() == "Iniciar Ollama"
    assert not window._ol_btn.isHidden()
    assert window._ol_action == window._start_ollama


# ------------------------------------------------------------ /api/pull

@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ("pull model manifest: dial tcp: lookup registry.ollama.ai: no such host",
         "sem conexão"),
        ("write /models/blobs: no space left on device", "espaço em disco"),
        ("pull model manifest: file does not exist", "não encontrado"),
    ],
)
def test_pull_errors_become_readable(error: str, expected: str) -> None:
    assert expected in setup_check.pull_error_message(error)


def test_pull_worker_reports_error_lines(qt_app, monkeypatch) -> None:
    import httpx

    lines = [
        json.dumps({"status": "pulling manifest"}),
        json.dumps({"error": "pull model manifest: dial tcp: i/o timeout"}),
    ]

    class _Resp:
        def raise_for_status(self) -> None:
            pass

        def iter_lines(self):
            return iter(lines)

    monkeypatch.setattr(httpx, "stream",
                        lambda *a, **k: contextlib.nullcontext(_Resp()))
    worker = setup_check.QwenPullWorker()
    failures: list[str] = []
    successes: list[bool] = []
    worker.failed.connect(failures.append)
    worker.finished_ok.connect(lambda: successes.append(True))
    worker.run()
    assert failures == ["sem conexão com a internet ou com o Ollama"]
    assert successes == []
