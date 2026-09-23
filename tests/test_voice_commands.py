from __future__ import annotations

import pytest

from sussurro.asr.postprocess import postprocess
from sussurro.commands import apply_commands


def _dictate(text: str) -> str:
    """Mesmo encadeamento do app: pós-processamento e depois comandos."""
    return apply_commands(postprocess(text), capitalize=True)


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("olá vírgula mundo ponto final fim", "Olá, mundo. Fim"),
        ("tudo bem ponto de interrogação", "Tudo bem?"),
        ("use ponto e vírgula aqui", "Use; aqui"),
        ("os itens são dois pontos arroz e feijão", "Os itens são: arroz e feijão"),
        ("ele disse abre aspas oi fecha aspas e saiu", 'Ele disse "oi" e saiu'),
        ("primeira frase novo parágrafo segunda frase", "Primeira frase\n\nSegunda frase"),
    ],
)
def test_spoken_commands_become_formatting(spoken: str, expected: str) -> None:
    assert _dictate(spoken) == expected


@pytest.mark.parametrize(
    "sentence",
    [
        "Ganhei dois pontos no jogo.",
        "Ganhei dois pontos",
        "Faltam dois pontos para vencer",
        "Subiu dois pontos percentuais",
        "A vírgula está no lugar errado.",
        "Chegamos ao ponto final da conversa.",
        "Vamos colocar um ponto final nisso.",
        "O ponto e vírgula é raro.",
        "Criamos uma nova linha de produtos.",
        "Ele escreveu um novo parágrafo.",
        "Faltou uma interrogação no título.",
    ],
)
def test_ordinary_words_are_not_commands(sentence: str) -> None:
    assert _dictate(sentence) == sentence


def test_sentences_started_by_commands_are_capitalized() -> None:
    out = _dictate(
        "olá vírgula tudo bem ponto final nova linha obrigado ponto final agora sim"
    )
    assert out == "Olá, tudo bem.\nObrigado. Agora sim"


def test_capitalization_is_optional() -> None:
    out = apply_commands("tudo bem ponto final obrigado", capitalize=False)
    assert out == "tudo bem. obrigado"


def test_line_break_survives_following_punctuation_command() -> None:
    assert _dictate("pergunta ponto de interrogação nova linha resposta") == (
        "Pergunta?\nResposta"
    )


def test_disabled_commands_leave_text_untouched() -> None:
    assert apply_commands("olá vírgula mundo", enabled=False) == "olá vírgula mundo"
