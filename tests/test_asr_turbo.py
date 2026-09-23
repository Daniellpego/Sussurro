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


def _worker_with_unload_counter(**kwargs) -> tuple[WhisperWorker, list[int]]:
    worker = WhisperWorker(**kwargs)
    calls: list[int] = []
    worker.request_unload = lambda: calls.append(1)  # type: ignore[method-assign]
    return worker, calls


def test_configure_keeps_model_loaded_when_nothing_changed() -> None:
    cfg = Config()
    worker, unloads = _worker_with_unload_counter(
        model_size=cfg.model_size, compute_type=cfg.compute_type,
        quality_preset=cfg.quality_preset,
    )
    for preset in ("quality", "balanced", "light", "quality"):
        assert worker.configure(model_size=cfg.model_size,
                                compute_type=cfg.compute_type,
                                quality_preset=preset) is False
    assert unloads == []
    assert worker._beam_size == resolve_preset("quality")["beam_size"]


def test_configure_ignores_previous_device_fallback() -> None:
    worker, unloads = _worker_with_unload_counter(compute_type="int8_float16")
    # simula o fallback que _load_model grava depois de a GPU falhar
    worker._device = "cpu"
    worker._compute_type = "int8"
    assert worker.configure(model_size="large-v3-turbo",
                            compute_type="int8_float16",
                            quality_preset="quality") is False
    assert unloads == []


def test_configure_reloads_when_model_changes() -> None:
    worker, unloads = _worker_with_unload_counter(compute_type="int8")
    worker._device = "cpu"  # fallback anterior
    assert worker.configure(model_size="small", compute_type="int8",
                            quality_preset="quality") is True
    assert unloads == [1]
    assert worker._model_size == "small"
    assert worker._device == "cuda"  # volta a tentar o dispositivo pedido
    # o mesmo pedido de novo não recarrega outra vez
    assert worker.configure(model_size="small", compute_type="int8",
                            quality_preset="light") is False
    assert unloads == [1]
