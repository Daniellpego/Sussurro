"""Modos como DADOS (CRUD) — coração do app.

Cada modo é um registro persistido (id, nome, cor, ícone/glyph, modelo, prompt,
atalho, ativo, builtin, contador de uso). Os 7 modos clássicos viram built-ins
semeados no primeiro boot; o usuário pode criar/editar/duplicar/ativar/desativar
e deletar os customizados.

Persistência: %APPDATA%/Sussurro/modes.json (formato novo = lista). Migração:
se o arquivo for o formato antigo ({id: prompt}) ou ausente, semeia os built-ins
preservando prompts customizados que o usuário já tinha (ninguém perde o Clean).

Built-in vs custom:
- built-in: editável, NÃO deletável (só desativável); tem "restaurar padrão" no prompt.
- custom: totalmente editável e deletável.

Aplicar um modo a um texto = chamar o LLM com system=prompt do modo. O modo 'raw'
não chama LLM (prompt vazio).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from sussurro.storage.paths import app_data_dir, write_text_atomic

DEFAULT_LLM_MODEL = "qwen2.5"
DEFAULT_LLM_LABEL = "Qwen 2.5 · 7B (Ollama)"


_BASE_RULES = (
    "Voce e um pos-processador de transcricoes de voz (ASR) em PT-BR, "
    "com code-switching ocasional PT/EN.\n"
    "REGRAS CRITICAS:\n"
    "1. Saida = SOMENTE o texto final. Sem aspas, sem preambulo, sem "
    "explicacao, sem 'aqui esta', sem markdown de cerca.\n"
    "2. Acentuacao PT-BR OBRIGATORIA: corrija 'voce'→'você', 'nao'→'não', "
    "'e' (verbo)→'é', 'ate'→'até', 'tambem'→'também', 'esta'→'está' quando "
    "for o verbo, 'horario'→'horário', 'numero'→'número', etc. Nao deixe "
    "palavra portuguesa sem o acento correto se o sentido for claro.\n"
    "3. Termos em INGLES: preserve grafia e casing de ferramentas, APIs, "
    "marcas, libs e jargao tecnico exatamente como o falante usou "
    "(Python, GitHub, Claude, Ollama, refactor, pull request, commit). "
    "NAO traduza esses termos.\n"
    "4. Nao invente fatos, nomes ou frases que nao estavam no original.\n"
    "5. Preserve a intencao e o tom emocional do falante."
)

_DEFAULT_PROMPTS: dict[str, str] = {
    "raw": "",
    "clean": (
        f"{_BASE_RULES}\n\nMODO: Clean.\n"
        "Tarefa: limpe a transcricão de ASR sem mudar o sentido.\n"
        "- Remova hesitacoes ('humm', 'ééé', 'tipo', 'né' vazio, 'assim').\n"
        "- Remova repeticoes consecutivas de palavra.\n"
        "- Corrija gramatica e ACENTUACAO obvias em PT-BR.\n"
        "- Corrija erros tipicos de ASR (homofonos: 'mas'/'mais', "
        "'por que'/'porque' quando o contexto deixar claro).\n"
        "- Pontue de forma natural (virgulas, pontos, interrogacoes).\n"
        "- Organize em paragrafos se houver mais de uma ideia.\n"
        "- Mantenha o registro (informal fica informal).\n"
        "- Se o texto ja estiver bom, mude o minimo necessario."
    ),
    "email": (
        f"{_BASE_RULES}\n\nMODO: Email.\n"
        "Tarefa: reescreva como e-mail profissional bem estruturado. "
        "Identifique destinatario, assunto e acao desejada se mencionados. "
        "Use saudacao, paragrafos curtos e despedida cordial. Mantenha o "
        "tom do falante (mais ou menos formal conforme o original). "
        "Acentuacao e termos em ingles corretos."
    ),
    "bullets": (
        f"{_BASE_RULES}\n\nMODO: Bullets.\n"
        "Tarefa: extraia os pontos-chave do texto em uma lista de bullets "
        "com marcador '-'. Cada bullet deve ser uma ideia completa e "
        "concisa, com acentuacao correta. Mantenha a ordem do raciocinio "
        "do falante e termos tecnicos em ingles."
    ),
    "prompt": (
        f"{_BASE_RULES}\n\nMODO: Prompt.\n"
        "Tarefa: refine a fala em um prompt limpo e direto para um LLM "
        "(ChatGPT, Claude, Midjourney). Remova hesitacoes e divagacoes. "
        "Mantenha a intencao especifica e termos tecnicos em ingles. "
        "Se for prompt para imagem, preserve detalhes visuais. Se for "
        "prompt de codigo, preserve requisitos tecnicos."
    ),
    "code": (
        f"{_BASE_RULES}\n\nMODO: Code.\n"
        "Tarefa: se o falante descreveu codigo, formate como bloco de "
        "codigo na linguagem inferida (Python por default). Converta "
        "nomes de variaveis em snake_case (Python) ou camelCase (JS/TS) "
        "conforme a linguagem. Se for explicacao tecnica, mantenha como "
        "texto com acentuacao PT-BR e termos tecnicos em ingles."
    ),
    "translate": (
        f"{_BASE_RULES}\n\nMODO: Translate.\n"
        "Tarefa: traduza o texto de PT-BR para ingles natural e idiomatico. "
        "Preserve termos tecnicos e nomes proprios que ja estavam em ingles "
        "(nao 'retraduza'). Nao invente conteudo."
    ),
    "email_corp": (
        f"{_BASE_RULES}\n\nMODO: E-mail Corporativo.\n"
        "Tarefa: reescreva a fala como um e-mail corporativo executivo de alto padrão.\n"
        "- Sugira na primeira linha o campo 'Assunto: [Assunto Conciso e Direto]'.\n"
        "- Estruture com saudação profissional adequada ao contexto.\n"
        "- Apresente o contexto e objetivo em 1 ou 2 parágrafos claros e objetivos.\n"
        "- Se houver tarefas, decisões ou prazos, organize-os em lista com marcadores (-).\n"
        "- Finalize com chamada para ação clara (Next Steps) e encerramento cordial profissional.\n"
        "- Garanta português corporativo impecável com acentuação estrita e termos técnicos preservados."
    ),
    "laudo_birads": (
        f"{_BASE_RULES}\n\nMODO: Laudo Radiológico BI-RADS.\n"
        "Tarefa: formate a transcrição médica como um Laudo Radiológico padronizado.\n"
        "- Estruture nas seções:\n"
        "  INDICAÇÃO CLÍNICA E TÉCNICA: (modalidade do exame e motivo)\n"
        "  ACHADOS: (descrição anatômica detalhada, composição tecidual, nódulos/calcificações)\n"
        "  IMPRESSÃO DIAGNÓSTICA: (síntese conclusiva clara)\n"
        "  CATEGORIA BI-RADS: (especifique de 0 a 6 conforme os achados citados)\n"
        "  RECOMENDAÇÃO / CONDUTA: (seguimento sugerido)\n"
        "- Mantenha rigor terminológico médico e farmacológico em PT-BR.\n"
        "- Não invente medidas, lateralidade ou achados ausentes no relato do médico."
    ),
    "peticao_inicial": (
        f"{_BASE_RULES}\n\nMODO: Petição Inicial.\n"
        "Tarefa: estruture o ditado jurídico nos moldes de uma Petição Inicial (CPC/Processo Civil brasileiro).\n"
        "- Estrutura:\n"
        "  I. DO ENDEREÇAMENTO E QUALIFICAÇÃO DAS PARTES\n"
        "  II. DOS FATOS (narrativa cronológica e lógica clara dos acontecimentos)\n"
        "  III. DO DIREITO (fundamentação jurídica com artigos e teses aplicáveis mencionadas)\n"
        "  IV. DOS PEDIDOS E REQUERIMENTOS (itens numerados: citação, procedência, provas, condenação em custas e honorários)\n"
        "  V. DO VALOR DA CAUSA e encerramento ('Termos em que, Pede deferimento. Local e Data. Advogado / OAB').\n"
        "- Linguagem formal forense escorreita, mantendo termos em latim e siglas de tribunais (STF, STJ, TJ, TRF) corretas."
    ),
    "humanizer": (
        f"{_BASE_RULES}\n\nMODO: Humanizador.\n"
        "Tarefa: reescreva a transcricao para soar 100% organica e humana.\n"
        "- Elimine cliches e maneirismos sinteticos de IA ('no cenario atual', 'em suma', 'e crucial').\n"
        "- Varie a cadencia das frases evitando simetria artificial.\n"
        "- Mantenha a intencao original e o tom espontaneo do falante.\n"
        "- Acentuacao e pontuacao corretas em PT-BR, preservando termos tecnicos em ingles."
    ),
    "segundo_cerebro": (
        f"{_BASE_RULES}\n\nMODO: Segundo Cerebro.\n"
        "Tarefa: estruture o ditado em uma nota limpa em Markdown para o Obsidian.\n"
        "- Inclua frontmatter YAML com tipo: nota_rapida e tags: [segundo_cerebro, ditado].\n"
        "- Adicione um titulo H1 sintetizando o ponto central.\n"
        "- Organize em secoes com marcadores para Conceitos, Decisoes e Acoes (- [ ]).\n"
        "- Linguagem concisa e direta, sem preambulos."
    ),
}

# (id, nome, descricao, cor-curada, glyph)
_BUILTIN_META: tuple[tuple[str, str, str, str, str], ...] = (
    ("raw",             "Raw",             "Texto verbatim, sem IA",                          "slate",   "~"),
    ("clean",           "Clean",           "Remove vícios e corrige a gramática",               "green",   "✓"),
    ("email",           "Email",           "Reescreve como e-mail profissional",               "blue",    "@"),
    ("bullets",         "Bullets",         "Pontos-chave em lista",                           "amber",   "≡"),
    ("prompt",          "Prompt",          "Refina pra virar prompt de IA",                   "purple",  "✦"),
    ("code",            "Code",            "Formata como bloco de código",                    "pink",    "</>"),
    ("translate",       "Translate",       "Traduz PT-BR → inglês",                           "teal",    "⇄"),
    ("email_corp",      "Corporativo",     "E-mail executivo com contexto e próximos passos", "blue",    "✉"),
    ("laudo_birads",    "Laudo BI-RADS",   "Laudo radiológico com classificação BI-RADS",     "indigo",  "⚕"),
    ("peticao_inicial", "Petição Inicial", "Estruturação forense de Petição Inicial (CPC)",   "amber",   "§"),
    ("humanizer",       "Humanizador",     "Escrita organica sem cliches de IA",               "amber",   "~"),
    ("segundo_cerebro", "Segundo Cerebro", "Nota Markdown estruturada para o Obsidian",        "teal",    "#"),
)


@dataclass
class Mode:
    id: str
    name: str
    description: str
    color: str               # chave curada (theme.MODE_PALETTE): slate/green/blue/...
    glyph: str
    prompt: str
    model: str = DEFAULT_LLM_MODEL
    shortcut: str | None = None
    active: bool = True
    builtin: bool = False
    usage_count: int = 0

    @property
    def is_raw(self) -> bool:
        return self.id == "raw"


def _seed_defaults() -> list[Mode]:
    out: list[Mode] = []
    for mid, name, desc, color, glyph in _BUILTIN_META:
        out.append(Mode(
            id=mid, name=name, description=desc, color=color, glyph=glyph,
            prompt=_DEFAULT_PROMPTS.get(mid, ""), builtin=True, active=True,
        ))
    return out


def default_prompt(mode_id: str) -> str:
    return _DEFAULT_PROMPTS.get(mode_id, "")


def _mode_from_dict(d: dict) -> Mode | None:
    valid = {f.name for f in fields(Mode)}
    data = {k: v for k, v in d.items() if k in valid}
    if "id" not in data:
        return None
    data.setdefault("name", data["id"].title())
    data.setdefault("description", "")
    data.setdefault("color", "slate")
    data.setdefault("glyph", "★")
    data.setdefault("prompt", "")
    return Mode(**data)


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "modo"


@dataclass
class ModeStore:
    modes: list[Mode] = field(default_factory=_seed_defaults)

    # ------------------------------------------------------------- load/save

    @classmethod
    def load(cls) -> ModeStore:
        path = _store_path()
        if not path.exists():
            store = cls(_seed_defaults())
            store.save()
            return store
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(_seed_defaults())

        # formato ANTIGO: {id: prompt} -> migra preservando prompts customizados
        if isinstance(data, dict):
            seeded = _seed_defaults()
            for m in seeded:
                p = data.get(m.id)
                if isinstance(p, str) and p:
                    m.prompt = p
            store = cls(seeded)
            store.save()
            return store

        # formato NOVO: lista de modos
        modes: list[Mode] = []
        if isinstance(data, list):
            for d in data:
                if isinstance(d, dict):
                    m = _mode_from_dict(d)
                    if m is not None:
                        modes.append(m)
        if not modes:
            modes = _seed_defaults()
        # garante que todos os built-ins existam (e marca builtin corretamente)
        existing = {m.id for m in modes}
        for d in _seed_defaults():
            if d.id not in existing:
                modes.append(d)
        builtin_ids = {mid for mid, *_ in _BUILTIN_META}
        upgraded = False
        for m in modes:
            m.builtin = m.id in builtin_ids
            # Built-ins com prompt "de fábrica" antigo (sem as regras de
            # acentuação/code-switch) sobem pro default novo. Prompt custom
            # do usuário (qualquer coisa sem o marcador velho exato) fica.
            if (
                m.builtin
                and m.id != "raw"
                and m.prompt
                and "Acentuacao PT-BR OBRIGATORIA" not in m.prompt
                and "pos-processador de transcricoes de voz em PT-BR." in m.prompt
            ):
                m.prompt = _DEFAULT_PROMPTS.get(m.id, m.prompt)
                upgraded = True
        store = cls(modes)
        if upgraded:
            store.save()
        return store

    def save(self) -> None:
        write_text_atomic(
            _store_path(),
            json.dumps([asdict(m) for m in self.modes],
                       ensure_ascii=False, indent=2),
        )

    # ------------------------------------------------------------------ CRUD

    def all(self) -> list[Mode]:
        return list(self.modes)

    def active_modes(self) -> list[Mode]:
        return [m for m in self.modes if m.active]

    def get(self, mode_id: str) -> Mode:
        for m in self.modes:
            if m.id == mode_id:
                return m
        # fallback seguro
        return self.modes[0] if self.modes else _seed_defaults()[0]

    def exists(self, mode_id: str) -> bool:
        return any(m.id == mode_id for m in self.modes)

    def get_prompt(self, mode_id: str) -> str:
        return self.get(mode_id).prompt

    def add(self, mode: Mode) -> Mode:
        self.modes.append(mode)
        self.save()
        return mode

    def new_id(self, name: str) -> str:
        base = _slug(name)
        mid = base
        i = 2
        while self.exists(mid):
            mid = f"{base}-{i}"
            i += 1
        return mid

    def update(self, mode: Mode) -> None:
        for i, m in enumerate(self.modes):
            if m.id == mode.id:
                self.modes[i] = mode
                self.save()
                return
        self.add(mode)

    def delete(self, mode_id: str) -> bool:
        """Remove um modo custom (built-ins não são deletáveis)."""
        m = next((m for m in self.modes if m.id == mode_id), None)
        if m is None:
            return False
        if m.builtin:
            return False
        self.modes = [x for x in self.modes if x.id != mode_id]
        self.save()
        return True

    def set_active(self, mode_id: str, active: bool) -> None:
        mode = next((m for m in self.modes if m.id == mode_id), None)
        if mode is None:
            raise KeyError(f"modo inexistente: {mode_id}")
        mode.active = active
        self.save()

    def reset_prompt(self, mode_id: str) -> str:
        """Restaura o prompt padrão (só faz sentido pra built-in)."""
        m = next((m for m in self.modes if m.id == mode_id), None)
        if m is None:
            raise KeyError(f"modo inexistente: {mode_id}")
        if not m.builtin:
            raise ValueError("apenas modos built-in têm prompt padrão")
        m.prompt = _DEFAULT_PROMPTS.get(mode_id, "")
        self.save()
        return m.prompt

    def increment_usage(self, mode_id: str) -> None:
        if self.exists(mode_id):
            self.get(mode_id).usage_count += 1
            self.save()

    def fallback_id(self, preferred: str | None = None) -> str:
        """ID de um modo ativo válido (preferido -> clean -> raw -> primeiro)."""
        active = self.active_modes()
        ids = {m.id for m in active}
        if preferred and preferred in ids:
            return preferred
        for cand in ("clean", "raw"):
            if cand in ids:
                return cand
        return active[0].id if active else "raw"


def _store_path() -> Path:
    return app_data_dir() / "modes.json"


# ===========================================================================
# Singleton ativo — componentes resolvem modo por id sem acoplar via parâmetro
# ===========================================================================

_active_store: ModeStore | None = None


def set_active(store: ModeStore) -> None:
    global _active_store
    _active_store = store


def active() -> ModeStore:
    """Store ativo (carrega sob demanda se ninguém registrou ainda)."""
    global _active_store
    if _active_store is None:
        _active_store = ModeStore.load()
    return _active_store


def get(mode_id: str) -> Mode:
    return active().get(mode_id)
