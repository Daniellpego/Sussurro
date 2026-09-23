"""Dicionário do usuário — termos/nomes/jargão que enviesam o Whisper.

Duas alavancas no faster-whisper:
1. `hotwords` — bias direto de decodificação nos termos (API nativa).
2. `initial_prompt` — prosa de estilo (acentuação PT-BR + code-switching).

No primeiro boot sem arquivo, semeia termos comuns de dev/PT.
Sugestões: observa transcricões e propõe termos conhecidos ainda não
adicionados (persistidos em suggestions.json).
"""
from __future__ import annotations

import json
import re
import unicodedata

from sussurro.storage.paths import app_data_dir, backup_corrupt, write_text_atomic

_MAX_TERMS = 80
_MAX_PROMPT_CHARS = 800
_MAX_HOTWORDS_CHARS = 400
_MAX_SUGGESTIONS = 40

_STYLE_PROMPT = (
    "Transcrição de ditado em português brasileiro. "
    "Use acentuação correta (você, não, é, até, também, está, horário). "
    "Pontuação natural. "
    "Preserve nomes próprios, marcas e termos técnicos em inglês exatamente "
    "como o falante usou (API, Python, GitHub, Claude, Ollama, refactor). "
    "Não traduza jargão técnico."
)

# Semente de 1º uso — jargão que o Whisper PT-BR costuma errar a grafia.
SEED_TERMS: tuple[str, ...] = (
    # IA / produtos
    "Claude", "ChatGPT", "Ollama", "Whisper", "OpenAI", "Anthropic",
    "Gemini", "Copilot", "Sussurro",
    # dev geral
    "Python", "JavaScript", "TypeScript", "PySide6", "Qt", "React",
    "Next.js", "Node.js", "GitHub", "Git", "Docker", "Kubernetes",
    "API", "JSON", "HTTP", "SQL", "PostgreSQL", "Redis",
    "VS Code", "Cursor", "PowerShell", "Windows Terminal",
    # fluxo de trabalho
    "refactor", "commit", "pull request", "merge", "deploy", "debug",
    "frontend", "backend", "fullstack", "prompt", "token",
    # PT-BR que o ASR deforma
    "microfone", "transcrição", "hotkey",
)

# Semente de macros PT-BR acústico-textuais (expansão fonética -> sigla/símbolo oficial)
SEED_MACROS: dict[str, str] = {
    "esse tê efe": "STF",
    "esse tê jota": "STJ",
    "tê jota": "TJ",
    "tê érre efe": "TRF",
    "tê érre tê": "TRT",
    "tê ésse é": "TSE",
    "ce pê éfe": "CPF",
    "ce ene pê jota": "CNPJ",
    "érre gê": "RG",
    "o a bê": "OAB",
    "ponto com": ".com",
    "arrouba": "@",
}

# Pool extra só pra detecção de sugestões (não entra no seed automático)
_DETECT_EXTRA: tuple[str, ...] = (
    "Notion", "Linear", "Figma", "Slack", "Discord", "Telegram",
    "WhatsApp", "Outlook", "Gmail", "Azure", "AWS", "GCP",
    "PyTorch", "TensorFlow", "Hugging Face", "CTranslate2",
    "faster-whisper", "Qwen", "Llama", "Midjourney", "Stable Diffusion",
    "Supabase", "Vercel", "Netlify", "nginx", "Linux", "WSL",
    "npm", "pnpm", "pip", "venv", "pytest", "Playwright",
)


def _fold(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


class Dictionary:
    def __init__(self) -> None:
        self._terms: list[str] = []
        self._suggestions: list[str] = []  # pendentes de aceite do usuário
        self._macros: dict[str, str] = {}  # macros acústicas trigger -> repl
        self.load()

    # ------------------------------------------------------------- persistência

    def _path(self):
        return app_data_dir() / "dictionary.json"

    def _suggestions_path(self):
        return app_data_dir() / "dictionary_suggestions.json"

    def _macros_path(self):
        return app_data_dir() / "macros.json"

    def load(self) -> None:
        path = self._path()
        if not path.exists():
            # primeiro uso: semente útil sem exigir configuração
            self._terms = list(SEED_TERMS)
            self.save()
        else:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except OSError:
                raw = []
            except json.JSONDecodeError:
                raw = None
            if isinstance(raw, list):
                self._terms = [str(t).strip() for t in raw if str(t).strip()]
            else:
                backup_corrupt(path)
                self._terms = []

        sp = self._suggestions_path()
        if sp.exists():
            try:
                raw = json.loads(sp.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    self._suggestions = [
                        str(t).strip() for t in raw if str(t).strip()]
            except (OSError, json.JSONDecodeError):
                self._suggestions = []

        mp = self._macros_path()
        if not mp.exists():
            self._macros = dict(SEED_MACROS)
            self._save_macros()
        else:
            try:
                raw = json.loads(mp.read_text(encoding="utf-8"))
            except OSError:
                raw = {}
            except json.JSONDecodeError:
                raw = None
            if isinstance(raw, dict):
                self._macros = {str(k).strip(): str(v).strip() for k, v in raw.items() if str(k).strip()}
            else:
                backup_corrupt(mp)
                self._macros = dict(SEED_MACROS)

    def save(self) -> None:
        write_text_atomic(
            self._path(),
            json.dumps(self._terms, ensure_ascii=False, indent=2),
        )

    def _save_suggestions(self) -> None:
        write_text_atomic(
            self._suggestions_path(),
            json.dumps(self._suggestions, ensure_ascii=False, indent=2),
        )

    def _save_macros(self) -> None:
        write_text_atomic(
            self._macros_path(),
            json.dumps(self._macros, ensure_ascii=False, indent=2),
        )

    # --------------------------------------------------------------------- API

    def all_macros(self) -> dict[str, str]:
        return dict(self._macros)

    def add_macro(self, trigger: str, replacement: str) -> bool:
        trigger = " ".join(trigger.strip().split())
        replacement = replacement.strip()
        if not trigger or not replacement:
            return False
        self._macros[trigger.lower()] = replacement
        self._save_macros()
        return True

    def remove_macro(self, trigger: str) -> None:
        key = trigger.strip().lower()
        if key in self._macros:
            del self._macros[key]
            self._save_macros()

    def apply_macros(self, text: str) -> str:
        """Aplica substituições acústico-textuais no texto com regex boundary."""
        if not text or not self._macros:
            return text
        # Mais longos primeiro pra evitar substituição parcial
        ordered = sorted(self._macros.items(), key=lambda kv: len(kv[0]), reverse=True)
        for trig, repl in ordered:
            pat = re.compile(r"(?<!\w)" + re.escape(trig) + r"(?!\w)", re.IGNORECASE)
            text = pat.sub(repl, text)
        return text

    def all(self) -> list[str]:
        return list(self._terms)

    def count(self) -> int:
        return len(self._terms)

    def add(self, term: str) -> bool:
        term = " ".join(term.strip().split())
        if not term:
            return False
        if any(t.lower() == term.lower() for t in self._terms):
            return False
        self._terms.append(term)
        # se estava nas sugestões, remove
        self._suggestions = [
            s for s in self._suggestions if s.lower() != term.lower()]
        self.save()
        self._save_suggestions()
        return True

    def remove(self, term: str) -> None:
        self._terms = [t for t in self._terms if t != term]
        self.save()

    def suggestions(self) -> list[str]:
        return list(self._suggestions)

    def dismiss_suggestion(self, term: str) -> None:
        self._suggestions = [s for s in self._suggestions if s != term]
        self._save_suggestions()

    def accept_suggestion(self, term: str) -> bool:
        ok = self.add(term)
        self.dismiss_suggestion(term)
        return ok

    def seed_if_empty(self) -> int:
        """Se o dicionário estiver vazio, aplica a semente. Retorna qtd adicionada."""
        if self._terms:
            return 0
        self._terms = list(SEED_TERMS)
        self.save()
        return len(self._terms)

    def observe_text(self, text: str) -> list[str]:
        """Olha uma transcrição e acumula sugestões de termos conhecidos.

        Não adiciona sozinho — só propõe. Retorna as *novas* sugestões desta
        observação (pode ser lista vazia).
        """
        if not text or not text.strip():
            return []

        known = list(SEED_TERMS) + list(_DETECT_EXTRA) + list(self._terms)
        # mapa fold -> grafia canônica
        canon: dict[str, str] = {}
        for k in known:
            canon.setdefault(_fold(k), k)

        owned = {_fold(t) for t in self._terms}
        pending = {_fold(s) for s in self._suggestions}
        # tokens e bigramas simples
        words = re.findall(r"[A-Za-zÀ-ú][A-Za-zÀ-ú0-9+.#/-]*", text)
        candidates: list[str] = []
        for i, w in enumerate(words):
            candidates.append(w)
            if i + 1 < len(words):
                candidates.append(f"{w} {words[i + 1]}")

        new: list[str] = []
        for cand in candidates:
            f = _fold(cand)
            if f not in canon:
                continue
            if f in owned or f in pending:
                continue
            # só sugere se a grafia do ASR difere da canônica
            # (ou se bate case-insensitive — usuário ainda não tem no dict)
            official = canon[f]
            if official.lower() == cand.lower() and f in owned:
                continue
            if f not in owned:
                new.append(official)
                pending.add(f)

        if not new:
            return []

        # dedupe preservando ordem
        seen: set[str] = set()
        uniq: list[str] = []
        for t in new:
            fl = _fold(t)
            if fl in seen:
                continue
            seen.add(fl)
            uniq.append(t)

        for t in uniq:
            if len(self._suggestions) >= _MAX_SUGGESTIONS:
                break
            if _fold(t) not in {_fold(s) for s in self._suggestions}:
                self._suggestions.append(t)
        self._save_suggestions()
        return uniq

    def to_hotwords(self) -> str | None:
        if not self._terms:
            return None
        parts: list[str] = []
        total = 0
        for t in self._terms[:_MAX_TERMS]:
            piece = t.strip()
            if not piece:
                continue
            add = len(piece) + (2 if parts else 0)
            if total + add > _MAX_HOTWORDS_CHARS:
                break
            parts.append(piece)
            total += add
        return ", ".join(parts) if parts else None

    def to_prompt(self) -> str | None:
        base = _STYLE_PROMPT
        if not self._terms:
            return base

        terms = self._terms[:_MAX_TERMS]
        vocab = " Vocabulário esperado: " + ", ".join(terms) + "."
        prompt = base + vocab
        if len(prompt) > _MAX_PROMPT_CHARS:
            budget = _MAX_PROMPT_CHARS - len(base) - len(" Vocabulário esperado: .")
            kept: list[str] = []
            used = 0
            for t in terms:
                need = len(t) + (2 if kept else 0)
                if used + need > budget:
                    break
                kept.append(t)
                used += need
            prompt = (base + " Vocabulário esperado: " + ", ".join(kept) + "."
                      if kept else base)
        return prompt
