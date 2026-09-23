from __future__ import annotations

import pytest

from sussurro.audio import capture

MME, DSOUND, WASAPI = 0, 1, 2
LONG = "Microfone (Realtek(R) Audio High Definition)"

DEVICES = [
    {"name": "Microsoft Sound Mapper - Input", "hostapi": MME, "max_input_channels": 2},
    {"name": "Microfone (USB Audio Device)", "hostapi": MME, "max_input_channels": 1},
    {"name": LONG[:31], "hostapi": MME, "max_input_channels": 2},
    {"name": "Alto-falantes (Realtek)", "hostapi": MME, "max_input_channels": 0},
    {"name": "Microfone (USB Audio Device)", "hostapi": DSOUND, "max_input_channels": 1},
    {"name": "Microfone (USB Audio Device)", "hostapi": WASAPI, "max_input_channels": 1},
    {"name": LONG, "hostapi": WASAPI, "max_input_channels": 2},
]


class _FakeSoundDevice:
    def __init__(self, devices, default_input: int | None = 0) -> None:
        self._devices = devices
        self._default_input = default_input

    def query_devices(self, device=None, kind=None):
        if kind == "input":
            if self._default_input is None:
                raise ValueError("no default input")
            return self._devices[self._default_input]
        return list(self._devices)


@pytest.fixture
def fake_sd(monkeypatch):
    def _install(devices=DEVICES, default_input=0):
        fake = _FakeSoundDevice(devices, default_input)
        monkeypatch.setattr(capture, "sd", fake)
        return fake
    return _install


def test_list_shows_each_microphone_once(fake_sd) -> None:
    fake_sd()
    names = capture.list_input_devices()
    assert names == [
        "Microsoft Sound Mapper - Input",
        "Microfone (USB Audio Device)",
        LONG[:31],
    ]


def test_list_without_default_hostapi_deduplicates(fake_sd) -> None:
    fake_sd(default_input=None)
    names = capture.list_input_devices()
    assert names.count("Microfone (USB Audio Device)") == 1
    assert "Alto-falantes (Realtek)" not in names


def test_duplicate_name_resolves_to_default_hostapi_index(fake_sd) -> None:
    fake_sd()
    assert capture.resolve_input_device("Microfone (USB Audio Device)") == 1


def test_full_name_from_other_hostapi_still_resolves(fake_sd) -> None:
    fake_sd()
    # nome completo salvo por uma versão antiga, que listava o WASAPI
    assert capture.resolve_input_device(LONG) == 6


def test_truncated_name_matches_full_device(fake_sd) -> None:
    fake_sd(devices=[d for d in DEVICES if d["hostapi"] == WASAPI], default_input=0)
    assert capture.resolve_input_device(LONG[:31]) == 1


def test_default_and_index_pass_through(fake_sd) -> None:
    fake_sd()
    assert capture.resolve_input_device(None) is None
    assert capture.resolve_input_device("") is None
    assert capture.resolve_input_device(3) == 3


def test_missing_microphone_raises(fake_sd) -> None:
    fake_sd()
    with pytest.raises(ValueError, match="não encontrado"):
        capture.resolve_input_device("Headset que foi desconectado")


def test_recorder_opens_stream_with_resolved_index(fake_sd, monkeypatch) -> None:
    fake = fake_sd()
    opened = {}

    class _Stream:
        def __init__(self, **kwargs) -> None:
            opened.update(kwargs)
            self._callback = kwargs["callback"]

        def start(self) -> None:
            import numpy as np
            self._callback(np.zeros((capture.BLOCK_SIZE, 1), dtype=np.float32),
                           0, None, None)

        def stop(self) -> None:
            pass

        def close(self) -> None:
            pass

    fake.InputStream = _Stream
    recorder = capture.Recorder(device="Microfone (USB Audio Device)")
    recorder.prepare(timeout=0.5)
    assert opened["device"] == 1
    recorder.close()
