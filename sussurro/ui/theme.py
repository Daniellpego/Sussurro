"""Sistema de design "Sussurro Quiet" — fonte unica da verdade dos tokens.

Minimalismo estilo Apple, silencioso. Dois temas alternaveis (DARK/LIGHT)
com tabelas de cor exatas do handoff de design. Assinatura da marca = um
gradiente indigo->rosa usado com parcimonia (brand mark, toggles ligados,
botoes primarios, item "Modos", waveform de gravacao) — nunca como fundo.

Uso:
    from sussurro.ui import theme
    theme.set_theme("dark")          # ou "light"
    pal = theme.palette()            # Palette ativa
    pal.surface                      # -> "#17181C"
    theme.GRADIENT                   # gradiente QSS da marca

Tudo que e cor/medida/peso de fonte mora aqui. Nenhum hex espalhado pelo
codigo: os widgets pedem `palette()` e os tokens deste modulo.

----------------------------------------------------------------------------
NOTA SOBRE QSS: Qt Style Sheets nao suportam `letter-spacing` nem
`box-shadow`. Letter-spacing vai via QFont.setLetterSpacing (helper `qfont`);
sombras via QGraphicsDropShadowEffect ou paint custom (specs em SHADOWS).
----------------------------------------------------------------------------
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont

from sussurro.ui import fonts

# ===========================================================================
# HELPERS DE COR
# ===========================================================================

def qcolor(value: str) -> QColor:
    """QColor a partir de '#RRGGBB' ou 'rgba(r,g,b,a)'."""
    v = value.strip()
    if v.startswith("rgba(") or v.startswith("rgb("):
        nums = v[v.index("(") + 1:v.index(")")].split(",")
        r, g, b = (int(float(n)) for n in nums[:3])
        a = int(float(nums[3]) * 255) if len(nums) > 3 else 255
        return QColor(r, g, b, a)
    return QColor(v)


def rgba(value: str, alpha: float) -> str:
    """String 'rgba(r, g, b, alpha)' pro QSS (alpha 0.0-1.0)."""
    c = qcolor(value)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"

# ===========================================================================
# TIPOGRAFIA
# ===========================================================================

# As familias reais sao resolvidas em runtime (fonts.load_fonts()). Os nomes
# abaixo batem com o que o QFontDatabase registra pras variable fonts Geist.
FONT_UI = "Geist"
FONT_MONO = "Geist Mono"

# Pesos (QFont.Weight numericos == valores CSS font-weight)
W_LIGHT = 300
W_REGULAR = 400
W_MEDIUM = 500
W_SEMIBOLD = 600
W_BOLD = 700

# Letter-spacing por faixa de tamanho (px). Titulos usam tracking negativo.
# (Aplicar via qfont(...) — QSS ignora.)
TRACK_DISPLAY = -0.5     # 25px+
TRACK_TITLE = -0.3       # 17-19px
TRACK_BODY = 0.0
TRACK_LABEL = 0.3        # labels de secao uppercase 11px
TRACK_WORDMARK = 1.0     # wordmark "sussurro" mono


def qfont(size: float, weight: int = W_REGULAR, *, mono: bool = False,
          tracking: float = 0.0) -> QFont:
    """QFont pronto com a familia certa + peso + letter-spacing.

    `size` em px (usa setPixelSize pra casar com as specs do design).
    `tracking` em px absolutos (AbsoluteSpacing).
    """
    family = fonts.mono_family() if mono else fonts.ui_family()
    f = QFont(family)
    f.setPixelSize(round(size))
    f.setWeight(QFont.Weight(weight))
    if tracking:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, tracking)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


# ===========================================================================
# ACENTO — a assinatura da marca (independente de tema)
# ===========================================================================

GRAD_A = "#7C84FF"            # indigo (inicio)
GRAD_B = "#FFAFC9"            # rosa (fim)
INDIGO = "#7C84FF"
LAVENDER = "#C0C1FF"          # destaques/links no dark
ROSE = "#FFAFC9"
LINK_LIGHT = "#6E74F5"        # link/realce no light

# Gradiente principal pronto pra QSS (135deg ~= top-left -> bottom-right).
GRADIENT = (f"qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {GRAD_A}, stop:1 {GRAD_B})")
GRADIENT_HOVER = ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                  "stop:0 #8C93FF, stop:1 #FFBCD3)")

# Sweep do brand mark (5 barras, esq->dir). A waveform do HUD usa as mesmas.
BRAND_SWEEP = ("#7C84FF", "#9A8DFB", "#C49AE8", "#E6A2D6", "#FFAFC9")
BRAND_SQUIRCLE_BG = "#14171D"   # mesmo no light


# ===========================================================================
# ESTADOS (alinhados ao sistema Apple) — variantes dark/light
# ===========================================================================

@dataclass(frozen=True)
class StateColor:
    dark: str
    light: str
    dark_text: str
    light_text: str


# (nomes curtos pra nao colidir com os legados STATE_* que sao strings)
READY = StateColor(dark="#30D158", light="#34C759",
                   dark_text="#30D158", light_text="#1FA34A")
ERROR = StateColor(dark="#FF453A", light="#FF3B30",
                   dark_text="#FFB4AB", light_text="#D9342B")
WARNING = StateColor(dark="#FBBF24", light="#F5A623",
                     dark_text="#FBBF24", light_text="#B07D00")
INFO = StateColor(dark="#0A84FF", light="#0A84FF",
                  dark_text="#0A84FF", light_text="#0A84FF")

# Mapa por chave de estado (conveniencia)
STATES = {"ready": READY, "error": ERROR, "warning": WARNING, "info": INFO}


# ===========================================================================
# MODOS (7) — cor do dot/tile + glyph + descricao
# ===========================================================================

# As cores e glyphs sao tokens de DESIGN; a definicao/lista de modos vive em
# sussurro.llm.modes (dados/CRUD). Cada modo guarda uma CHAVE de cor curada
# (sem color picker livre) e um glyph do conjunto curado.

@dataclass(frozen=True)
class Swatch:
    key: str
    dark: str
    light: str
    dark_glyph: bool  # True -> glyph escuro (#0E0F12) sobre a cor; False -> branco


# Paleta curada de cores de modo (ordem = ordem dos swatches no editor)
MODE_PALETTE: tuple[Swatch, ...] = (
    Swatch("slate",  "#94A3B8", "#94A3B8", True),
    Swatch("green",  "#30D158", "#34C759", True),
    Swatch("blue",   "#0A84FF", "#0A84FF", False),
    Swatch("amber",  "#FBBF24", "#F5A623", True),
    Swatch("purple", "#A78BFA", "#A78BFA", False),
    Swatch("pink",   "#F472B6", "#F472B6", False),
    Swatch("teal",   "#2DD4BF", "#2DD4BF", True),
)
_SWATCHES = {s.key: s for s in MODE_PALETTE}

# Conjunto curado de glyphs pros icones (Geist Mono)
MODE_GLYPHS: tuple[str, ...] = (
    "~", "✓", "@", "≡", "✦", "</>", "⇄", "★", "✎", "#", "➤", "✱",
)


def mode_swatch(color_key: str, light: bool = False) -> str:
    s = _SWATCHES.get(color_key, MODE_PALETTE[0])
    return s.light if light else s.dark


def mode_glyph_on_light(color_key: str) -> bool:
    return _SWATCHES.get(color_key, MODE_PALETTE[0]).dark_glyph


def mode_glyph_color(color_key: str) -> str:
    return "#0E0F12" if mode_glyph_on_light(color_key) else "#FFFFFF"


# ===========================================================================
# GEOMETRIA / RAIOS / ESPACAMENTO
# ===========================================================================

# Raios
RADIUS_WINDOW = 16
RADIUS_CARD = 12          # cards/grupos: 12-14
RADIUS_CARD_LG = 14
RADIUS_INPUT = 10         # inputs/botoes
RADIUS_TILE = 8           # tiles de icone de modo
RADIUS_KEYCAP = 9
RADIUS_KEYCAP_LG = 13
RADIUS_BRAND_46 = 14      # squircle do brand mark (46px)
RADIUS_BRAND_70 = 21      # squircle do brand mark (70px, onboarding)
RADIUS_TILE_BTN = 7       # botoes de title bar / tile de aba

# Espacamentos recorrentes (px)
SP_WINDOW_MARGIN = 16
SP_CARD_PAD = 14
SP_HERO_PAD = 22
SP_GAP = 8
SP_GAP_SM = 6
SP_GAP_LG = 10

# Title bar
TITLEBAR_HEIGHT = 40

# --- HUD / pilula (novo design) ---
HUD_HEIGHT = 40
HUD_HEIGHT_HERO = 46
HUD_RADIUS = 20
HUD_RADIUS_HERO = 23
HUD_BOTTOM_MARGIN = 80
HUD_SHADOW_MARGIN = 18    # folga ao redor da pilula pra sombra nao cortar

# Toggle iOS — tres tamanhos (trilho_w, trilho_h, raio, bolinha)
TOGGLE_DEFAULT = (40, 24, 12, 20)
TOGGLE_SMALL = (34, 20, 10, 16)
TOGGLE_LARGE = (44, 26, 13, 20)

# Brand mark — alturas das 5 barras por tamanho de mark
BRAND_BARS_46 = (11, 18, 26, 18, 11)   # largura 3px
BRAND_BARS_70 = (17, 28, 40, 28, 17)   # largura 3px
BRAND_BARS_28 = (7, 11, 15, 11, 7)     # largura 2px (bandeja)


# ===========================================================================
# SOMBRAS — specs (QSS nao tem box-shadow; usar drop-shadow/paint)
# ===========================================================================

@dataclass(frozen=True)
class Shadow:
    """Spec de sombra: blur (px), dy (px), cor rgba (r,g,b,a 0-255)."""
    blur: int
    dy: int
    color: tuple[int, int, int, int]


SHADOWS = {
    "window_dark":  Shadow(60, 24, (0, 0, 0, 153)),        # 0.6 alpha
    "window_light": Shadow(60, 24, (20, 22, 40, 56)),      # 0.22
    "hud_dark":     Shadow(34, 12, (0, 0, 0, 153)),
    "hud_hero":     Shadow(40, 16, (0, 0, 0, 179)),        # 0.7
    "tray_dark":    Shadow(50, 20, (0, 0, 0, 179)),
    "btn_glow_dark":  Shadow(24, 8, (124, 132, 255, 179)),  # 0.7
    "btn_glow_light": Shadow(24, 8, (124, 132, 255, 128)),  # 0.5
}


# ===========================================================================
# PALETTE — tokens dependentes de tema
# ===========================================================================

@dataclass(frozen=True)
class Palette:
    name: str                    # "dark" | "light"
    # superficies
    window: str                  # fundo externo da janela
    chrome: str                  # title bar / sidebar (== window no dark)
    surface: str                 # card
    inset: str                   # inset / campo
    hover: str                   # hover de linha
    toggle_off: str              # trilho do toggle desligado
    # texto
    text_primary: str
    text_secondary: str
    text_tertiary: str           # dim
    text_mono_dim: str           # mono bem apagado (footer)
    text_body_card: str          # corpo de texto dentro de card
    # bordas
    border_subtle: str
    divider: str                 # divisor de linha em grupo
    border_strong: str
    input_border: str
    # acento/link conforme tema
    link: str
    # progress trilho
    progress_track: str

    # --- helpers de estado no tema atual ---
    def state(self, s: StateColor) -> str:
        return s.dark if self.name == "dark" else s.light

    def state_text(self, s: StateColor) -> str:
        return s.dark_text if self.name == "dark" else s.light_text

    @property
    def is_dark(self) -> bool:
        return self.name == "dark"


DARK = Palette(
    name="dark",
    window="#0E0F12",
    chrome="#0E0F12",
    surface="#17181C",
    inset="#1E2025",
    hover="#26282E",
    toggle_off="#33363D",
    text_primary="#F2F3F5",
    text_secondary="#989BA4",
    text_tertiary="#62656E",
    text_mono_dim="#52555D",
    text_body_card="#C7C9D0",
    border_subtle="rgba(255, 255, 255, 0.06)",
    divider="rgba(255, 255, 255, 0.05)",
    border_strong="rgba(255, 255, 255, 0.10)",
    input_border="rgba(255, 255, 255, 0.10)",
    link=LAVENDER,
    progress_track="rgba(255, 255, 255, 0.08)",
)

LIGHT = Palette(
    name="light",
    window="#F1F1F4",
    chrome="#FBFBFD",
    surface="#FFFFFF",
    inset="#ECEDF0",
    hover="#E7E8EE",
    toggle_off="#D8DAE0",
    text_primary="#1B1C1F",
    text_secondary="#6A6D75",
    text_tertiary="#9DA0A8",
    text_mono_dim="#9DA0A8",
    text_body_card="#3A3C42",
    border_subtle="rgba(0, 0, 0, 0.05)",
    divider="rgba(0, 0, 0, 0.05)",
    border_strong="rgba(0, 0, 0, 0.10)",
    input_border="rgba(0, 0, 0, 0.10)",
    link=LINK_LIGHT,
    progress_track="#E4E5EA",
)

_PALETTES = {"dark": DARK, "light": LIGHT}
_active: Palette = DARK


def set_theme(name: str) -> Palette:
    """Troca o tema ativo. Aceita 'dark'/'light' (default dark)."""
    global _active
    _active = _PALETTES.get(name, DARK)
    return _active


def resolve_preference(pref: str) -> str:
    """Mapeia a preferencia de tema -> esquema concreto.

    'dark'/'light' passam direto; 'system' (ou qualquer outro) le o esquema
    de cor do Windows via QStyleHints (Qt 6.5+), caindo em 'dark' se nao der.
    """
    if pref in ("dark", "light"):
        return pref
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication
        hints = QGuiApplication.styleHints()
        if hints is not None and hints.colorScheme() == Qt.ColorScheme.Light:
            return "light"
    except Exception:  # noqa: BLE001
        pass
    return "dark"


def apply_preference(pref: str) -> Palette:
    """Resolve 'system'/'dark'/'light' e ativa o tema correspondente."""
    return set_theme(resolve_preference(pref))


def palette() -> Palette:
    """Palette ativa."""
    return _active


def is_dark() -> bool:
    return _active.name == "dark"


# ===========================================================================
# TOKENS DE DESIGN EXTRAS (mock-specific, fora da Palette base) — dark/light
# ===========================================================================

# Dots inativos do onboarding
ONB_DOT_OFF_DARK = "#2C2E34"
ONB_DOT_OFF_LIGHT = "#D2D4DB"


def onb_dot_off() -> str:
    return ONB_DOT_OFF_DARK if is_dark() else ONB_DOT_OFF_LIGHT


# Popup da bandeja (bg entre window e surface — não é token da Palette)
POPUP_BG_DARK, POPUP_BG_LIGHT = "#1A1C20", "#FFFFFF"
POPUP_BORDER_DARK, POPUP_BORDER_LIGHT = "rgba(255,255,255,0.08)", "rgba(0,0,0,0.08)"
POPUP_DIVIDER_DARK, POPUP_DIVIDER_LIGHT = "rgba(255,255,255,0.06)", "rgba(0,0,0,0.07)"
POPUP_HOVER_DARK, POPUP_HOVER_LIGHT = "#26282E", "#EEF0F3"
POPUP_TEXT_LIGHT = "#2A2C30"


def popup_colors() -> tuple[str, str, str, str]:
    """(bg, border, divider, hover) do popup da bandeja, por tema."""
    if is_dark():
        return POPUP_BG_DARK, POPUP_BORDER_DARK, POPUP_DIVIDER_DARK, POPUP_HOVER_DARK
    return POPUP_BG_LIGHT, POPUP_BORDER_LIGHT, POPUP_DIVIDER_LIGHT, POPUP_HOVER_LIGHT


# Texto de código (modo Code) no histórico
CODE_TEXT_DARK, CODE_TEXT_LIGHT = "#A9C7E8", "#3E6CA8"


def code_text() -> str:
    return CODE_TEXT_DARK if is_dark() else CODE_TEXT_LIGHT


# ===========================================================================
# QSS BASE — aplicado no QApplication (defaults globais discretos)
# ===========================================================================

def app_base_qss() -> str:
    """QSS global minimo: fonte default + tooltip. As janelas trazem o
    proprio QSS detalhado por cima."""
    p = _active
    return f"""
    * {{
        font-family: "{FONT_UI}", "Segoe UI", system-ui;
    }}
    QToolTip {{
        background: {p.surface};
        color: {p.text_primary};
        border: 1px solid {p.border_strong};
        border-radius: 8px;
        padding: 5px 9px;
        font-size: 12px;
    }}
    """
