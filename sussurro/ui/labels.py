"""Rótulos das opções exibidas na interface.

Fonte única para a janela principal, os Ajustes e a bandeja mostrarem o
mesmo texto para o mesmo valor de configuração.
"""
from __future__ import annotations

LANGUAGE = {
    "pt": "Português",
    "en": "English",
    "auto": "Detectar automaticamente",
}

PASTE_METHOD = {
    "auto": "Automático",
    "ctrl+v": "Ctrl + V",
    "shift+insert": "Shift + Insert",
    "type": "Digitar o texto",
}

QUALITY = {
    "quality": "Qualidade",
    "balanced": "Equilíbrio",
    "light": "Leve",
}

KEEP_ALIVE = {
    "0": "Liberar na hora (recomendado)",
    "5m": "5 minutos",
    "10m": "10 minutos",
    "30m": "30 minutos",
}

MOUSE_BUTTON = {
    "none": "Nenhum",
    "middle": "Botão do meio",
    "x1": "Lateral (voltar)",
    "x2": "Lateral (avançar)",
}

DEFAULT_MIC = "Padrão do sistema"
