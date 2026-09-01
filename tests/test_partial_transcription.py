from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from sussurro.asr.whisper import PartialTranscriptionJob, WhisperWorker


class _Model:
    def transcribe(self, audio, **kwargs):
        del audio, kwargs
        return iter([SimpleNamespace(text=" texto parcial")]), SimpleNamespace()


def test_partial_transcription_emits_hud_hypothesis_only() -> None:
    worker = WhisperWorker()
    worker._model = _Model()
    emitted: list[tuple[int, str]] = []
    worker.partial.connect(lambda request_id, text: emitted.append((request_id, text)))
    worker._handle_partial(PartialTranscriptionJob(np.ones(16_000), 11))
    assert emitted == [(11, "texto parcial")]


def test_partial_transcription_updates_for_short_and_long_audio() -> None:
    worker = WhisperWorker()
    worker._model = _Model()
    emitted: list[tuple[int, str]] = []
    worker.partial.connect(lambda request_id, text: emitted.append((request_id, text)))

    worker._handle_partial(PartialTranscriptionJob(np.ones(5 * 16_000), 5))
    worker._handle_partial(PartialTranscriptionJob(np.ones(30 * 16_000), 30))

    assert [request_id for request_id, _ in emitted] == [5, 30]
