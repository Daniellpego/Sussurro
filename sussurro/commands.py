"""Comandos de voz — converte frases ditadas em formatação.

Ex.: "olá mundo nova linha tudo bem" -> "olá mundo\ntudo bem".

Foco em comandos SEGUROS (multi-palavra, raros como texto literal no meio da
fala) pra minimizar falso-positivo: quebras de linha/parágrafo e pontuação por
extenso. Aplicado ao texto do Whisper ANTES do LLM (pra os modos com IA
preservarem a estrutura). PT-BR + alguns equivalentes em inglês.
"""
from __future__ import annotations

import re

# frase ditada -> substituição. (sem acento e com acento; case-insensitive)
_BREAKS = {
    "nova linha": "\n",
    "quebra de linha": "\n",
    "new line": "\n",
    "novo paragrafo": "\n\n",
    "novo parágrafo": "\n\n",
    "new paragraph": "\n\n",
}

# pontuação de fim: sem espaço antes, espaço depois
# Frases multi-palavra primeiro (evitam falso-positivo de "ponto"/"vírgula"
# isolados no meio de frase real — esses singles vêm depois, mais curtos).
_PUNCT = {
    "ponto de interrogacao": "?",
    "ponto de interrogação": "?",
    "ponto de exclamacao": "!",
    "ponto de exclamação": "!",
    "ponto e virgula": ";",
    "ponto e vírgula": ";",
    "ponto final": ".",
    "dois pontos": ":",
    "reticencias": "…",
    "reticências": "…",
    # singles — alto valor em ditado; risco de FP aceitável (raro em prosa)
    "virgula": ",",
    "vírgula": ",",
    "interrogacao": "?",
    "interrogação": "?",
    "exclamacao": "!",
    "exclamação": "!",
}

# abre: espaço antes, sem espaço depois (cola na próxima palavra)
_OPEN = {
    "abre aspas": '"',
    "abre parenteses": "(",
    "abre parênteses": "(",
}

# fecha: sem espaço antes, espaço depois
_CLOSE = {
    "fecha aspas": '"',
    "fecha parenteses": ")",
    "fecha parênteses": ")",
}


def _boundary(phrase: str) -> str:
    # limites que respeitam acentos (\w em modo unicode inclui acentuadas)
    return r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"


def apply_commands(text: str, enabled: bool = True) -> str:
    if not enabled or not text:
        return text

    # quebras: comem pontuação/espaço ao redor pra não sobrar ", \n" etc.
    for phrase, repl in sorted(_BREAKS.items(), key=lambda kv: -len(kv[0])):
        pat = r"\s*[,;.]?\s*" + _boundary(phrase) + r"\s*[,;.]?\s*"
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    # pontuação de fim: sem espaço antes, espaço depois
    for phrase, repl in sorted(_PUNCT.items(), key=lambda kv: -len(kv[0])):
        pat = r"\s*[,;.!?]?\s*" + _boundary(phrase) + r"\s*[,;.!?]?\s*"
        text = re.sub(pat, repl + " ", text, flags=re.IGNORECASE)

    # abre aspas/parênteses: espaço antes, cola na próxima palavra
    for phrase, repl in sorted(_OPEN.items(), key=lambda kv: -len(kv[0])):
        pat = r"\s*" + _boundary(phrase) + r"\s*"
        text = re.sub(pat, " " + repl, text, flags=re.IGNORECASE)

    # fecha aspas/parênteses: sem espaço antes, espaço depois
    for phrase, repl in sorted(_CLOSE.items(), key=lambda kv: -len(kv[0])):
        pat = r"\s*" + _boundary(phrase) + r"\s*"
        text = re.sub(pat, repl + " ", text, flags=re.IGNORECASE)

    # limpeza geral
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?…])", r"\1", text)
    return text.strip()
