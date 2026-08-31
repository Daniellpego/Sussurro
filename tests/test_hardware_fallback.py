from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
from PySide6.QtCore import QCoreApplication

from sussurro.asr.whisper import TranscriptionJob, TranscriptionResult, WhisperWorker


def test_whisper_worker_graceful_cuda_fallback(monkeypatch) -> None:
    # Garante QCoreApplication se necessário
    _ = QCoreApplication.instance() or QCoreApplication([])

    worker = WhisperWorker(model_size="large-v3-turbo", device="cuda")
    worker._active_device = "cuda"

    mock_cuda_model = MagicMock()
    # Simula falha de CUDA OOM na primeira chamada
    mock_cuda_model.transcribe.side_effect = RuntimeError("CUDA out of memory")
    worker._model = mock_cuda_model

    mock_cpu_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 1.0
    mock_segment.text = "transcrição recuperada em CPU"
    mock_info = MagicMock()
    mock_info.language = "pt"
    mock_cpu_model.transcribe.return_value = ([mock_segment], mock_info)

    def fake_load_model():
        worker._model = mock_cpu_model
        worker._active_device = "cpu"
        return True

    monkeypatch.setattr(worker, "_load_model", fake_load_model)

    done_results: list[TranscriptionResult] = []
    worker.done.connect(done_results.append)

    audio = np.zeros(16_000, dtype=np.float32)
    job = TranscriptionJob(audio=audio, mode="raw", request_id=1)

    worker._handle(job)

    assert len(done_results) == 1
    assert done_results[0].text == "transcrição recuperada em CPU"
    assert done_results[0].device == "cpu"
