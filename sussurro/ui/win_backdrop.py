"""Efeito vidro (acrílico/mica) via DWM no Windows 11 (22H2+).

Aplica o backdrop do sistema atrás da janela. Requer que a janela seja
translúcida (WA_TranslucentBackground) e que o "card" tenha fundo semi-
transparente pra o blur aparecer. Tolerante a falha: em Windows mais antigo ou
se a API não existir, simplesmente não faz nada (a janela fica sólida).
"""
from __future__ import annotations

import ctypes
import sys

# DwmSetWindowAttribute attrs
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWA_SYSTEMBACKDROP_TYPE = 38

# corner preference
_DWMWCP_ROUND = 2

# backdrop kinds
BACKDROP_NONE = 1
BACKDROP_MICA = 2
BACKDROP_ACRYLIC = 3   # "transient" — blur do que está atrás (mais vidro)
BACKDROP_TABBED = 4


def available() -> bool:
    return sys.platform == "win32"


def apply_backdrop(hwnd: int, *, dark: bool, kind: int = BACKDROP_ACRYLIC) -> bool:
    """Liga o backdrop + cantos arredondados + tint dark/light. Retorna True
    se aplicou (best-effort; não levanta)."""
    if not available() or not hwnd:
        return False
    try:
        dwm = ctypes.windll.dwmapi

        def setattr_(attr: int, value: int) -> int:
            v = ctypes.c_int(value)
            return dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v),
                                             ctypes.sizeof(v))

        setattr_(_DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0)
        setattr_(_DWMWA_WINDOW_CORNER_PREFERENCE, _DWMWCP_ROUND)
        rc = setattr_(_DWMWA_SYSTEMBACKDROP_TYPE, kind)
        return rc == 0
    except Exception:  # noqa: BLE001 - cosmético, nunca quebra a janela
        return False
