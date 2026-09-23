from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from sussurro.transcribe_file import _format_time
from sussurro.ui.window import FileTranscriptionWorker, _DropZoneCard


def test_format_time():
    assert _format_time(0.0) == "00:00"
    assert _format_time(65.0) == "01:05"
    assert _format_time(3605.0) == "60:05"


def test_drop_zone_card_build():
    _ = QApplication.instance() or QApplication([])
    card = _DropZoneCard()
    assert card.acceptDrops()
    card.set_active(True)
    assert card._active
    card.set_status("Processando...", "Quase pronto")
    assert card._lbl_title.text() == "Processando..."


def test_file_transcription_worker_init():
    _ = QCoreApplication.instance() or QCoreApplication([])
    worker = FileTranscriptionWorker(Path("dummy.mp3"), model_size="small")
    assert worker._audio_path.name == "dummy.mp3"
    assert worker._model_size == "small"
