from __future__ import annotations

from sussurro.asr.postprocess import (
    apply_macros,
    capitalize_sentences,
    postprocess,
    should_capitalize_start,
)


def test_should_capitalize_start() -> None:
    assert should_capitalize_start(None) is True
    assert should_capitalize_start("") is True
    assert should_capitalize_start(".") is True
    assert should_capitalize_start("!\n") is True
    assert should_capitalize_start("?") is True

    # Continuação de palavra ou pontuação de continuidade -> False
    assert should_capitalize_start("a") is False
    assert should_capitalize_start("texto,") is False
    assert should_capitalize_start(":") is False
    assert should_capitalize_start("123") is False


def test_capitalize_sentences_options() -> None:
    text = "olá mundo. tudo bem? sim."
    assert capitalize_sentences(text, capitalize_first=True) == "Olá mundo. Tudo bem? Sim."
    assert capitalize_sentences(text, capitalize_first=False) == "olá mundo. Tudo bem? Sim."


def test_postprocess_semantic_capitalization() -> None:
    raw = "continuação da frase anterior. nova ideia."
    res_lower = postprocess(raw, preceding_char="vírgula,", capitalize=True)
    assert res_lower.startswith("continuação da frase anterior. Nova ideia.")

    res_upper = postprocess(raw, preceding_char=".", capitalize=True)
    assert res_upper.startswith("Continuação da frase anterior. Nova ideia.")

    res_nocap = postprocess(raw, capitalize=False)
    assert res_nocap == "continuação da frase anterior. nova ideia."


def test_postprocess_with_macros() -> None:
    macros = {
        "esse tê efe": "STF",
        "ponto com": ".com",
    }
    raw = "decisão do esse tê efe no site ponto com"
    out = apply_macros(raw, macros)
    assert out == "decisão do STF no site .com"
