from __future__ import annotations

from sussurro import setup_check


def test_qwen_requires_exact_expected_tag(monkeypatch) -> None:
    monkeypatch.setattr(
        setup_check.ollama_client,
        "list_models",
        lambda: ["qwen2.5:3b", "other:latest"],
    )
    assert setup_check.qwen_pulled() is False

    monkeypatch.setattr(
        setup_check.ollama_client,
        "list_models",
        lambda: [setup_check._QWEN_MODEL],
    )
    assert setup_check.qwen_pulled() is True
