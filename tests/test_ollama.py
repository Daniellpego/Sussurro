from __future__ import annotations

from sussurro.llm import ollama


def test_unload_models_only_touches_requested_loaded_models(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(ollama, "loaded_models", lambda: ["sussurro-model", "foreign-model"])
    monkeypatch.setattr(ollama, "unload_model", lambda model: calls.append(model) or True)

    unloaded = ollama.unload_models({"sussurro-model"})
    assert unloaded == ["sussurro-model"]
    assert calls == ["sussurro-model"]
