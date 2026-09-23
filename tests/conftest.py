"""Configuração comum dos testes."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qt_app():
    """Um QApplication para a sessão inteira.

    Sem isso, um teste que cria só um QCoreApplication impediria os testes
    de widgets que rodassem depois dele.
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from sussurro.ui import fonts
    fonts.load_fonts()
    return app
