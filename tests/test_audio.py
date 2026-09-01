from __future__ import annotations

import time
from unittest import mock

import numpy as np
import pytest

from sussurro.audio import capture


def test_recorder_recovers_when_stream_start_fails(monkeypatch) -> None:
    stream = mock.Mock()
    stream.start.side_effect = RuntimeError("device busy")
    monkeypatch.setattr(capture.sd, "InputStream", lambda **_: stream)

    recorder = capture.Recorder()
    with pytest.raises(RuntimeError, match="device busy"):
        recorder.start()

    assert recorder.is_recording is False
    stream.close.assert_called_once()


class _LiveStream:
    def __init__(self, callback) -> None:
        self.callback = callback
        self.starts = 0
        self.closed = False

    def start(self) -> None:
        self.starts += 1
        self.callback(np.ones((capture.BLOCK_SIZE, 1), dtype=np.float32), 0, None, None)

    def stop(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


def test_preopened_stream_is_ready_within_50ms(monkeypatch) -> None:
    streams: list[_LiveStream] = []

    def factory(**kwargs):
        stream = _LiveStream(kwargs["callback"])
        streams.append(stream)
        return stream

    monkeypatch.setattr(capture.sd, "InputStream", factory)
    first_frames: list[float] = []
    recorder = capture.Recorder(on_first_frame=first_frames.append)
    recorder.prepare()

    hotkey_down = time.perf_counter()
    ready = recorder.start()
    streams[0].callback(
        np.ones((capture.BLOCK_SIZE, 1), dtype=np.float32), 0, None, None
    )

    assert (ready - hotkey_down) * 1000 < 50
    assert (first_frames[0] - hotkey_down) * 1000 < 50
    assert streams[0].starts == 1
    assert recorder.snapshot().size >= capture.BLOCK_SIZE * 2
    recorder.stop()
    recorder.close()
    assert streams[0].closed
