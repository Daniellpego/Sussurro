from __future__ import annotations

from unittest import mock

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
