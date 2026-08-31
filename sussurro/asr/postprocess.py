"""Pós-processamento leve da saída do Whisper (sem LLM, ~0 ms).

Objetivo: consertar o que o modelo "quase acerta" — espaços, casing de termos
do dicionário, pontuação colada, e artefatos comuns de ditado PT-BR — sem
reescrever o sentido. Nada aqui deve inventar conteúdo.
"""
from __future__ import annotations

import re
import unicodedata

# Artefatos frequentes do Whisper em PT-BR / ditado curto.
# Só substituições seguras (alto recall com baixo falso-positivo).
_COMMON_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    # pontuação com espaço antes (Whisper às vezes emite " ,")
    (re.compile(r"\s+([,.;:!?…])"), r"\1"),
    # espaço depois de abertura
    (re.compile(r"([(\[\"“«])\s+"), r"\1"),
    # espaço antes de fechamento
    (re.compile(r"\s+([)\]\"”»])"), r"\1"),
    # reticências quebradas
    (re.compile(r"\.\.\.+"), "…"),
    # múltiplos espaços / tabs
    (re.compile(r"[ \t]{2,}"), " "),
    # espaço no início de linha após \n
    (re.compile(r"\n[ \t]+"), "\n"),
    (re.compile(r"[ \t]+\n"), "\n"),
    # 3+ quebras -> 2
    (re.compile(r"\n{3,}"), "\n\n"),
)

# Capitaliza a 1ª letra de cada sentença (após .!?… ou início).
_SENTENCE_START = re.compile(
    r"(^|[.!?…]\s+|[\n]\s*)([a-zà-ú])",
    re.UNICODE,
)


def _fold(s: str) -> str:
    """minúsculas sem acento — pra matching de dicionário tolerante."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def apply_dictionary_casing(text: str, terms: list[str]) -> str:
    """Força a grafia canônica dos termos do dicionário no texto.

    Matching case-insensitive e sem acento no miolo da palavra. Ex.: se o
    dicionário tem "PySide6" e o Whisper escreveu "pyside6" ou "Pyside 6"
    (variante sem espaço já coberta; com espaço só se o termo tiver espaço).
    """
    if not text or not terms:
        return text

    # mais longos primeiro pra não corromper substrings (GitHub antes de Git)
    ordered = sorted({t.strip() for t in terms if t and t.strip()},
                     key=len, reverse=True)
    for term in ordered:
        # palavra inteira (limites unicode-aware)
        # tenta match exato case-insensitive primeiro
        pat = re.compile(
            r"(?<!\w)" + re.escape(term) + r"(?!\w)",
            re.IGNORECASE,
        )
        if pat.search(text):
            text = pat.sub(term, text)
            continue

        # variante sem espaços/hífens se o termo for camelCase/PascalCase
        # (ex.: termo "PySide6", whisper "py side 6" — raro; skip se curto)
        compact = re.sub(r"[\s\-_]+", "", term)
        if len(compact) >= 4 and compact != term:
            # match da forma "p y s i d e 6" não; só se whisper juntou errado
            pat2 = re.compile(
                r"(?<!\w)" + re.escape(compact) + r"(?!\w)",
                re.IGNORECASE,
            )
            text = pat2.sub(term, text)

        # matching por forma "dobrada" (sem acento) — só se o termo tem acento
        # ou o texto pode ter errado o acento do termo
        folded_term = _fold(term)
        if folded_term != term.lower():
            # varre tokens e troca se o fold bater
            def _repl_token(m: re.Match[str], _t=term, _ft=folded_term) -> str:
                tok = m.group(0)
                return _t if _fold(tok) == _ft else tok

            text = re.sub(r"\w+", _repl_token, text, flags=re.UNICODE)

    return text


def should_capitalize_start(preceding_char: str | None) -> bool:
    """Verifica se o início do texto ditado deve ser capitalizado com base no caractere anterior."""
    if not preceding_char:
        return True
    c = preceding_char.rstrip()
    if not c:
        return True
    last = c[-1]
    # Se o caractere anterior for pontuação terminal de sentença, capitaliza
    if last in ".!?…\n":
        return True
    # Se for vírgula, dois pontos, ponto e vírgula, traço, barra, letra ou dígito -> continua em minúscula
    if last in ",;:/-" or last.isalnum():
        return False
    return True


def capitalize_sentences(text: str, *, capitalize_first: bool = True) -> str:
    """Capitaliza início de sentença sem tocar no miolo (preserva iPhone etc.)."""
    if not text:
        return text

    if not capitalize_first:
        # Capitaliza apenas sentenças internas (após .!?… ou \n), sem forçar o início absoluto
        internal_start = re.compile(r"([.!?…]\s+|[\n]\s*)([a-zà-ú])", re.UNICODE)
        return internal_start.sub(lambda m: m.group(1) + m.group(2).upper(), text)

    def _up(m: re.Match[str]) -> str:
        return m.group(1) + m.group(2).upper()

    return _SENTENCE_START.sub(_up, text)


def cleanup_transcript(text: str) -> str:
    """Limpeza determinística — espaços, pontuação colada, reticências."""
    if not text:
        return text
    text = text.strip()
    for pat, repl in _COMMON_FIXES:
        text = pat.sub(repl, text)
    return text.strip()


def apply_macros(text: str, macros: dict[str, str]) -> str:
    """Aplica substituições acústico-textuais ordenadas por comprimento."""
    if not text or not macros:
        return text
    ordered = sorted(macros.items(), key=lambda kv: len(kv[0]), reverse=True)
    for trig, repl in ordered:
        pat = re.compile(r"(?<!\w)" + re.escape(trig) + r"(?!\w)", re.IGNORECASE)
        text = pat.sub(repl, text)
    return text


def postprocess(
    text: str,
    *,
    terms: list[str] | None = None,
    macros: dict[str, str] | None = None,
    capitalize: bool = True,
    preceding_char: str | None = None,
) -> str:
    """Pipeline completo pós-ASR (antes de comandos de voz / LLM)."""
    if not text:
        return text
    text = cleanup_transcript(text)
    if macros:
        text = apply_macros(text, macros)
        text = cleanup_transcript(text)
    if terms:
        text = apply_dictionary_casing(text, terms)
        text = cleanup_transcript(text)
    if capitalize:
        cap_first = should_capitalize_start(preceding_char)
        text = capitalize_sentences(text, capitalize_first=cap_first)
    return text.strip()
