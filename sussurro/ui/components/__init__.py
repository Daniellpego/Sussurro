"""Kit de componentes reutilizaveis do design "Sussurro Quiet".

Todos parametrizados por `theme.palette()` — funcionam em dark e light. Os
widgets que dependem de tema expoem `apply_theme()` pra re-renderizar quando o
usuario troca o esquema (tela 05). Nenhum hex mora aqui: tudo vem de `theme`.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from sussurro.ui.components.brand_mark import BrandMark, brand_icon, brand_pixmap
from sussurro.ui.components.buttons import GhostButton, PrimaryButton, SecondaryButton
from sussurro.ui.components.chevron import Chevron
from sussurro.ui.components.fields import LineEdit, TextArea
from sussurro.ui.components.group import GroupCard, ToggleRow, ValueRow
from sussurro.ui.components.icon_tile import ModeIconTile
from sussurro.ui.components.keycap import Keycap
from sussurro.ui.components.mode_chip import ModeChip
from sussurro.ui.components.progress import ProgressBar
from sussurro.ui.components.segmented import SegmentedControl
from sussurro.ui.components.title_bar import WindowTitleBar
from sussurro.ui.components.toggle import IOSToggle
from sussurro.ui.components.window_frame import FramelessWindow


def apply_theme_recursive(root: QWidget) -> None:
    """Re-renderiza toda a arvore apos troca de tema: chama apply_theme() em
    quem tiver, e força update() nos widgets pintados a mao."""
    widgets = [root, *root.findChildren(QWidget)]
    for w in widgets:
        fn = getattr(w, "apply_theme", None)
        if callable(fn):
            fn()
        else:
            w.update()


__all__ = [
    "BrandMark", "brand_icon", "brand_pixmap",
    "PrimaryButton", "SecondaryButton", "GhostButton",
    "Chevron",
    "GroupCard", "ValueRow", "ToggleRow",
    "ModeIconTile",
    "Keycap",
    "ModeChip",
    "ProgressBar",
    "IOSToggle",
    "WindowTitleBar",
    "FramelessWindow",
    "LineEdit",
    "TextArea",
    "SegmentedControl",
    "apply_theme_recursive",
]
