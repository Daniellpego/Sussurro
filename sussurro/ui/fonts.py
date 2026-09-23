"""Carrega as fontes empacotadas Geist e Geist Mono.

Design system "Sussurro Quiet": a UI inteira usa **Geist** (pesos
300/400/500/600/700) e o conteudo tecnico (keycaps, timer do HUD, nome do
modelo, contadores, labels mono) usa **Geist Mono** (400/500/600).

Chamar `load_fonts()` uma vez, logo apos criar o QApplication e antes de
construir widgets. Retorna o nome da familia da UI ("Geist" se carregou, ou
um fallback do sistema). O nome da familia mono fica disponivel via
`mono_family()`. As duas sao variable fonts — o Qt 6 registra cada peso como
um estilo nomeado, entao `font-weight: 600` no QSS mapeia pro SemiBold.
"""
from __future__ import annotations

import logging

from PySide6.QtGui import QFontDatabase

from sussurro.storage.paths import asset_path

log = logging.getLogger("sussurro")

# Fallbacks do sistema caso o .ttf nao registre (Segoe UI cobre Windows).
_UI_FALLBACK = "Segoe UI"
_MONO_FALLBACK = "Consolas"

_ui_family: str | None = None
_mono_family: str | None = None


def _register(filename: str, fallback: str) -> str:
    path = asset_path("fonts", filename)
    if not path.exists():
        log.warning("fonte %s nao encontrada em %s, usando %s", filename, path, fallback)
        return fallback
    idx = QFontDatabase.addApplicationFont(str(path))
    if idx == -1:
        log.warning("falha ao registrar %s, usando %s", filename, fallback)
        return fallback
    families = QFontDatabase.applicationFontFamilies(idx)
    # A variable font reporta varias entradas ("Geist", "Geist Medium", ...).
    # A familia base e a mais curta (sem sufixo de peso).
    base = min(families, key=len) if families else fallback
    return base or fallback


def load_fonts() -> str:
    """Registra Geist + Geist Mono. Retorna a familia da UI."""
    global _ui_family, _mono_family
    if _ui_family is not None:
        return _ui_family

    _ui_family = _register("Geist.ttf", _UI_FALLBACK)
    _mono_family = _register("GeistMono.ttf", _MONO_FALLBACK)
    log.info("fontes carregadas: ui=%s mono=%s", _ui_family, _mono_family)
    return _ui_family


def ui_family() -> str:
    """Familia da UI (carrega sob demanda se ainda nao foi)."""
    if _ui_family is None:
        load_fonts()
    return _ui_family or _UI_FALLBACK


def mono_family() -> str:
    """Familia mono (carrega sob demanda se ainda nao foi)."""
    if _mono_family is None:
        load_fonts()
    return _mono_family or _MONO_FALLBACK
