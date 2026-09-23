"""Só um Sussurro por vez: o segundo clique mostra o que já está aberto."""
from __future__ import annotations

import subprocess
import sys
import uuid

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="mutex do Windows")


_FIRST = """
import sys
from PySide6.QtCore import QCoreApplication, QTimer
app = QCoreApplication([])
from sussurro.single_instance import SingleInstance
s = SingleInstance({key!r})
assert s.acquire()
s.listen(lambda: (print("shown", flush=True), app.quit()))
print("ready", flush=True)
QTimer.singleShot(10000, app.quit)
app.exec()
"""

_SECOND = """
from PySide6.QtCore import QCoreApplication
app = QCoreApplication([])
from sussurro.single_instance import SingleInstance
s = SingleInstance({key!r})
print(f"acquire={{s.acquire()}} notify={{s.notify_running()}}")
"""


def _key() -> str:
    return f"Sussurro-test-{uuid.uuid4().hex}"


def test_second_instance_is_refused_while_first_is_alive() -> None:
    from sussurro.single_instance import SingleInstance

    key = _key()
    first = SingleInstance(key)
    assert first.acquire()
    assert not SingleInstance(key).acquire()


def test_second_instance_asks_first_to_show_window() -> None:
    # dois processos, como dois cliques no atalho
    key = _key()
    first = subprocess.Popen(
        [sys.executable, "-c", _FIRST.format(key=key)],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        assert first.stdout is not None
        assert first.stdout.readline().strip() == "ready"
        second = subprocess.run(
            [sys.executable, "-c", _SECOND.format(key=key)],
            capture_output=True, text=True, timeout=30,
        )
        assert "acquire=False notify=True" in second.stdout
        out, _ = first.communicate(timeout=15)
        assert "shown" in out
    finally:
        if first.poll() is None:
            first.kill()


def test_notify_without_running_instance_returns_false() -> None:
    from sussurro.single_instance import SingleInstance

    assert not SingleInstance(_key()).notify_running(timeout_ms=200)
