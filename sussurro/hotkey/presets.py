"""Atalhos de teclado que podem ser escolhidos nos Ajustes.

Sem pynput aqui: a UI e a config usam estes nomes sem instalar o hook do
teclado. As teclas de cada atalho ficam em `listener.HOTKEYS`.
"""
from __future__ import annotations

DEFAULT_HOTKEY = "Ctrl+Win"

# valor salvo em Config.hotkey_label -> rotulo no seletor dos Ajustes
HOTKEY_LABELS: dict[str, str] = {
    "Ctrl+Win": "Ctrl + Win (padrão)",
    "Ctrl+Shift": "Ctrl + Shift",
    "Ctrl+Alt": "Ctrl + Alt",
    "Ctrl direito": "Ctrl direito sozinho",
}


def normalize_hotkey(name: str | None) -> str:
    """Atalho conhecido; valores antigos ou inválidos voltam ao padrão."""
    return name if name in HOTKEY_LABELS else DEFAULT_HOTKEY


def keycap_labels(name: str | None) -> list[str]:
    """Teclas do atalho na ordem dos keycaps ("Ctrl+Win" -> ["Ctrl", "Win"])."""
    return normalize_hotkey(name).split("+")
