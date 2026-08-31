"""Sistema de icones SVG inline.

Cada icone e um path SVG (24x24, viewBox 0 0 24 24, stroke-based ou
filled style) que e renderizado em QIcon na cor pedida. Inspirado nos
Material Symbols Outlined (forma e proporcao).
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Cada SVG e o conteudo INTERNO de <svg viewBox="0 0 24 24"> — sem o
# wrapper outer. {color} placeholder substituido em runtime.
ICONS: dict[str, str] = {
    "home": (
        '<path fill="{color}" d="M3 11.5 12 4l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4'
        'a1 1 0 0 1-1-1z"/>'
    ),
    "history": (
        '<path fill="{color}" d="M12.5 3a9 9 0 1 0 8.94 9.94l-2-.22A7 7 0 1 1 12.5 5'
        'a7 7 0 0 1 4.95 2.05L14 10h7V3l-2.46 2.46A8.98 8.98 0 0 0 12.5 3z"/>'
        '<path fill="{color}" d="M11 8v5l4.25 2.5.75-1.25-3.5-2.06V8z"/>'
    ),
    "tune": (
        '<path fill="{color}" d="M3 17v2h6v-2H3zm0-7v2h10v-2H3zm0-7v2h14V3H3zm18 16'
        'v-4h-2v1.5h-4v1H21zm-8 0v-1H7v2h6v-1zm2-7v-1h-2v2h8v-1H15zm6-7v1.5h-4V3'
        'h-2v4h6V3z"/>'
    ),
    "settings": (
        '<path fill="{color}" d="M19.43 12.98a7.65 7.65 0 0 0 0-1.96l2.11-1.65'
        'a.5.5 0 0 0 .12-.64l-2-3.46a.5.5 0 0 0-.61-.22l-2.49 1a7.32 7.32 0 0 0-1.69-.98'
        'l-.38-2.65A.49.49 0 0 0 14 2h-4a.49.49 0 0 0-.49.42l-.38 2.65c-.6.24-1.17.57-1.69.98'
        'l-2.49-1a.5.5 0 0 0-.61.22l-2 3.46a.5.5 0 0 0 .12.64l2.11 1.65a7.65 7.65 0 0 0 0 1.96'
        'l-2.11 1.65a.5.5 0 0 0-.12.64l2 3.46a.5.5 0 0 0 .61.22l2.49-1c.52.41 1.09.74 1.69.98'
        'l.38 2.65c.05.24.25.42.49.42h4c.24 0 .44-.18.49-.42l.38-2.65c.6-.24 1.17-.57 1.69-.98'
        'l2.49 1a.5.5 0 0 0 .61-.22l2-3.46a.5.5 0 0 0-.12-.64zM12 15.5a3.5 3.5 0 1 1 0-7'
        ' 3.5 3.5 0 0 1 0 7z"/>'
    ),
    "info": (
        '<path fill="{color}" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-6h2zm0-8h-2V7'
        'h2z"/>'
    ),
    "keyboard": (
        '<path fill="{color}" d="M20 5H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7'
        'a2 2 0 0 0-2-2zm-9 3h2v2h-2zm0 3h2v2h-2zM8 8h2v2H8zm0 3h2v2H8zm-1 5v-2h10v2zm10-3h-2'
        'v-2h2zm0-3h-2V8h2z"/>'
    ),
    "mic": (
        '<path fill="{color}" d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z"/>'
        '<path fill="{color}" d="M17.3 11c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5a6.32 6.32 0 0 0 5.16 6.16V20h3.68v-2.84'
        'A6.32 6.32 0 0 0 19 11z"/>'
    ),
    "content_copy": (
        '<path fill="{color}" d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14'
        'a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11z"/>'
    ),
    "search": (
        '<path fill="{color}" d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79'
        'L20 20.5l1.5-1.5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.49 4.49 0 0 1 9.5 14z"/>'
    ),
    "close": (
        '<path fill="{color}" d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59'
        ' 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>'
    ),
    "minimize": (
        '<path fill="{color}" d="M5 11h14v2H5z"/>'
    ),
    "maximize": (
        '<path fill="none" stroke="{color}" stroke-width="1.5" d="M5 5h14v14H5z"/>'
    ),
    "description": (
        '<path fill="{color}" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'
        'M16 18H8v-2h8zm0-4H8v-2h8zm-3-5V3.5L18.5 9z"/>'
    ),
    "mail": (
        '<path fill="{color}" d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6'
        'a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5z"/>'
    ),
    "code": (
        '<path fill="{color}" d="m9.4 16.6-4.6-4.6 4.6-4.6L8 6l-6 6 6 6zm5.2 0 4.6-4.6-4.6-4.6'
        'L16 6l6 6-6 6z"/>'
    ),
    "edit": (
        '<path fill="{color}" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75zm17.71-10.21'
        'a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75z"/>'
    ),
    "chevron_down": (
        '<path fill="{color}" d="M7.41 8.59 12 13.17l4.59-4.58L18 10l-6 6-6-6z"/>'
    ),
    "chevron_right": (
        '<path fill="{color}" d="M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z"/>'
    ),
    "check": (
        '<path fill="{color}" d="m9 16.17-4.17-4.17L3.41 13.42 9 19l12-12-1.41-1.42z"/>'
    ),
    "trash": (
        '<path fill="{color}" d="M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6zM19 4h-3.5l-1-1h-5'
        'l-1 1H5v2h14z"/>'
    ),
    "refresh": (
        '<path fill="{color}" d="M17.65 6.35A8 8 0 1 0 19.73 14h-2.08a6 6 0 1 1-5.65-8'
        'A5.92 5.92 0 0 1 16.22 8H13v2h7V3z"/>'
    ),
    "folder": (
        '<path fill="{color}" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8'
        'c0-1.1-.9-2-2-2h-8z"/>'
    ),
    "open_in_new": (
        '<path fill="{color}" d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2'
        'v-7h-2zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3z"/>'
    ),
    "globe": (
        '<path fill="{color}" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12'
        'S17.52 2 11.99 2zm-1 17.93A8.01 8.01 0 0 1 4 12c0-.61.07-1.2.19-1.78L9 15v1a2 2 0 0 0 2 2zm6.9-2.54'
        'a2 2 0 0 0-1.9-1.39h-1v-3a1 1 0 0 0-1-1H8v-2h2a1 1 0 0 0 1-1V7h2a2 2 0 0 0 2-2v-.41A7.98 7.98 0 0 1 20 12'
        'a7.97 7.97 0 0 1-2.1 5.39z"/>'
    ),
    "filter": (
        '<path fill="{color}" d="M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6'
        's3.72-4.8 5.74-7.39A1 1 0 0 0 18.95 4H5.04a1 1 0 0 0-.79 1.61z"/>'
    ),
}


def icon(name: str,
         color: str = "#E2E2E8",
         size: int = 24) -> QIcon:
    """Retorna QIcon do nome dado, renderizado na cor + tamanho pedidos."""
    svg_inner = ICONS.get(name)
    if svg_inner is None:
        return QIcon()
    inner = svg_inner.replace("{color}", color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}">{inner}</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()
    return QIcon(pix)


def pixmap(name: str, color: str = "#E2E2E8", size: int = 24) -> QPixmap:
    return icon(name, color, size).pixmap(QSize(size, size))
