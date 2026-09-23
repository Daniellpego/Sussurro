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
    # singles — alto valor em ditado; usos como substantivo ("a vírgula")
    # ficam como texto graças a _NOUN_CONTEXT
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


# Palavras que, logo antes da expressão, indicam uso como substantivo e não
# como comando: "a vírgula está errada", "chegamos ao ponto final",
# "criamos uma nova linha de produtos", "os dois pontos do placar".
_NOUN_CONTEXT = frozenset({
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "ao", "aos", "à", "às", "do", "da", "dos", "das",
    "no", "na", "nos", "nas", "pelo", "pela", "pelos", "pelas",
    "num", "numa", "de", "em", "com", "sem", "por",
    "este", "esta", "esse", "essa", "aquele", "aquela",
    "neste", "nesta", "nesse", "nessa", "naquele", "naquela",
    "deste", "desta", "desse", "dessa", "daquele", "daquela",
    "meu", "minha", "seu", "sua", "nosso", "nossa", "teu", "tua",
    "cada", "outro", "outra", "mesmo", "mesma", "qualquer",
    "primeiro", "primeira", "último", "última", "ultimo", "ultima",
    "mais", "menos", "só", "so", "apenas", "quase", "até", "ate",
})

# "dois pontos" também é quantidade ("ganhei dois pontos no jogo"). Nesses
# casos a expressão costuma terminar a frase ou vir seguida de uma destas
# palavras; aí fica como texto.
_QUANTITY_PHRASES = frozenset({"dois pontos"})
_QUANTITY_FOLLOWERS = frozenset({
    "de", "do", "da", "dos", "das", "no", "na", "nos", "nas", "em",
    "a", "o", "ao", "à", "para", "pra", "por", "pelo", "pela", "com",
    "sem", "e", "ou", "mas", "que", "percentuais", "percentual",
    "hoje", "ontem", "amanhã", "amanha", "agora", "também", "tambem",
    "já", "ja", "só", "so", "apenas", "atrás", "atras", "acima", "abaixo",
})


def _alternation(phrases) -> str:
    # mais longas primeiro: "ponto e vírgula" ganha de "vírgula" na mesma posição
    ordered = sorted(phrases, key=len, reverse=True)
    body = "|".join(re.escape(p) for p in ordered)
    # limites que respeitam acentos (\w em modo unicode inclui acentuadas)
    return r"(?<!\w)(?P<cmd>" + body + r")(?!\w)"


def _is_literal(m: re.Match[str]) -> bool:
    """True quando a expressão casada é texto comum, não um comando."""
    source = m.string
    pre = m.group("pre")
    if not re.search(r"[,;.!?]", pre):
        prev = re.search(r"(\w+)$", source[: m.start()])
        if prev and prev.group(1).lower() in _NOUN_CONTEXT:
            return True
    if m.group("cmd").lower() in _QUANTITY_PHRASES:
        if re.search(r"[.!?]", m.group("post")):
            return True
        nxt = re.match(r"(\w+)", source[m.end():])
        if not nxt or nxt.group(1).lower() in _QUANTITY_FOLLOWERS:
            return True
    return False


def _sub_commands(text: str, table: dict[str, str], edge: str, fmt) -> str:
    """Troca cada comando da tabela numa única varredura.

    Uma varredura só evita que a parte curta de uma expressão mantida como
    texto (o "vírgula" de "o ponto e vírgula") seja convertida depois.
    """
    pattern = re.compile(
        r"(?P<pre>" + edge + r")" + _alternation(table) + r"(?P<post>" + edge + r")",
        re.IGNORECASE,
    )

    def _repl(m: re.Match[str]) -> str:
        if _is_literal(m):
            return m.group(0)
        return fmt(table[m.group("cmd").lower()])

    return pattern.sub(_repl, text)


def apply_commands(text: str, enabled: bool = True, *, capitalize: bool = False) -> str:
    """Converte comandos falados em formatação.

    Com ``capitalize=True``, as frases iniciadas por um comando ("ponto final",
    "nova linha") também ganham maiúscula, já que a capitalização do
    pós-processamento roda antes de os comandos virarem pontuação.
    """
    if not enabled or not text:
        return text

    # quebras: comem pontuação/espaço ao redor pra não sobrar ", \n" etc.
    text = _sub_commands(text, _BREAKS, r"\s*[,;.]?\s*", lambda r: r)

    # pontuação de fim: sem espaço antes, espaço depois. Daqui em diante as
    # bordas só comem espaço e tab, pra não apagar as quebras já inseridas.
    text = _sub_commands(text, _PUNCT, r"[ \t]*[,;.!?]?[ \t]*", lambda r: r + " ")

    # abre aspas/parênteses: espaço antes, cola na próxima palavra
    text = _sub_commands(text, _OPEN, r"[ \t]*", lambda r: " " + r)

    # fecha aspas/parênteses: sem espaço antes, espaço depois
    text = _sub_commands(text, _CLOSE, r"[ \t]*", lambda r: r + " ")

    # limpeza geral
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?…])", r"\1", text)
    text = text.strip()

    if capitalize:
        from sussurro.asr.postprocess import capitalize_sentences
        text = capitalize_sentences(text, capitalize_first=False)
    return text
