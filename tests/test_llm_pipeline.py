"""Testes do pipeline LLM sem exigir Ollama ou rede."""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from sussurro.llm import modes as modes_mod
from sussurro.llm import ollama as ollama_client
from sussurro.llm.modes import ModeStore
from sussurro.llm.worker import LLMJob, LLMResult, LLMWorker

EXPECTED_MODES = {
    "raw",
    "clean",
    "email",
    "bullets",
    "prompt",
    "code",
    "translate",
    "email_corp",
    "laudo_birads",
    "peticao_inicial",
    "humanizer",
    "segundo_cerebro",
}


def _temp_store(monkeypatch, tmp_path: Path) -> ModeStore:
    path = tmp_path / "modes.json"
    monkeypatch.setattr(modes_mod, "_store_path", lambda: path)
    return ModeStore.load()


def test_default_prompts() -> None:
    assert set(modes_mod._DEFAULT_PROMPTS) == EXPECTED_MODES
    for mode, prompt in modes_mod._DEFAULT_PROMPTS.items():
        if mode != "raw":
            assert len(prompt) > 100


def test_store_roundtrip_is_atomic(monkeypatch, tmp_path: Path) -> None:
    store = _temp_store(monkeypatch, tmp_path)
    clean = store.get("clean")
    clean.prompt = "TESTE ROUNDTRIP"
    store.update(clean)

    loaded = ModeStore.load()
    assert loaded.get("clean").prompt == "TESTE ROUNDTRIP"
    assert not (tmp_path / "modes.json.tmp").exists()


def test_unknown_mode_mutations_do_not_touch_fallback(monkeypatch, tmp_path: Path) -> None:
    store = _temp_store(monkeypatch, tmp_path)
    raw = store.get("raw")
    before = (raw.active, raw.prompt)

    try:
        store.set_active("nao-existe", False)
    except KeyError:
        pass
    else:
        raise AssertionError("set_active deveria rejeitar id inexistente")

    try:
        store.reset_prompt("nao-existe")
    except KeyError:
        pass
    else:
        raise AssertionError("reset_prompt deveria rejeitar id inexistente")

    assert store.delete("nao-existe") is False
    assert (store.get("raw").active, store.get("raw").prompt) == before


def test_llm_raw_mode_bypass(monkeypatch, tmp_path: Path) -> None:
    qt = QCoreApplication.instance() or QCoreApplication([])
    store = _temp_store(monkeypatch, tmp_path)
    worker = LLMWorker(store=store)
    result_holder: list[LLMResult] = []
    worker.done.connect(result_holder.append)
    worker.start()
    worker.submit(LLMJob(request_id=1, mode="raw", raw_text="texto puro"))

    deadline = time.time() + 3
    while time.time() < deadline and not result_holder:
        qt.processEvents()
        time.sleep(0.02)

    worker.shutdown()
    worker.wait(2000)
    assert result_holder
    assert result_holder[0].processed_text == "texto puro"
    assert result_holder[0].used_llm is False


def test_llm_offline_fallback(monkeypatch, tmp_path: Path) -> None:
    qt = QCoreApplication.instance() or QCoreApplication([])
    store = _temp_store(monkeypatch, tmp_path)
    monkeypatch.setattr(ollama_client, "is_running", lambda *a, **k: False)
    monkeypatch.setattr(ollama_client, "try_start", lambda *a, **k: False)

    worker = LLMWorker(store=store, allow_autostart=False)
    result_holder: list[LLMResult] = []
    worker.done.connect(result_holder.append)
    worker.start()
    worker.submit(LLMJob(request_id=2, mode="clean", raw_text="eh tipo um teste"))

    deadline = time.time() + 3
    while time.time() < deadline and not result_holder:
        qt.processEvents()
        time.sleep(0.02)

    worker.shutdown()
    worker.wait(2000)
    assert result_holder
    result = result_holder[0]
    assert result.used_llm is False
    assert result.reason == "offline"
    assert result.processed_text == "eh tipo um teste"
