from PySide6.QtCore import QCoreApplication

from sussurro.asr.whisper import _UNLOAD, WhisperWorker


def test_whisper_worker_set_model_size():
    _ = QCoreApplication.instance() or QCoreApplication([])

    worker = WhisperWorker(model_size="large-v3-turbo")
    assert worker.model_size == "large-v3-turbo"

    worker.set_model_size("small")
    assert worker.model_size == "small"

    # Verify that unload was requested (enqueued in _queue)
    item = worker._queue.get_nowait()
    assert item is _UNLOAD


def test_whisper_worker_set_model_size_unchanged():
    _ = QCoreApplication.instance() or QCoreApplication([])

    worker = WhisperWorker(model_size="large-v3-turbo")
    # Same size should not trigger unload
    worker.set_model_size("large-v3-turbo")
    assert worker._queue.empty()
