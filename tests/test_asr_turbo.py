from __future__ import annotations

from sussurro.asr.whisper import WhisperWorker, resolve_preset
from sussurro.storage.config import Config


def test_presets_default_to_large_v3_turbo_int8() -> None:
    quality = resolve_preset("quality")
    assert quality["model_size"] == "large-v3-turbo"
    assert quality["compute_type"] == "int8_float16"

    balanced = resolve_preset("balanced")
    assert balanced["model_size"] == "large-v3-turbo"

    light = resolve_preset("light")
    assert light["model_size"] == "large-v3-turbo"
    assert light["compute_type"] == "int8"


def test_config_defaults_turbo() -> None:
    cfg = Config()
    assert cfg.model_size == "large-v3-turbo"
    assert cfg.compute_type == "int8"
    assert cfg.auto_capitalization is True


def test_whisper_worker_defaults() -> None:
    worker = WhisperWorker()
    assert worker._model_size == "large-v3-turbo"
    assert worker._quality_preset == "quality"
